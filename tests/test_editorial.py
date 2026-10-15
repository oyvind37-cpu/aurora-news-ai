"""Fast, dependency-free regression tests for headline guardrails."""
import unittest
from ai_engine import editorial_override, EMERGENCY_HEADLINE

class TestEditorialRules(unittest.TestCase):
    def test_sport(self):
        self.assertEqual(editorial_override("FIFA President Infantino apologises"), "sport")
        self.assertEqual(editorial_override("LSK med Europa-bragd"), "sport")
        self.assertEqual(editorial_override("Formula 1 race in Rwanda"), "sport")
    def test_politics(self):
        self.assertEqual(editorial_override("Albania's prime minister vows not to resign"), "politikk")
        self.assertEqual(editorial_override("US deportations spark protests"), "politikk")
    def test_technology(self):
        self.assertEqual(editorial_override("Why are eight states suing OpenAI?"), "teknologi")
    def test_incident(self):
        self.assertTrue(EMERGENCY_HEADLINE.search("Brannutrykning til skole"))
        self.assertEqual(editorial_override("Brann i boligblokk"), "nyheter")
    def test_unknown(self):
        self.assertIsNone(editorial_override("Været blir fint til helgen"))

if __name__ == "__main__":
    unittest.main()
