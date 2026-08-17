from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.evision_engine.schemas import Telemetry, TripAnalysis


def generate_grounded_answer(
    question: str,
    telemetry: Telemetry,
    analysis: TripAnalysis,
    retrieved_chunks: list[dict],
) -> str | None:
    endpoint = os.getenv("EVISION_LLM_ENDPOINT", "").strip()
    api_key = os.getenv("EVISION_LLM_API_KEY", "").strip()
    model = os.getenv("EVISION_LLM_MODEL", "").strip()
    if not endpoint or not api_key or not model:
        return None

    context = "\n\n".join(
        f"Source: {chunk.get('source', 'knowledge base')}\n{chunk.get('text', '')[:700]}"
        for chunk in retrieved_chunks[:4]
    )
    system_prompt = (
        "You are EVision, an in-car EV battery utilization copilot. Answer in no more than "
        "three short sentences. Use simple language, give one immediate action, never invent "
        "vehicle facts, and treat supplied analytics as authoritative."
    )
    user_prompt = (
        f"Driver question: {question}\n"
        f"Live telemetry: {json.dumps(telemetry.to_dict())}\n"
        f"EVision analytics: {json.dumps(analysis.to_dict())}\n"
        f"Retrieved knowledge:\n{context or 'No matching knowledge chunk.'}"
    )
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        answer = body["choices"][0]["message"]["content"].strip()
        return answer or None
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError):
        return None
