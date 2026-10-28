"""Regression for paid-call count: no network and no real key is used."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion.core import Rewrite
from tools import live_eval


class LiveEvalTests(unittest.TestCase):
    def test_case_selection_controls_actual_paid_call_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            args = ["live_eval.py", "--live", "--cases", "kill_healer,auction", "--round", "test"]
            with patch.object(live_eval, "ROOT", root), patch.object(live_eval.sys, "argv", args), \
                 patch.object(live_eval, "load_api_key", return_value="dummy"), \
                 patch.object(live_eval, "rewrite", return_value=Rewrite("normal", "Test")) as call, \
                 patch("builtins.print"):
                live_eval.main()
            self.assertEqual(call.call_count, 2)
            sources = {item.args[0] for item in call.call_args_list}
            self.assertEqual(sources, {"先杀奶", "拍卖行这瓶药也太贵了"})
            report = json.loads((root / "docs" / "openai-live-test.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["calls"], 2)


if __name__ == "__main__": unittest.main()
