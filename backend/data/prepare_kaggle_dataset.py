from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "kaggle_ev_energy" / "files" / "EV_Energy_Consumption_Dataset.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "evision_energy_training.csv"

DRIVE_MODE = {"1": "eco", "2": "normal", "3": "sport"}
ROAD_TYPE = {"1": "highway", "2": "city", "3": "rural"}
TRAFFIC = {"1": "light", "2": "moderate", "3": "dense"}
WEATHER = {"1": "clear", "2": "rain", "3": "snow", "4": "fog"}

FIELDS = [
    "speed_kmh", "speed_squared", "acceleration_ms2", "absolute_acceleration",
    "battery_state_percent", "battery_voltage_v", "battery_temperature_c", "drive_mode",
    "road_type", "traffic", "slope_percent", "absolute_slope", "weather",
    "ambient_temperature_c", "temperature_delta", "humidity_percent", "wind_speed_ms",
    "tire_pressure_psi", "vehicle_weight_kg", "route_distance_km", "energy_consumption_kwh",
]


def number(row: dict[str, str], field: str) -> float:
    return float(row[field])


def transform(row: dict[str, str]) -> dict[str, str | float]:
    speed = number(row, "Speed_kmh")
    acceleration = number(row, "Acceleration_ms2")
    battery_temperature = number(row, "Battery_Temperature_C")
    ambient_temperature = number(row, "Temperature_C")
    slope = number(row, "Slope_%")
    return {
        "speed_kmh": speed, "speed_squared": speed * speed,
        "acceleration_ms2": acceleration, "absolute_acceleration": abs(acceleration),
        "battery_state_percent": number(row, "Battery_State_%"),
        "battery_voltage_v": number(row, "Battery_Voltage_V"),
        "battery_temperature_c": battery_temperature,
        "drive_mode": DRIVE_MODE[row["Driving_Mode"]], "road_type": ROAD_TYPE[row["Road_Type"]],
        "traffic": TRAFFIC[row["Traffic_Condition"]], "slope_percent": slope,
        "absolute_slope": abs(slope), "weather": WEATHER[row["Weather_Condition"]],
        "ambient_temperature_c": ambient_temperature,
        "temperature_delta": abs(battery_temperature - ambient_temperature),
        "humidity_percent": number(row, "Humidity_%"), "wind_speed_ms": number(row, "Wind_Speed_ms"),
        "tire_pressure_psi": number(row, "Tire_Pressure_psi"),
        "vehicle_weight_kg": number(row, "Vehicle_Weight_kg"),
        "route_distance_km": number(row, "Distance_Travelled_km"),
        "energy_consumption_kwh": number(row, "Energy_Consumption_kWh"),
    }


def main() -> None:
    if not RAW_PATH.exists():
        raise SystemExit("Kaggle dataset missing. See data/raw/kaggle_ev_energy/DATASET.md for download instructions.")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with RAW_PATH.open("r", encoding="utf-8", newline="") as source, OUTPUT_PATH.open("w", encoding="utf-8", newline="") as destination:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(destination, fieldnames=FIELDS)
        writer.writeheader()
        for row in reader:
            writer.writerow(transform(row))
            written += 1
    print(f"Prepared {written} Kaggle records at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
