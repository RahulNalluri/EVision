from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "evision_energy_training.csv"
MODEL_PATH = ROOT / "models" / "evision_energy_model.json"

NUMERIC_FEATURES = [
    "speed_kmh", "speed_squared", "acceleration_ms2", "absolute_acceleration",
    "battery_state_percent", "battery_voltage_v", "battery_temperature_c",
    "slope_percent", "absolute_slope", "ambient_temperature_c", "temperature_delta",
    "humidity_percent", "wind_speed_ms", "tire_pressure_psi", "vehicle_weight_kg",
    "route_distance_km",
]
CATEGORICAL_FEATURES = {
    "drive_mode": ["eco", "normal", "sport"],
    "road_type": ["highway", "city", "rural"],
    "traffic": ["light", "moderate", "dense"],
    "weather": ["clear", "rain", "snow", "fog"],
}
TARGET = "energy_consumption_kwh"


def read_rows() -> list[dict[str, str]]:
    if not DATA_PATH.exists():
        raise SystemExit("Processed Kaggle data is missing. Run: python -m backend.data.prepare_kaggle_dataset")
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def feature_names() -> list[str]:
    names = list(NUMERIC_FEATURES)
    for field, choices in CATEGORICAL_FEATURES.items():
        names.extend(f"{field}={choice}" for choice in choices[1:])
    return names


def raw_vector(row: dict[str, str]) -> list[float]:
    values = [float(row[feature]) for feature in NUMERIC_FEATURES]
    for field, choices in CATEGORICAL_FEATURES.items():
        values.extend(1.0 if row[field] == choice else 0.0 for choice in choices[1:])
    return values


def calculate_stats(rows: list[dict[str, str]]) -> tuple[list[float], list[float]]:
    vectors = [raw_vector(row) for row in rows]
    means = [sum(vector[i] for vector in vectors) / len(vectors) for i in range(len(vectors[0]))]
    stds = []
    for i, mean in enumerate(means):
        variance = sum((vector[i] - mean) ** 2 for vector in vectors) / len(vectors)
        stds.append(max(math.sqrt(variance), 1e-8))
    return means, stds


def normalized_vector(row: dict[str, str], means: list[float], stds: list[float]) -> list[float]:
    raw = raw_vector(row)
    return [1.0, *((value - means[i]) / stds[i] for i, value in enumerate(raw))]


def solve_linear_system(matrix: list[list[float]], values: list[float]) -> list[float]:
    size = len(values)
    augmented = [matrix[i][:] + [values[i]] for i in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        if abs(divisor) < 1e-12:
            continue
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * pivot_value
                for current, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [augmented[i][-1] for i in range(size)]


def fit_ridge(rows: list[dict[str, str]], means: list[float], stds: list[float], ridge: float) -> list[float]:
    vectors = [normalized_vector(row, means, stds) for row in rows]
    size = len(vectors[0])
    gram = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for vector, row in zip(vectors, rows):
        label = float(row[TARGET])
        for i in range(size):
            rhs[i] += vector[i] * label
            for j in range(size):
                gram[i][j] += vector[i] * vector[j]
    for i in range(1, size):
        gram[i][i] += ridge
    return solve_linear_system(gram, rhs)


def predict(row: dict[str, str], coefficients: list[float], means: list[float], stds: list[float]) -> float:
    return sum(
        coefficient * value
        for coefficient, value in zip(coefficients, normalized_vector(row, means, stds))
    )


def validation_metrics(rows: list[dict[str, str]], coefficients: list[float], means: list[float], stds: list[float]) -> dict[str, float]:
    actual = [float(row[TARGET]) for row in rows]
    predicted = [predict(row, coefficients, means, stds) for row in rows]
    errors = [estimate - label for estimate, label in zip(predicted, actual)]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    mean_actual = sum(actual) / len(actual)
    denominator = sum((value - mean_actual) ** 2 for value in actual)
    r2 = 1 - sum(error * error for error in errors) / denominator if denominator else 1.0
    return {"mae_kwh": round(mae, 4), "rmse_kwh": round(rmse, 4), "r2": round(r2, 4)}


def main(test_ratio: float = 0.2, ridge: float = 0.15) -> None:
    rows = read_rows()
    random.Random(42).shuffle(rows)
    split = max(1, round(len(rows) * (1 - test_ratio)))
    train_rows, test_rows = rows[:split], rows[split:]
    means, stds = calculate_stats(train_rows)
    names = feature_names()
    coefficients = fit_ridge(train_rows, means, stds, ridge)
    usable_rates = [
        float(row[TARGET]) / float(row["route_distance_km"])
        for row in rows if float(row["route_distance_km"]) >= 5
    ]
    model = {
        "name": "EVision Kaggle energy prediction model",
        "version": "2.0.0",
        "algorithm": "multi-feature ridge regression",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": "EV Energy Consumption Dataset", "provider": "Kaggle",
            "slug": "ziya07/ev-energy-consumption-dataset", "license": "CC0: Public Domain",
            "total_rows": len(rows), "train_rows": len(train_rows),
            "validation_rows": len(test_rows), "split_seed": 42,
        },
        "target": TARGET,
        "reference_efficiency_kwh_per_km": round(statistics.median(usable_rates), 6),
        "features": names,
        "normalization": {
            "means": dict(zip(names, means)),
            "standard_deviations": dict(zip(names, stds)),
        },
        "intercept": coefficients[0],
        "coefficients": dict(zip(names, coefficients[1:])),
        "validation": validation_metrics(test_rows, coefficients, means, stds),
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2), encoding="utf-8")
    metrics = model["validation"]
    print(f"Saved trained model to {MODEL_PATH}")
    print(f"Rows: {len(train_rows)} train / {len(test_rows)} validation")
    print(f"Energy prediction: MAE={metrics['mae_kwh']:.3f} kWh, RMSE={metrics['rmse_kwh']:.3f} kWh, R2={metrics['r2']:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EVision on processed Kaggle EV energy data.")
    parser.add_argument("--test-ratio", type=float, default=0.2, help="Validation split ratio.")
    parser.add_argument("--ridge", type=float, default=0.15, help="L2 regularization strength.")
    args = parser.parse_args()
    if not 0.1 <= args.test_ratio <= 0.4:
        parser.error("--test-ratio must be between 0.1 and 0.4")
    main(test_ratio=args.test_ratio, ridge=max(0.0, args.ridge))
