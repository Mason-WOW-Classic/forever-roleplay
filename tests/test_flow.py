"""UI coordinator tests using fakes: never touches the real desktop/clipboard."""
import queue
import unittest
from concurrent.futures import Future

from companion.app import App
from companion.clipboard import ClipboardBusy
from companion.core import ClipboardFlow, Config, Rewrite, RewriteError, make_request


class Value:
    def __init__(self): self.value = ""
    def set(self, text): self.value = text
    def get(self, *args): return self.value
    def edit_modified(self, value=None):
        if value is not None: self.modified = value
        return getattr(self, 'modified', False)
    def focus_set(self): pass
    def tag_add(self, *args): pass
    def configure(self, **kwargs): pass
    def delete(self, *args): self.value = ""
    def insert(self, index, text): self.value = text


class Root:
    def __init__(self): self.bells = 0
    def bell(self): self.bells += 1
    def after(self, *args): pass


class Clipboard:
    def __init__(self): self.seq, self.text = 1, ""
    def sequence(self): return self.seq
    def snapshot(self): return self.seq, self.text
    def copy(self, text): self.seq += 1; self.text = text
    def replace_if_unchanged(self, seq, expected, text):
        if self.seq != seq or self.text != expected: return None
        self.copy(text)
        return self.seq


class Pool:
    def __init__(self): self.calls = []
    def submit(self, fn, *args):
        future = Future()
        future.set_running_or_notify_cancel()
        self.calls.append((args, future))
        return future


class FlowTests(unittest.TestCase):
    def setUp(self):
        app = object.__new__(App)
        app.closed, app.future = False, None
        app.flow, app.pool, app.events = ClipboardFlow(), Pool(), queue.Queue()
        app.clipboard, app.root = Clipboard(), Root()
        app.last_sequence = app.clipboard.sequence()
        app.config, app.key = Config(), ""
        app.result, app.status = Value(), Value()
        app.request, app.pasted, app.expressive = Value(), Value(), Value()
        app.context, app.source = Value(), Value()
        self.app = app

    def copy_request(self, source="先杀奶"):
        self.app.clipboard.copy(make_request(source))
        self.app.poll()
        return self.app.pool.calls[-1][1]

    def test_end_to_end_request_completion_no_loop(self):
        future = self.copy_request()
        future.set_result(Rewrite("normal", "Healer FIRST!"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, "Healer FIRST!")
        self.assertEqual(self.app.root.bells, 1)
        self.app.poll()
        self.assertEqual(len(self.app.pool.calls), 1)

    def test_unrelated_copy_before_completion_preserved(self):
        future = self.copy_request()
        self.app.clipboard.copy("new unrelated clipboard")
        future.set_result(Rewrite("normal", "Healer FIRST!"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, "new unrelated clipboard")
        self.assertEqual(self.app.root.bells, 0)

    def test_out_of_order_results_only_latest_wins(self):
        first = self.copy_request()
        second = self.copy_request("不要打羊")
        second.set_result(Rewrite("normal", "Do NOT hit sheep!"))
        first.set_result(Rewrite("normal", "Healer FIRST!"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, "Do NOT hit sheep!")

    def test_pause_while_running_never_writes(self):
        future = self.copy_request()
        original = self.app.clipboard.text
        self.app.pause()
        future.set_result(Rewrite("normal", "Healer FIRST!"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, original)

    def test_provider_failure_preserves_request(self):
        future = self.copy_request()
        original = self.app.clipboard.text
        future.set_exception(RewriteError("test provider error"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, original)
        self.assertIn("test provider error", self.app.status.value)

    def test_atomic_final_check_prevents_last_moment_overwrite(self):
        future = self.copy_request()
        future.set_result(Rewrite("normal", "Healer FIRST!"))
        original_replace = self.app.clipboard.replace_if_unchanged
        def raced(seq, expected, text):
            self.app.clipboard.copy("copied during completion")
            return original_replace(seq, expected, text)
        self.app.clipboard.replace_if_unchanged = raced
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, "copied during completion")

    def test_busy_read_retries_without_losing_sequence(self):
        self.app.clipboard.copy(make_request("先杀奶"))
        snapshot = self.app.clipboard.snapshot
        def busy(): raise ClipboardBusy("busy")
        self.app.clipboard.snapshot = busy
        self.app.poll()
        self.assertEqual(self.app.last_sequence, 1)
        self.app.clipboard.snapshot = snapshot
        self.app.poll()
        self.assertEqual(len(self.app.pool.calls), 1)

    def test_checkbox_change_invalidates_inflight_result(self):
        future = self.copy_request()
        original = self.app.clipboard.text
        self.app.expressive.set(True)
        self.app.style_changed()
        future.set_result(Rewrite("normal", "Healer FIRST!"))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, original)

    def test_clipboard_mode_reaches_worker_unchanged(self):
        self.app.clipboard.copy(make_request("先杀奶", "expressive"))
        self.app.poll()
        self.assertEqual(self.app.pool.calls[0][0][3], "expressive")

    def test_context_reaches_worker_with_source(self):
        context = '地点：死亡矿井\n队友：Player1 - 牧师'
        self.app.clipboard.copy(make_request('缺1奶', 'expressive', context))
        self.app.poll()
        args = self.app.pool.calls[0][0]
        self.assertEqual(args[0], '缺1奶')
        self.assertEqual(args[4], context)

    def test_context_edit_invalidates_expressive_inflight_result(self):
        self.app.expressive.set(True)
        self.app.clipboard.copy(make_request('先杀奶', 'expressive', '地点：死亡矿井'))
        self.app.poll()
        future = self.app.pool.calls[-1][1]
        original = self.app.clipboard.text
        self.app.context.edit_modified(True)
        self.app.context_changed()
        future.set_result(Rewrite('expressive', 'Healer FIRST!'))
        self.app.poll()
        self.assertEqual(self.app.clipboard.text, original)
        self.assertFalse(self.app.context.edit_modified())

    def test_normal_prepare_does_not_read_background(self):
        self.app.source.set('先杀奶')
        def forbidden(*args): raise AssertionError('Normal must not read background')
        self.app.context.get = forbidden
        self.app.prepare()
        self.assertNotIn('context data', self.app.request.value)
        from companion.core import parse_request
        self.assertEqual(parse_request(self.app.request.value).context, '')


if __name__ == "__main__": unittest.main()
