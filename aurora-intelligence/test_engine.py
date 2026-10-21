"""Offline tests; no network, API key or billable calls."""
import unittest
from engine import build, validate

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.data = {"items": [
            {"title": "Sak A", "source": "NRK", "url": "https://example.org/a",
             "category": "norge", "summary": "Kort sammendrag"},
            {"title": "Sak B", "source": "Avisa Oslo", "url": "https://example.org/b",
             "category": "lokalt", "summary": "Kort sammendrag"}]}

    def test_dry_run_no_model(self):
        result = build(self.data)
        self.assertIsNone(result["analysis"])
        self.assertEqual(len(result["sources"]), 2)

    def test_rejects_fake_source(self):
        sources = build(self.data)["sources"]
        payload = '{"headline":"H","intro":"I","limitations":"L","sections":[{"heading":"A","text":"B","source_ids":["S999"]}]}'
        with self.assertRaises(ValueError):
            validate(payload, sources)

    def test_valid_source(self):
        sources = build(self.data)["sources"]
        payload = '{"headline":"H","intro":"I","limitations":"L","sections":[{"heading":"A","text":"B","source_ids":["S1"]}]}'
        self.assertEqual(validate(payload, sources)["headline"], "H")

    def test_cloudflare_object_response(self):
        sources = build(self.data)["sources"]
        payload = {"headline":"H","intro":"I","limitations":"L","sections":[{"heading":"A","text":"B","source_ids":["S1"]}]}
        self.assertEqual(validate(payload, sources)["headline"], "H")

    def test_rejects_unexpected_response_type(self):
        sources = build(self.data)["sources"]
        with self.assertRaises(ValueError):
            validate(["unexpected"], sources)

    def test_many_long_summaries_fit_budget(self):
        self.data["items"] = [
            {"title": "Sak " + str(i), "source": "NRK", "url": "https://example.org/" + str(i),
             "category": "norge", "summary": "lang tekst " * 150} for i in range(18)
        ]
        result = build(self.data)
        import json
        self.assertLessEqual(len(json.dumps(result["sources"], ensure_ascii=False)), 16000)
        self.assertGreater(len(result["sources"]), 0)

    def test_rejects_four_sections(self):
        sources = build(self.data)["sources"]
        section = {"heading": "A", "text": "B", "source_ids": ["S1"]}
        payload = {"headline": "H", "intro": "I", "limitations": "L",
                   "sections": [section.copy() for _ in range(4)]}
        with self.assertRaisesRegex(ValueError, "Ugyldig antall seksjoner"):
            validate(payload, sources)

    def test_accepts_three_sections(self):
        sources = build(self.data)["sources"]
        section = {"heading": "A", "text": "B", "source_ids": ["S1"]}
        payload = {"headline": "H", "intro": "I", "limitations": "L",
                   "sections": [section.copy() for _ in range(3)]}
        self.assertEqual(len(validate(payload, sources)["sections"]), 3)

    def test_rejects_invented_url(self):
        sources = build(self.data)["sources"]
        payload = '{"headline":"H","intro":"I","limitations":"L","sections":[{"heading":"A","text":"Les https://falsk.example/artikkel","source_ids":["S1"]}]}'
        with self.assertRaises(ValueError):
            validate(payload, sources)

if __name__ == "__main__":
    unittest.main()
