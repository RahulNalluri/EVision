from __future__ import annotations

from backend.evision_engine.domain_model import predict as predict_with_domain_model
from backend.evision_engine.schemas import Suggestion, Telemetry, TripAnalysis


TRAFFIC_PENALTY = {"light": 2, "moderate": 7, "dense": 14}
WEATHER_PENALTY = {"clear": 0, "hot": 6, "rain": 5, "wind": 7}
ROAD_PENALTY = {"city": 5, "highway": 8, "hills": 14, "mixed": 7}
MODE_PENALTY = {"eco": -5, "normal": 3, "sport": 11}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def estimate_wastage(telemetry: Telemetry) -> float:
    speed_waste = 4 if telemetry.speed < 35 else 0
    if telemetry.speed > 72:
        speed_waste += (telemetry.speed - 72) * 0.38

    acceleration_waste = telemetry.acceleration * 0.15
    braking_waste = max(0, telemetry.braking - 58) * 0.14
    ac_waste = telemetry.ac_load * 0.11
    context_waste = (
        TRAFFIC_PENALTY[telemetry.traffic]
        + WEATHER_PENALTY[telemetry.weather]
        + ROAD_PENALTY[telemetry.road_type]
        + MODE_PENALTY[telemetry.drive_mode]
    )
    history_bonus = (telemetry.past_efficiency_score - 70) * -0.05
    charging_bonus = (telemetry.charging_habit_score - 70) * -0.03
    return round(clamp(4 + speed_waste + acceleration_waste + braking_waste + ac_waste + context_waste + history_bonus + charging_bonus, 0, 42), 1)


def predict_ranges(telemetry: Telemetry, wastage: float) -> tuple[int, int]:
    base_range = telemetry.battery * 3.25
    current = round(base_range * (1 - wastage / 100))
    optimized_wastage = max(3, wastage - 11)
    optimized = round(base_range * (1 - optimized_wastage / 100))
    return current, optimized


def build_breakdown(telemetry: Telemetry, wastage: float) -> dict[str, float]:
    return {
        "motor_load": round(clamp(42 + telemetry.speed * 0.16 + telemetry.acceleration * 0.08, 35, 68), 1),
        "climate_load": round(clamp(8 + telemetry.ac_load * 0.23 + (7 if telemetry.weather == "hot" else 0), 5, 32), 1),
        "traffic_idle": round(clamp(TRAFFIC_PENALTY[telemetry.traffic] * 1.5 + (5 if telemetry.braking > 55 else 0), 3, 26), 1),
        "road_terrain": round(clamp(ROAD_PENALTY[telemetry.road_type] * 1.2, 4, 24), 1),
        "avoidable_wastage": wastage,
    }


def generate_suggestions(telemetry: Telemetry, current_range: int, optimized_range: int, wastage: float) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    arrival_buffer = current_range - round(telemetry.route_distance)

    if telemetry.acceleration > 62:
        suggestions.append(
            Suggestion(
                "Smooth acceleration",
                "Ease into starts for the next few minutes. Sharp launches are the biggest avoidable drain right now.",
                "Save 4-7 km",
                "driving",
            )
        )

    if telemetry.speed > 78:
        suggestions.append(
            Suggestion(
                "Reduce cruising speed",
                "Stay near 68-74 km/h on this road. The current speed is pushing motor load up quickly.",
                "Save 5-9 km",
                "speed",
            )
        )
    elif telemetry.traffic == "dense":
        suggestions.append(
            Suggestion(
                "Traffic strategy",
                "Traffic is dense ahead. Hold 42-48 km/h, keep regen high, and avoid sharp starts.",
                "Save 3-5 km",
                "traffic",
            )
        )

    if telemetry.ac_load > 55 or telemetry.weather == "hot":
        suggestions.append(
            Suggestion(
                "Cabin efficiency",
                "Set cabin temperature around 24C and keep fan near level 2 to reduce climate load.",
                "Climate load -6%",
                "climate",
            )
        )

    if arrival_buffer < 15:
        suggestions.append(
            Suggestion(
                "Protect arrival buffer",
                "Your destination buffer is tight. Use Eco mode, lower AC load, and keep acceleration smooth.",
                "Protect range",
                "route",
            )
        )

    if telemetry.drive_mode == "sport":
        suggestions.append(
            Suggestion(
                "Switch drive mode",
                "Sport mode is costing range on this route. Eco mode gives the safest battery buffer.",
                "Save 6-10 km",
                "mode",
            )
        )

    suggestions.extend(
        [
            Suggestion(
                "Regenerative braking",
                "Lift earlier before stops so regen can recover more energy instead of using hard braking.",
                "Improve index",
                "braking",
            ),
            Suggestion(
                "Charging plan",
                "Fast charging is not needed for this route if your next trip is short. Charge after arrival to reduce battery stress.",
                "Avoid battery stress",
                "charging",
            ),
        ]
    )

    return suggestions[:4]


