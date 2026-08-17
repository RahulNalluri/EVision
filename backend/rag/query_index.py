from __future__ import annotations

import sys
from pathlib import Path

from backend.evision_engine.rag import RAGIndex

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "data" / "rag_index.json"


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Why is my battery draining fast?"
    index = RAGIndex.load(INDEX_PATH)
    for result in index.search(query, limit=5):
        print(f"[{result['score']}] {result['id']} ({result['source']})")
        print(result["text"])
        print()


if __name__ == "__main__":
    main()
