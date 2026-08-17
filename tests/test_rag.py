from __future__ import annotations

import unittest
from pathlib import Path

from backend.evision_engine.rag import RAGIndex


ROOT = Path(__file__).resolve().parents[1]


class RAGTests(unittest.TestCase):
    def test_battery_question_retrieves_relevant_context(self) -> None:
        index = RAGIndex.load(ROOT / "data" / "rag_index.json")
        results = index.search("Why is my battery draining fast in dense traffic?", limit=3)
        self.assertTrue(results)
        self.assertGreater(results[0]["score"], 0)
        self.assertIn("source", results[0])


if __name__ == "__main__":
    unittest.main()
