from __future__ import annotations

from pathlib import Path

from backend.evision_engine.rag import RAGIndex

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "knowledge_base"
INDEX_PATH = ROOT / "data" / "rag_index.json"


def main() -> None:
    index = RAGIndex.build(DOCS_DIR)
    index.save(INDEX_PATH)
    print(f"Indexed {len(index.chunks)} chunks from {DOCS_DIR}")
    print(f"Saved RAG index to {INDEX_PATH}")


if __name__ == "__main__":
    main()
