"""Offline model-adapter tests: mock HTTP, never contact providers."""
import io
import json
import os
import unittest
from unittest.mock import patch
from engine import model_request, build, validate

SOURCES = [{"id":"S1","title":"Testnyhet","source":"Testkilde",
            "url":"https://example.org/a","category":"norge","summary":"Oppgitt i RSS."}]
REPLY = json.dumps({"headline":"Morgenbrief","intro":"Kildene opplyser.",
 "sections":[{"heading":"Norge","text":"Kilden omtaler saken.","source_ids":["S1"]}],
 "limitations":"Bare RSS-utdrag."})

class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, *args):
        return json.dumps(self.payload).encode("utf-8")

class AdapterTests(unittest.TestCase):
    def test_cloudflare_without_credentials_never_calls_network(self):
        with patch.dict(os.environ, {}, clear=True), patch("urllib.request.urlopen") as call:
            with self.assertRaises(RuntimeError):
                model_request("cloudflare", SOURCES)
            call.assert_not_called()

    def test_openai_without_credentials_never_calls_network(self):
        with patch.dict(os.environ, {}, clear=True), patch("urllib.request.urlopen") as call:
            with self.assertRaises(RuntimeError):
                model_request("openai", SOURCES)
            call.assert_not_called()

    def test_cloudflare_mock_response(self):
        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID":"test-account",
                                     "CLOUDFLARE_API_TOKEN":"test-token"}, clear=True):
            with patch("urllib.request.urlopen", return_value=FakeResponse(
                    {"result":{"response":REPLY}})) as call:
                answer = model_request("cloudflare", SOURCES)
                self.assertEqual(validate(answer, SOURCES)["headline"], "Morgenbrief")
                request = call.call_args.args[0]
                self.assertIn("/ai/run/", request.full_url)
                self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

    def test_openai_mock_response(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY":"test-token"}, clear=True):
            with patch("urllib.request.urlopen", return_value=FakeResponse(
                    {"choices":[{"message":{"content":REPLY}}]})) as call:
                answer = model_request("openai", SOURCES)
                self.assertEqual(validate(answer, SOURCES)["headline"], "Morgenbrief")
                request = call.call_args.args[0]
                self.assertIn("/chat/completions", request.full_url)

    def test_model_output_rejects_non_source_citation(self):
        bad = json.loads(REPLY)
        bad["sections"][0]["source_ids"] = ["S999"]
        with self.assertRaises(ValueError):
            validate(json.dumps(bad), SOURCES)

if __name__ == "__main__":
    unittest.main()
