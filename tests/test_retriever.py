from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lino_autocare_copilot import AutoCareRetriever  # noqa: E402


class RetrieverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = AutoCareRetriever(PROJECT_ROOT / "data")

    def test_diagnostics_price_is_confirmed(self):
        results = self.retriever.search("How much is vehicle diagnostics?", top_k=1)
        self.assertEqual(results[0].category, "service_price")
        self.assertIn("₦20,000", results[0].content)
        self.assertEqual(results[0].price_status, "user_confirmed_current")

    def test_known_tyre_size_is_retrievable(self):
        results = self.retriever.search("Do you have 205/55R16 tyres?", top_k=5)
        self.assertTrue(any("205/55R16" in result.title for result in results))
        self.assertTrue(all(result.price_status == "historical_unconfirmed" for result in results if result.category == "tyre_product"))

    def test_engine_oil_is_retrievable(self):
        results = self.retriever.search("Castrol Edge 5W-40 5 litre engine oil", top_k=3)
        self.assertTrue(any(result.category == "engine_oil_product" for result in results))

    def test_overheating_triggers_safety_notice(self):
        notice = self.retriever.urgent_safety_notice("My car is overheating and there is smoke")
        self.assertIsNotNone(notice)
        self.assertIn("stop driving", notice.lower())

    def test_irrelevant_question_is_unsupported(self):
        results = self.retriever.search("Who won the football match on Saturday?")
        self.assertEqual(results, [])

    def test_alignment_price_is_confirmed(self):
        results = self.retriever.search(
            "How much does wheel alignment cost?",
            top_k=1,
        )

        self.assertTrue(results)
        self.assertEqual(results[0].id, "SERVICE-002")
        self.assertEqual(results[0].category, "service_price")
        self.assertIn("₦3,000", results[0].content)
        self.assertEqual(
            results[0].price_status,
            "user_confirmed_current",
        )

    def test_tyre_bulge_retrieves_correct_safety_source(self):
        results = self.retriever.search(
            "My tyre has a bulge. Can I continue driving?",
            top_k=1,
        )

        self.assertTrue(results)
        self.assertEqual(results[0].id, "KB015")
        self.assertEqual(results[0].category, "tyre_damage")
        self.assertEqual(results[0].safety_level, "urgent")

    def test_tyre_bulge_triggers_safety_notice(self):
        notice = self.retriever.urgent_safety_notice(
            "My tyre has a bulge. Can I continue driving?"
        )

        self.assertIsNotNone(notice)
        self.assertIn("stop driving", notice.lower())
        self.assertIn("professional inspection", notice.lower())
if __name__ == "__main__":
    unittest.main()
