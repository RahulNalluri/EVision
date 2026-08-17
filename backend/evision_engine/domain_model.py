from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.evision_engine.schemas import Telemetry


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "evision_energy_model.json"


def feature_values(telemetry: Telemetry) -> dict[str, float]:
    speed = telemetry.speed
    acceleration = (telemetry.acceleration - 50) / 16.67
    route_distance = min(max(telemetry.route_distance, 0.1), 49.99)
    road_type = {"city": "city", "highway": "highway", "hills": "rural", "mixed": "city"}[telemetry.road_type]
    weather = {"clear": "clear", "hot": "clear", "rain": "rain", "wind": "fog"}[telemetry.weather]
    raw = {
        "speed_kmh": speed,
        "speed_squared": speed * speed,
        "acceleration_ms2": acceleration,
        "absolute_acceleration": abs(acceleration),
        "battery_state_percent": telemetry.battery,
        "battery_voltage_v": telemetry.battery_voltage,
        "battery_temperature_c": telemetry.battery_temperature,
        "slope_percent": telemetry.slope_percent,
        "absolute_slope": abs(telemetry.slope_percent),
        "ambient_temperature_c": telemetry.ambient_temperature,
        "temperature_delta": abs(telemetry.battery_temperature - telemetry.ambient_temperature),
        "humidity_percent": telemetry.humidity,
        "wind_speed_ms": telemetry.wind_speed,
        "tire_pressure_psi": telemetry.tire_pressure,
        "vehicle_weight_kg": telemetry.vehicle_weight,
        "route_distance_km": route_distance,
    }
    categories = {
        "drive_mode": telemetry.drive_mode,
        "road_type": road_type,
        "traffic": telemetry.traffic,
        "weather": weather,
    }
    choices = {
        "drive_mode": ["normal", "sport"],
        "road_type": ["city", "rural"],
        "traffic": ["moderate", "dense"],
        "weather": ["rain", "snow", "fog"],
    }
    for field, selected in categories.items():
        for choice in choices[field]:
            raw[f"{field}={choice}"] = 1.0 if selected == choice else 0.0
    return raw


@lru_cache(maxsize=1)
def load_model() -> dict | None:
    if not MODEL_PATH.exists():
        return None
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def predict(telemetry: Telemetry) -> dict[str, float] | None:
    model = load_model()
    if not model:
        return None
    raw = feature_values(telemetry)
    means = model["normalization"]["means"]
    stds = model["normalization"]["standard_deviations"]
    normalized = {
        name: (raw[name] - means[name]) / max(stds[name], 1e-8)
        for name in model["features"]
    }
    energy = model["intercept"] + sum(
        model["coefficients"][name] * normalized[name]
        for name in model["features"]
    )
    return {
        "energy_consumption_kwh": max(0.1, energy),
        "reference_efficiency_kwh_per_km": model["reference_efficiency_kwh_per_km"],
        "model_distance_km": raw["route_distance_km"],
        "validation_mae_kwh": model["validation"]["mae_kwh"],
    }
