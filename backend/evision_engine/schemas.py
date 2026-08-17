from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Literal


Traffic = Literal["light", "moderate", "dense"]
Weather = Literal["clear", "hot", "rain", "wind"]
RoadType = Literal["city", "highway", "hills", "mixed"]
DriveMode = Literal["eco", "normal", "sport"]


DEFAULT_TELEMETRY = {
    "battery": 68,
    "speed": 46,
    "acceleration": 36,
    "braking": 42,
    "ac_load": 38,
    "route_distance": 168,
    "traffic": "dense",
    "weather": "clear",
    "road_type": "city",
    "drive_mode": "eco",
    "charging_habit_score": 72,
    "past_efficiency_score": 78,
    "battery_voltage": 380,
    "battery_temperature": 28,
    "ambient_temperature": 25,
    "slope_percent": 0,
    "humidity": 55,
    "wind_speed": 3,
    "tire_pressure": 32,
    "vehicle_weight": 1800,
}


@dataclass
class Telemetry:
    battery: float
    speed: float
    acceleration: float
    braking: float
    ac_load: float
    route_distance: float
    traffic: Traffic
    weather: Weather
    road_type: RoadType
    drive_mode: DriveMode
    charging_habit_score: float = 72
    past_efficiency_score: float = 78
    battery_voltage: float = 380
    battery_temperature: float = 28
    ambient_temperature: float = 25
    slope_percent: float = 0
    humidity: float = 55
    wind_speed: float = 3
    tire_pressure: float = 32
    vehicle_weight: float = 1800

    def __post_init__(self) -> None:
        numeric_bounds = {
            "battery": (0, 100),
            "speed": (0, 220),
            "acceleration": (0, 100),
            "braking": (0, 100),
            "ac_load": (0, 100),
            "route_distance": (0, 1500),
            "charging_habit_score": (0, 100),
            "past_efficiency_score": (0, 100),
            "battery_voltage": (200, 900),
            "battery_temperature": (-30, 90),
            "ambient_temperature": (-50, 65),
            "slope_percent": (-35, 35),
            "humidity": (0, 100),
            "wind_speed": (0, 60),
            "tire_pressure": (15, 60),
            "vehicle_weight": (500, 5000),
        }
        for field, (low, high) in numeric_bounds.items():
            try:
                value = float(getattr(self, field))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field} must be numeric") from exc
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{field} must be between {low} and {high}")
            setattr(self, field, value)

        valid_categories = {
            "traffic": {"light", "moderate", "dense"},
            "weather": {"clear", "hot", "rain", "wind"},
            "road_type": {"city", "highway", "hills", "mixed"},
            "drive_mode": {"eco", "normal", "sport"},
        }
        for field, choices in valid_categories.items():
            if getattr(self, field) not in choices:
                raise ValueError(f"{field} must be one of: {', '.join(sorted(choices))}")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Suggestion:
    title: str
    message: str
    impact: str
    category: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TripAnalysis:
    battery_utilization_index: int
    current_predicted_range: int
    optimized_predicted_range: int
    energy_wastage_percent: float
    arrival_buffer: int
    energy_breakdown: dict[str, float]
    suggestions: list[Suggestion]
    trip_summary: dict[str, str | int | float]
    intelligence: dict[str, str | float]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["suggestions"] = [suggestion.to_dict() for suggestion in self.suggestions]
        return payload
