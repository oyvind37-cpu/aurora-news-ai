"""End-to-end test of the Aurora morning brief with a simulated AI model.

This test never sends a request to Cloudflare or OpenAI.
"""
import json
import unittest
from unittest.mock import patch
from engine import build

FIXTURE = {"items": [
    {"title":"Ny lokal sak", "source":"Avisa Oslo", "url":"https://example.org/oslo",
     "category":"lokalt", "summary":"Kort lokalnyhet."},
    {"title":"Ny norsk sak", "source":"NRK", "url":"https://example.org/norge",
     "category":"norge", "summary":"Kort nasjonal nyhet."},
    {"title":"Ny verdenssak", "source":"BBC", "url":"https://example.org/verden",
     "category":"verden", "summary":"Kort utenriksnyhet."}
]}

def response(source_ids):
    return json.dumps({
        "headline":"Aurora Morgenbrief",
        "intro":"En kildebasert oppsummering av utvalgte RSS-nyheter.",
        "sections":[
            {"heading":"Oslo", "text":"Kildene opplyser om en lokal sak.", "source_ids":[source_ids[0]]},
            {"heading":"Norge", "text":"Kildene opplyser om en norsk sak.", "source_ids":[source_ids[1]]},
            {"heading":"Verden", "text":"Kildene opplyser om en internasjonal sak.", "source_ids":[source_ids[2]]}
        ],
        "limitations":"Bare RSS-utdrag er gjennomgått; ikke uavhengig faktaverifisert."
    }, ensure_ascii=False)

class EndToEndTests(unittest.TestCase):
    def test_morgenbrief_with_mock_ai(self):
        with patch("engine.model_request", side_effect=lambda provider, sources: response(
                [s["id"] for s in sources])) as model:
            result = build(FIXTURE, "cloudflare")
        self.assertEqual(result["method"], "generative_ai_source_attributed")
        self.assertEqual(len(result["analysis"]["sections"]), 3)
        self.assertEqual(len(result["sources"]), 3)
        self.assertTrue(all(section["source_ids"] for section in result["analysis"]["sections"]))
        model.assert_called_once()

    def test_bad_model_response_fails_closed(self):
        with patch("engine.model_request", return_value="Dette er ikke JSON"):
            with self.assertRaises(json.JSONDecodeError):
                build(FIXTURE, "cloudflare")

    def test_missing_citations_fails_closed(self):
        bad = json.loads(response(["S1","S2","S3"]))
        bad["sections"][1]["source_ids"] = []
        with patch("engine.model_request", return_value=json.dumps(bad)):
            with self.assertRaises(ValueError):
                build(FIXTURE, "cloudflare")

if __name__ == "__main__":
    unittest.main()
