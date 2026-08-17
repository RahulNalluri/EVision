from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass
class Chunk:
    id: str
    source: str
    text: str
    tokens: list[str]


class RAGIndex:
    def __init__(self, chunks: list[Chunk], idf: dict[str, float]) -> None:
        self.chunks = chunks
        self.idf = idf

    @classmethod
    def empty(cls) -> "RAGIndex":
        return cls([], {})

    @classmethod
    def build(cls, docs_dir: Path, chunk_size: int = 95, overlap: int = 22) -> "RAGIndex":
        chunks: list[Chunk] = []
        for path in sorted(docs_dir.glob("*.md")):
            words = tokenize(path.read_text(encoding="utf-8"))
            raw_text = path.read_text(encoding="utf-8")
            raw_words = raw_text.split()
            start = 0
            number = 1
            while start < len(raw_words):
                end = min(len(raw_words), start + chunk_size)
                text = " ".join(raw_words[start:end])
                chunks.append(
                    Chunk(
                        id=f"{path.stem}-{number}",
                        source=path.name,
                        text=text,
                        tokens=tokenize(text),
                    )
                )
                number += 1
                if end == len(raw_words):
                    break
                start = max(0, end - overlap)

        document_frequency: Counter[str] = Counter()
        for chunk in chunks:
            document_frequency.update(set(chunk.tokens))

        idf = {
            token: math.log((1 + len(chunks)) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        return cls(chunks, idf)

    def vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total = max(1, sum(counts.values()))
        return {
            token: (count / total) * self.idf.get(token, 1.0)
            for token, count in counts.items()
        }

    @staticmethod
    def cosine(left: dict[str, float], right: dict[str, float]) -> float:
        shared = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search(self, query: str, limit: int = 4) -> list[dict]:
        query_vector = self.vectorize(tokenize(query))
        results = []
        for chunk in self.chunks:
            score = self.cosine(query_vector, self.vectorize(chunk.tokens))
            if score > 0:
                results.append(
                    {
                        "id": chunk.id,
                        "source": chunk.source,
                        "score": round(score, 4),
                        "text": chunk.text,
                    }
                )
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"chunks": [asdict(chunk) for chunk in self.chunks], "idf": self.idf}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "RAGIndex":
        payload = json.loads(path.read_text(encoding="utf-8"))
        chunks = [Chunk(**chunk) for chunk in payload["chunks"]]
        return cls(chunks, payload["idf"])
