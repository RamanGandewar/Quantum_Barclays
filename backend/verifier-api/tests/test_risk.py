"""Unit tests for app.risk module."""

import math

from app.models import DataClass, MigrationState
from app.risk import (
    VALUE_MULTIPLIER,
    compute_risk,
    crqc_probability,
    recommended_action,
    risk_band,
)


class TestCrqcProbability:
    def test_at_median_year(self):
        assert abs(crqc_probability(2038) - 0.5) < 1e-6

    def test_far_past_is_near_zero(self):
        assert crqc_probability(2000) < 0.01

    def test_far_future_is_near_one(self):
        assert crqc_probability(2080) > 0.99

    def test_monotonically_increasing(self):
        vals = [crqc_probability(y) for y in range(2020, 2060, 5)]
        for i in range(len(vals) - 1):
            assert vals[i] < vals[i + 1]

    def test_symmetric_around_median(self):
        below = crqc_probability(2033)
        above = crqc_probability(2043)
        assert abs(below - (1.0 - above)) < 1e-6


class TestRiskBand:
    def test_critical(self):
        assert risk_band(10.0) == "critical"
        assert risk_band(50.0) == "critical"

    def test_high(self):
        assert risk_band(3.0) == "high"
        assert risk_band(9.99) == "high"

    def test_medium(self):
        assert risk_band(1.0) == "medium"
        assert risk_band(2.99) == "medium"

    def test_low(self):
        assert risk_band(0.0) == "low"
        assert risk_band(0.99) == "low"

    def test_boundaries(self):
        assert risk_band(0.999) == "low"
        assert risk_band(1.0) == "medium"
        assert risk_band(2.999) == "medium"
        assert risk_band(3.0) == "high"
        assert risk_band(9.999) == "high"
        assert risk_band(10.0) == "critical"


class TestRecommendedAction:
    def test_pqc_native_gets_maintain(self):
        action = recommended_action("critical", MigrationState.S4_PQC_NATIVE)
        assert "Maintain" in action

    def test_critical_high_urges_immediate(self):
        for band in ("critical", "high"):
            action = recommended_action(band, MigrationState.S0_CLASSICAL)
            assert "immediate" in action.lower() or "prioritize" in action.lower()

    def test_medium_schedules(self):
        action = recommended_action("medium", MigrationState.S2_HYBRID_KX)
        assert "schedule" in action.lower()

    def test_low_tracks(self):
        action = recommended_action("low", MigrationState.S0_CLASSICAL)
        assert "backlog" in action.lower() or "track" in action.lower()


class TestComputeRisk:
    def test_s4_native_has_zero_risk(self):
        result = compute_risk(
            MigrationState.S4_PQC_NATIVE,
            DataClass.confidential,
            lifetime_years=30,
            current_year=2026,
        )
        assert result["risk_score"] == 0.0
        assert result["quantum_security_level"] == 1.0

    def test_s0_classical_has_nonzero_risk(self):
        result = compute_risk(
            MigrationState.S0_CLASSICAL,
            DataClass.confidential,
            lifetime_years=30,
            current_year=2026,
        )
        assert result["risk_score"] > 0

    def test_higher_data_class_increases_risk(self):
        low = compute_risk(
            MigrationState.S0_CLASSICAL, DataClass.public, 30, current_year=2026
        )
        high = compute_risk(
            MigrationState.S0_CLASSICAL, DataClass.top_secret, 30, current_year=2026
        )
        assert high["risk_score"] > low["risk_score"]
        assert high["value_multiplier"] > low["value_multiplier"]

    def test_longer_lifetime_increases_risk(self):
        short = compute_risk(
            MigrationState.S0_CLASSICAL, DataClass.confidential, 5, current_year=2026
        )
        long = compute_risk(
            MigrationState.S0_CLASSICAL, DataClass.confidential, 50, current_year=2026
        )
        assert long["risk_score"] > short["risk_score"]

    def test_returns_all_fields(self):
        result = compute_risk(
            MigrationState.S0_CLASSICAL, DataClass.confidential, 10, current_year=2026
        )
        for key in (
            "crqc_probability",
            "quantum_security_level",
            "value_multiplier",
            "risk_score",
            "risk_band",
            "recommended_action",
        ):
            assert key in result

    def test_value_multipliers_match_definition(self):
        for dc, mult in VALUE_MULTIPLIER.items():
            result = compute_risk(
                MigrationState.S0_CLASSICAL, dc, 10, current_year=2026
            )
            assert result["value_multiplier"] == mult

    def test_score_equals_probability_times_security_times_multiplier(self):
        result = compute_risk(
            MigrationState.S2_HYBRID_KX,
            DataClass.confidential,
            20,
            current_year=2026,
        )
        prob = result["crqc_probability"]
        security = result["quantum_security_level"]
        mult = result["value_multiplier"]
        expected = prob * (1.0 - security) * mult
        assert abs(result["risk_score"] - round(expected, 6)) < 1e-5
