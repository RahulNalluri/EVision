from __future__ import annotations

from backend.evision_engine.llm import generate_grounded_answer
from backend.evision_engine.schemas import Telemetry, TripAnalysis


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    best = chunks[0]
    return f" Related EV knowledge: {best.get('text', '')[:220]}"


def answer_driver_question(
    question: str,
    telemetry: Telemetry,
    analysis: TripAnalysis,
    retrieved_chunks: list[dict] | None = None,
) -> str:
    q = question.lower()
    chunks = retrieved_chunks or []
    generated = generate_grounded_answer(question, telemetry, analysis, chunks)
    if generated:
        return generated
    context = format_context(chunks)
    top = analysis.suggestions[0] if analysis.suggestions else None
    top_message = top.message if top else "Keep your speed steady and avoid sharp acceleration."

    if "draining" in q or "fast" in q:
        return (
            f"Your battery is draining faster because EVision sees {telemetry.traffic} traffic, "
            f"{telemetry.ac_load:.0f}% AC load, and {telemetry.acceleration:.0f}% acceleration intensity. "
            f"That creates about {analysis.energy_wastage_percent:.1f}% avoidable wastage. "
            f"{top_message}{context}"
        )

    if "reach" in q or "destination" in q:
        if analysis.arrival_buffer >= 0:
            return (
                f"Yes. Your current predicted range is {analysis.current_predicted_range} km for a "
                f"{telemetry.route_distance:.0f} km route, leaving about {analysis.arrival_buffer} km of buffer. "
                f"Following EVision's optimized plan can raise range to about {analysis.optimized_predicted_range} km."
            )
        return (
            f"Not safely at the current driving pattern. Your predicted range is "
            f"{analysis.current_predicted_range} km for a {telemetry.route_distance:.0f} km route. "
            "Use Eco mode, reduce AC load, and drive smoothly, or plan a short charging stop."
        )

    if "save" in q or "battery" in q:
        return (
            f"Best action now: {top_message} If you follow the optimized plan, EVision estimates "
            f"about {analysis.trip_summary['range_gain_if_optimized']} km of practical range gain."
        )

    if "charge" in q:
        if analysis.arrival_buffer > 30:
            return (
                f"Fast charging is not needed for this route. You have about {analysis.arrival_buffer} km "
                "of arrival buffer, so charging after arrival is better unless your next trip is long."
            )
        return (
            f"Your buffer is only {analysis.arrival_buffer} km. Try Eco mode first, but plan a short top-up "
            "if your next leg adds more than 50 km."
        )

    return (
        f"EVision's current recommendation is: {top_message} Your Battery Utilization Index is "
        f"{analysis.battery_utilization_index}, current range is {analysis.current_predicted_range} km, "
        f"and optimized range is {analysis.optimized_predicted_range} km."
    )
