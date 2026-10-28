import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from companion.core import (FLAGSHIP_MODEL, OPENAI_BASE_URL, OPENAI_MODEL, Config, RewriteError,
                            load_api_key, rewrite)


class OpenAITests(unittest.TestCase):
    def setUp(self):
        self.config = Config(base_url=OPENAI_BASE_URL, model=OPENAI_MODEL, demo=False)

    def test_keyfile_only_for_official_endpoint(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory)
            (path / "key.txt").write_text("sk-dummy-local-test-only\n", encoding="utf-8-sig")
            self.assertEqual(load_api_key(self.config, path), "sk-dummy-local-test-only")
            self.assertEqual(load_api_key(Config(base_url="https://other.example/v1", demo=False), path), "")
            self.assertEqual(load_api_key(Config(), path), "")

    def test_environment_precedes_keyfile(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"WOW_RP_API_KEY": "test-env-key"}, clear=True):
            self.assertEqual(load_api_key(self.config, Path(directory)), "test-env-key")

    def test_invalid_keyfile_error_does_not_echo_contents(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory)
            (path / "key.txt").write_text("secret-value with whitespace")
            with self.assertRaises(RewriteError) as error:
                load_api_key(self.config, path)
            self.assertNotIn("secret-value", str(error.exception))

    @patch("companion.core.urllib.request.build_opener")
    def test_openai_request_schema_and_usage(self, build_opener):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps({
            "model": "gpt-5.4-mini-2026-03-17", "usage": {"total_tokens": 100},
            "choices": [{"finish_reason": "stop", "message": {
                "content": '{"mode":"normal","text":"Healer FIRST!"}',
            }}],
        }).encode()
        build_opener.return_value.open.return_value = response
        result = rewrite("先杀奶", self.config, "test-secret")
        request = build_opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertFalse(payload["store"])
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(result.usage["total_tokens"], 100)
        self.assertEqual(result.model, "gpt-5.4-mini-2026-03-17")

    @patch("companion.core.urllib.request.build_opener")
    def test_refusal_and_truncated_completion_not_used(self, build_opener):
        response = MagicMock()
        response.__enter__.return_value = response
        build_opener.return_value.open.return_value = response
        for choice in (
            {"message": {"refusal": "refused", "content": None}},
            {"finish_reason": "length", "message": {"content": '{"mode":"normal","text":"Healer"}'}},
        ):
            response.read.return_value = json.dumps({"choices": [choice]}).encode()
            with self.assertRaises(RewriteError):
                rewrite("先杀奶", self.config, "test-secret")

    @patch("companion.core.urllib.request.build_opener")
    def test_flagship_responses_transport_and_actual_tier(self, build_opener):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps({
            "status": "completed", "model": FLAGSHIP_MODEL, "service_tier": "ultrafast",
            "usage": {"input_tokens": 100, "output_tokens": 25},
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "content": [{"type": "output_text", "text":
                    '{"mode":"normal","text":"Healer FIRST!"}'}]},
            ],
        }).encode()
        build_opener.return_value.open.return_value = response
        config = Config(base_url=OPENAI_BASE_URL, model=FLAGSHIP_MODEL, demo=False, service_tier="ultrafast")
        result = rewrite("先杀奶", config, "test-secret")
        request = build_opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(payload["reasoning"], {"effort": "low"})
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertEqual(payload["service_tier"], "ultrafast")
        self.assertLessEqual(payload["max_output_tokens"], 1024)
        self.assertEqual(result.service_tier, "ultrafast")
        self.assertEqual(result.text, "Healer FIRST!")

    @patch("companion.core.urllib.request.build_opener")
    def test_responses_refusal_or_incomplete_never_used(self, build_opener):
        response = MagicMock()
        response.__enter__.return_value = response
        build_opener.return_value.open.return_value = response
        config = Config(base_url=OPENAI_BASE_URL, model=FLAGSHIP_MODEL, demo=False, service_tier="ultrafast")
        for envelope in (
            {"status": "incomplete", "output": []},
            {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal"}]}]},
        ):
            response.read.return_value = json.dumps(envelope).encode()
            with self.assertRaises(RewriteError):
                rewrite("先杀奶", config, "test-secret")

    def test_unsupported_ultrafast_model_fails_before_network(self):
        with self.assertRaises(RewriteError):
            Config(base_url=OPENAI_BASE_URL, model=OPENAI_MODEL, demo=False, service_tier="ultrafast").validate()


if __name__ == "__main__": unittest.main()
