from __future__ import annotations

import unittest

from backend.evision_engine.model import analyze_trip
from backend.evision_engine.schemas import DEFAULT_TELEMETRY, Telemetry


class EVisionEngineTests(unittest.TestCase):
    def test_hybrid_model_returns_guarded_trip_analysis(self) -> None:
        result = analyze_trip(Telemetry(**DEFAULT_TELEMETRY))
        self.assertEqual(result.intelligence["prediction_mode"], "hybrid_ml_and_analytics")
        self.assertGreater(result.current_predicted_range, 0)
        self.assertGreaterEqual(result.optimized_predicted_range, result.current_predicted_range)
        self.assertGreaterEqual(result.battery_utilization_index, 35)
        self.assertLessEqual(result.battery_utilization_index, 98)
        self.assertTrue(result.suggestions)

    def test_aggressive_driving_creates_actionable_guidance(self) -> None:
        telemetry = Telemetry(**{**DEFAULT_TELEMETRY, "speed": 105, "acceleration": 90, "drive_mode": "sport"})
        result = analyze_trip(telemetry)
        titles = {suggestion.title for suggestion in result.suggestions}
        self.assertIn("Smooth acceleration", titles)
        self.assertIn("Reduce cruising speed", titles)

    def test_invalid_battery_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "battery must be between"):
            Telemetry(**{**DEFAULT_TELEMETRY, "battery": 140})

    def test_destination_risk_is_reported(self) -> None:
        telemetry = Telemetry(**{**DEFAULT_TELEMETRY, "battery": 20, "route_distance": 300})
        result = analyze_trip(telemetry)
        self.assertEqual(result.trip_summary["destination_status"], "charging_recommended")


if __name__ == "__main__":
    unittest.main()
