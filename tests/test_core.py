import json
import threading
import unittest
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from companion.core import (NORMAL_BYTES, ClipboardFlow, Config, DraftRequest, PREFIX, RewriteError,
                            make_request, parse_request, rewrite, validate_output)


class CoreTests(unittest.TestCase):
    def test_wire_roundtrip_windows_newlines(self):
        self.assertEqual(parse_request(make_request("找一坦一奶").replace("\n", "\r\n")), DraftRequest("找一坦一奶", "normal"))

    def test_only_explicit_requests(self):
        for text in ("password", "先杀奶", "WOWRP/4\nReal DonaldTrump\nhello", "WOWRP/1\nOther\nhello"):
            self.assertIsNone(parse_request(text))

    def test_empty_and_oversized_rejected(self):
        for source in ("  ", "中" * 667, "a\0b"):
            with self.assertRaises(RewriteError):
                make_request(source)

    def test_manual_mode_never_inferred_from_content(self):
        self.assertEqual(parse_request(make_request("LFM Maraudon")).mode, "normal")
        self.assertEqual(parse_request(make_request("先杀奶", "expressive")).mode, "expressive")
        self.assertEqual(parse_request(make_request("That rogue runs fast", "normal")).mode, "normal")

    def test_context_roundtrip_and_json_delimiters(self):
        context = '地点：死亡矿井\n队友：Player1 - 牧师；Player2 - 盗贼\n"引号" \\ WOWRP/3'
        self.assertEqual(parse_request(make_request('收拾迪菲亚\n别开第二组', 'expressive', context)),
                         DraftRequest('收拾迪菲亚\n别开第二组', 'expressive', context))

    def test_normal_never_carries_context(self):
        wire = make_request('找1奶', 'normal', '私人背景')
        self.assertNotIn('私人背景', wire)
        self.assertEqual(parse_request(wire).context, '')
        data = {'mode': 'normal', 'source': 'hello', 'context': '私人背景'}
        self.assertEqual(parse_request(PREFIX + json.dumps(data)).context, '')

    def test_v2_requests_still_work_without_context(self):
        self.assertEqual(parse_request('WOWRP/2\nReal DonaldTrump\nexpressive\n找1奶'),
                         DraftRequest('找1奶', 'expressive'))

    def test_invalid_context_envelope_rejected(self):
        for data in ({'mode':'expressive','source':'hi','context':[]},
                     {'mode':'expressive','source':'hi'},
                     {'mode':'expressive','source':42,'context':''},
                     {'mode':'expressive','source':'hi','context':'中'*1334},
                     {'mode':'expressive','source':'hi','context':'bad\0data'}):
            with self.assertRaises(RewriteError): parse_request(PREFIX + json.dumps(data))
        with self.assertRaises(RewriteError): make_request('hi', 'expressive', '中'*1334)

    def test_json_unpaired_unicode_is_a_recoverable_error(self):
        for field in ('source', 'context'):
            data = {'mode':'expressive','source':'hi','context':''}
            data[field] = '\ud800'
            with self.assertRaises(RewriteError): parse_request(PREFIX + json.dumps(data))

    def test_legacy_and_invalid_mode_requests_are_rejected(self):
        for wire in ("WOWRP/1\nReal DonaldTrump\nhello", PREFIX + "auto\nhello", PREFIX + "normal"):
            with self.assertRaises(RewriteError):
                parse_request(wire)

    def test_refuse_newlines_commands_escape_codes(self):
        for text in ("hello\nworld", "/run hello", ".command", "|Hitem:1|h", "WOWRP/1 hello"):
            with self.assertRaises(RewriteError):
                validate_output({"mode": "expressive", "text": text}, "hello", "expressive")

    def test_normal_uses_utf8_bytes_and_never_truncates(self):
        with self.assertRaises(RewriteError):
            validate_output({"mode": "normal", "text": "中" * (NORMAL_BYTES // 3 + 1)}, "先杀奶", "normal")
        with self.assertRaises(RewriteError):
            validate_output({"mode": "expressive", "text": "A" * 256}, "lfm", "expressive")

    def test_model_cannot_switch_either_manual_mode(self):
        for requested, returned in (("normal", "expressive"), ("expressive", "normal")):
            with self.assertRaises(RewriteError):
                validate_output({"mode": returned, "text": "TREMENDOUS!"}, "先杀奶", requested)

    def test_explicit_numbers_preserved(self):
        good = {"mode": "expressive", "text": "Maraudon! Need 1 TANK and 1 HEALER. TREMENDOUS!"}
        self.assertEqual(validate_output(good, "玛拉顿缺1坦1奶", "expressive").text, good["text"])
        with self.assertRaises(RewriteError):
            validate_output({"mode": "normal", "text": "Need 2 tanks"}, "Need 1 tank", "normal")

    def test_topic_backstop_rejects_explicit_markers_in_both_modes(self):
        banned = ('MAGA!', 'M.A.G.A.', 'ＭＡＧＡ', 'Make Azeroth Great Again!',
                  'Make-our-group-great-again!', 'Keep America Great',
                  'ICE will deal with them.', 'I.C.E. agents!', 'ice agents',
                  'Illegal immigrants!', 'illegal-aliens', '非法移民',
                  'abortion policy', '同性恋', 'Christianity', 'Vote for Trump!')
        for mode in ('normal', 'expressive'):
            for text in banned:
                with self.subTest(mode=mode, text=text), self.assertRaises(RewriteError):
                    validate_output({'mode': mode, 'text': text}, 'hello', mode)

    def test_topic_backstop_preserves_game_terms_and_allowed_metaphors(self):
        allowed = ('Deport these Defias to Kalimdor!', 'Build a wall here, folks!',
                   'Need a priest and a paladin.', 'That troll is mysterious!',
                   'Ice Block NOW!', 'ICE BLOCK NOW!', 'Nice work, folks!', 'Abort the pull!',
                   'China, Russia, Mexico: what a trade route!',
                   'Trump coin is CRASHING!', 'TREMENDOUS group!')
        for text in allowed:
            with self.subTest(text=text):
                self.assertEqual(validate_output({'mode':'expressive','text':text}, 'hello', 'expressive').text, text)

    def test_new_copy_even_unrelated_invalidates(self):
        flow = ClipboardFlow()
        generation, _ = flow.observe(make_request("先杀奶"))
        flow.observe("unrelated clipboard")
        self.assertFalse(flow.is_current(generation))

    def test_recopied_identical_draft_is_new_request(self):
        flow = ClipboardFlow()
        first, _ = flow.observe(make_request("先杀奶"))
        second, _ = flow.observe(make_request("先杀奶"))
        self.assertNotEqual(first, second)
        self.assertTrue(flow.is_current(second))

    def test_pause_discards_inflight(self):
        flow = ClipboardFlow()
        generation, _ = flow.observe(make_request("先杀奶"))
        flow.enabled = False
        self.assertFalse(flow.is_current(generation))

    def test_output_does_not_retrigger(self):
        flow = ClipboardFlow()
        self.assertIsNone(flow.observe("Healer FIRST!"))

    def test_demo_explicitly_marked(self):
        result = rewrite("先杀奶", Config())
        self.assertTrue(result.demo)
        self.assertEqual(result.text, "先杀奶")
        self.assertEqual(result.mode, "normal")

    def test_endpoint_validation(self):
        for url in ("http://remote.example/v1", "https://key@remote.example/v1", "file:///tmp/api", "https://remote.example/v1?key=abc"):
            with self.assertRaises(RewriteError):
                Config(base_url=url, model="test", demo=False).validate()


class Handler(BaseHTTPRequestHandler):
    status = 200
    content = '{"mode":"normal","text":"Healer FIRST!"}'
    captured = None

    def do_POST(self):
        type(self).captured = (self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"]))), self.headers.get("Authorization"))
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        if self.status == 302:
            self.send_header("Location", "http://127.0.0.1:1/stolen")
        self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": self.content}}]}).encode())

    def log_message(self, *args):
        pass


class ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.config = Config(base_url=f"http://127.0.0.1:{cls.server.server_port}/v1", model="fake-model", demo=False)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Handler.status = 200
        Handler.content = '{"mode":"normal","text":"Healer FIRST!"}'

    def test_actual_http_contract(self):
        self.assertEqual(rewrite("先杀奶", self.config, "test-secret").text, "Healer FIRST!")
        path, payload, auth = Handler.captured
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(auth, "Bearer test-secret")
        self.assertEqual(payload["model"], "fake-model")
        request = json.loads(payload["messages"][1]["content"])
        self.assertEqual(request["requested_mode"], "normal")
        self.assertNotIn("force_brief", request)
        self.assertEqual(request["source"], "先杀奶")

    def test_provider_receives_explicit_expressive_mode(self):
        Handler.content = '{"mode":"expressive","text":"Maraudon! Need 1 TANK, 1 HEALER. TREMENDOUS group!"}'
        self.assertEqual(rewrite("玛拉顿缺一坦一奶", self.config, mode="expressive").mode, "expressive")
        self.assertEqual(json.loads(Handler.captured[1]["messages"][1]["content"])["requested_mode"], "expressive")

    def test_context_separate_from_source_and_normal_omits_it(self):
        Handler.content = '{"mode":"expressive","text":"Need 1 healer, folks!"}'
        rewrite('缺1奶', self.config, mode='expressive', context='队友：Player2 - 牧师')
        request = json.loads(Handler.captured[1]['messages'][1]['content'])
        self.assertEqual(request['context'], '队友：Player2 - 牧师')
        self.assertEqual(request['source'], '缺1奶')
        Handler.content = '{"mode":"normal","text":"Need 1 healer!"}'
        rewrite('缺1奶', self.config, context='队友：Player2 - 牧师')
        self.assertNotIn('context', json.loads(Handler.captured[1]['messages'][1]['content']))

    def test_same_language_setting_reaches_model(self):
        Handler.content = '{"mode":"normal","text":"先杀奶！"}'
        self.assertEqual(rewrite("先杀奶", replace(self.config, output_language="跟随原文")).text, "先杀奶！")
        self.assertTrue(json.loads(Handler.captured[1]["messages"][1]["content"])["output_language"].startswith("Chinese"))

    def test_chinese_setting_rejects_english_response(self):
        with self.assertRaisesRegex(RewriteError, "中文输出"):
            rewrite("先杀奶", replace(self.config, output_language="跟随原文"))

    def test_http_error_no_raw_response_or_key(self):
        Handler.status = 401
        with self.assertRaises(RewriteError) as ctx:
            rewrite("先杀奶", self.config, "test-secret")
        self.assertIn("401", str(ctx.exception))
        self.assertNotIn("test-secret", str(ctx.exception))

    def test_redirect_refused(self):
        Handler.status = 302
        with self.assertRaisesRegex(RewriteError, "重定向"):
            rewrite("先杀奶", self.config)

    def test_malformed_output_rejected(self):
        Handler.content = "not JSON"
        with self.assertRaises(RewriteError):
            rewrite("先杀奶", self.config)

    def test_empty_output_rejected(self):
        Handler.content = '{"mode":"normal","text":""}'
        with self.assertRaises(RewriteError):
            rewrite("先杀奶", self.config)


if __name__ == "__main__":
    unittest.main()
