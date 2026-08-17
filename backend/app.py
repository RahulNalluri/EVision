from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from backend.evision_engine.assistant import answer_driver_question
from backend.evision_engine.model import analyze_trip
from backend.evision_engine.rag import RAGIndex
from backend.evision_engine.schemas import DEFAULT_TELEMETRY, Telemetry

ROOT = Path(__file__).resolve().parents[1]
RAG_INDEX_PATH = ROOT / "data" / "rag_index.json"
STATIC_ROOT = ROOT / "frontend"


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)


def load_rag() -> RAGIndex:
    if RAG_INDEX_PATH.exists():
        return RAGIndex.load(RAG_INDEX_PATH)
    return RAGIndex.empty()


class EVisionHandler(BaseHTTPRequestHandler):
    server_version = "EVisionBackend/1.0"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            json_response(self, {"status": "ok", "service": "EVision backend"})
            return

        if parsed.path == "/api/demo-trip":
            result = analyze_trip(Telemetry(**DEFAULT_TELEMETRY))
            json_response(self, result.to_dict())
            return

        if parsed.path == "/api/rag/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            index = load_rag()
            json_response(self, {"query": query, "chunks": index.search(query, limit=5)})
            return

        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = read_json(self)
        except json.JSONDecodeError:
            json_response(self, {"error": "Invalid JSON payload"}, status=400)
            return

        if parsed.path == "/api/analyze":
            try:
                telemetry = Telemetry(**{**DEFAULT_TELEMETRY, **payload})
            except (TypeError, ValueError) as exc:
                json_response(self, {"error": str(exc)}, status=422)
                return
            result = analyze_trip(telemetry)
            json_response(self, result.to_dict())
            return

        if parsed.path == "/api/assistant":
            question = str(payload.get("question", "")).strip()
            try:
                telemetry = Telemetry(**{**DEFAULT_TELEMETRY, **payload.get("telemetry", {})})
            except (TypeError, ValueError) as exc:
                json_response(self, {"error": str(exc)}, status=422)
                return
            result = analyze_trip(telemetry)
            rag = load_rag()
            chunks = rag.search(question, limit=4) if question else []
            answer = answer_driver_question(question, telemetry, result, chunks)
            json_response(
                self,
                {
                    "question": question,
                    "answer": answer,
                    "retrieved_context": chunks,
                    "analysis": result.to_dict(),
                },
            )
            return

        json_response(self, {"error": "Unknown endpoint"}, status=404)

    def serve_static(self, request_path: str) -> None:
        rel = request_path.lstrip("/") or "index.html"
        target = (STATIC_ROOT / rel).resolve()
        if not target.is_relative_to(STATIC_ROOT.resolve()) or not target.exists() or target.is_dir():
            json_response(self, {"error": "Not found"}, status=404)
            return

        content_type = "text/plain"
        if target.suffix == ".html":
            content_type = "text/html"
        elif target.suffix == ".css":
            content_type = "text/css"
        elif target.suffix == ".js":
            content_type = "application/javascript"
        elif target.suffix == ".json":
            content_type = "application/json"

        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), EVisionHandler)
    print(f"EVision backend running at http://{host}:{port}")
    print("Open the app at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