def analyze_trip(telemetry: Telemetry) -> TripAnalysis:
    analytic_wastage = estimate_wastage(telemetry)
    analytic_current, analytic_optimized = predict_ranges(telemetry, analytic_wastage)
    analytic_utilization = clamp(100 - analytic_wastage * 1.55, 35, 98)
    learned = predict_with_domain_model(telemetry)

    if learned:
        learned_rate = learned["energy_consumption_kwh"] / learned["model_distance_km"]
        learned_rate = clamp(learned_rate, 0.08, 0.45)
        available_energy_kwh = 60 * telemetry.battery / 100
        learned_current = available_energy_kwh / learned_rate
        relative_waste = max(
            0,
            (learned_rate / learned["reference_efficiency_kwh_per_km"] - 1) * 100,
        )
        learned_wastage = clamp(relative_waste, 0, 42)
        learned_optimized = learned_current * (1 + min(0.15, learned_wastage / 100))
        # Blend learned estimates with guard-railed analytics for stable, explainable inference.
        wastage = round(clamp(analytic_wastage * 0.65 + learned_wastage * 0.35, 0, 42), 1)
        utilization = round(clamp(100 - wastage * 1.55, 35, 98))
        current_range = round(clamp(analytic_current * 0.65 + learned_current * 0.35, 0, 5000))
        optimized_range = round(
            clamp(analytic_optimized * 0.65 + learned_optimized * 0.35, current_range, 5000)
        )
        intelligence = {
            "prediction_mode": "hybrid_ml_and_analytics",
            "model": "EVision Kaggle energy prediction model v2.0.0",
            "ml_weight": 0.35,
            "predicted_energy_kwh": round(learned["energy_consumption_kwh"], 3),
            "validation_mae_kwh": learned["validation_mae_kwh"],
        }
    else:
        wastage = analytic_wastage
        current_range, optimized_range = analytic_current, analytic_optimized
        utilization = round(analytic_utilization)
        intelligence = {
            "prediction_mode": "explainable_analytics_fallback",
            "model": "EVision analytics engine",
            "ml_weight": 0.0,
        }

    arrival_buffer = current_range - round(telemetry.route_distance)
    breakdown = build_breakdown(telemetry, wastage)
    suggestions = generate_suggestions(telemetry, current_range, optimized_range, wastage)

    return TripAnalysis(
        battery_utilization_index=utilization,
        current_predicted_range=current_range,
        optimized_predicted_range=optimized_range,
        energy_wastage_percent=wastage,
        arrival_buffer=arrival_buffer,
        energy_breakdown=breakdown,
        suggestions=suggestions,
        trip_summary={
            "route_distance": telemetry.route_distance,
            "range_gain_if_optimized": max(0, optimized_range - current_range),
            "destination_status": "reachable" if arrival_buffer >= 0 else "charging_recommended",
            "main_improvement": suggestions[0].title if suggestions else "Maintain current driving style",
        },
        intelligence=intelligence,
    )
