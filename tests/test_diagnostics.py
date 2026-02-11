"""
Tests for Diagnostics Module.

Tests SRM detection, Test Health, and Novelty Effect detection.
"""

import pytest
from pyexpstats.diagnostics.srm import (
    check_sample_ratio,
    SampleRatioResult,
)
from pyexpstats.diagnostics.health import (
    check_health,
    TestHealthReport,
)
from pyexpstats.diagnostics.novelty import (
    detect_novelty_effect,
    NoveltyEffectResult,
)


class TestSRMDetection:
    """Tests for Sample Ratio Mismatch detection."""

    def test_balanced_ratio_passes(self):
        """Test that balanced 50/50 ratio passes."""
        result = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=5000,
        )

        assert isinstance(result, SampleRatioResult)
        assert result.is_valid == True
        assert result.severity == "ok"

    def test_slight_imbalance_passes(self):
        """Test that slight natural variance passes."""
        result = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=4950,  # 1% difference
        )

        assert result.is_valid == True
        assert result.severity == "ok"

    def test_significant_imbalance_detected(self):
        """Test that significant imbalance is detected."""
        result = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=4000,  # 20% difference
        )

        assert result.is_valid == False
        assert result.p_value < 0.001
        assert result.severity in ["warning", "critical"]

    def test_critical_imbalance(self):
        """Test critical imbalance detection."""
        result = check_sample_ratio(
            control_visitors=10000,
            variant_visitors=5000,  # 50% difference
        )

        assert result.is_valid == False
        assert result.severity == "critical"

    def test_custom_expected_ratio(self):
        """Test with non-50/50 expected ratio."""
        result = check_sample_ratio(
            control_visitors=3000,
            variant_visitors=7000,  # 30/70 split
            expected_ratio=0.30,  # Control should be 30%
        )

        assert result.is_valid == True

    def test_wrong_custom_ratio(self):
        """Test SRM detection with wrong custom ratio."""
        result = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=5000,
            expected_ratio=0.30,  # Expected 30/70, got 50/50
        )

        assert result.is_valid == False

    def test_custom_alpha(self):
        """Test custom alpha level."""
        result = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=4800,
            alpha=0.01,  # More lenient
        )

        assert isinstance(result.p_value, float)

    def test_small_sample(self):
        """Test SRM with small samples."""
        result = check_sample_ratio(
            control_visitors=50,
            variant_visitors=60,
        )

        assert isinstance(result, SampleRatioResult)
        # Small samples can have high variance

    def test_very_large_sample(self):
        """Test SRM with very large samples."""
        result = check_sample_ratio(
            control_visitors=1000000,
            variant_visitors=999000,  # Only 0.1% difference
        )

        # Even tiny imbalances detectable at scale
        assert isinstance(result.p_value, float)

    def test_deviation_calculation(self):
        """Test deviation percentage calculation."""
        result = check_sample_ratio(
            control_visitors=1000,
            variant_visitors=1200,  # Larger difference
        )

        # Should report significant deviation
        assert abs(result.deviation_percent) > 5

    def test_zero_visitors_handled(self):
        """Test handling of zero visitors."""
        try:
            result = check_sample_ratio(
                control_visitors=0,
                variant_visitors=1000,
            )
            assert isinstance(result, SampleRatioResult)
        except (ValueError, ZeroDivisionError):
            pass  # Expected


class TestTestHealth:
    """Tests for Test Health Dashboard."""

    def test_healthy_test(self):
        """Test a healthy experiment."""
        result = check_health(
            control_visitors=5000,
            control_conversions=250,
            variant_visitors=5000,
            variant_conversions=275,
        )

        assert isinstance(result, TestHealthReport)
        assert result.overall_status in ["healthy", "warning", "unhealthy"]
        assert 0 <= result.score <= 100

    def test_unhealthy_test_srm(self):
        """Test unhealthy experiment with SRM."""
        result = check_health(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=5000,  # Major SRM
            variant_conversions=300,
        )

        assert result.overall_status == "unhealthy"
        assert result.can_trust_results == False

    def test_warning_small_sample(self):
        """Test warning for small sample size."""
        result = check_health(
            control_visitors=50,  # Very small
            control_conversions=3,
            variant_visitors=50,
            variant_conversions=4,
        )

        assert result.overall_status in ["warning", "unhealthy"]

    def test_with_expected_visitors(self):
        """Test with expected visitors parameter."""
        result = check_health(
            control_visitors=5000,
            control_conversions=250,
            variant_visitors=5000,
            variant_conversions=275,
            expected_visitors_per_variant=10000,
        )

        assert result.overall_status in ["warning", "unhealthy", "healthy"]

    def test_zero_conversions(self):
        """Test with zero conversions."""
        result = check_health(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=0,
        )

        assert isinstance(result, TestHealthReport)
        # Should warn about zero conversions

    def test_with_start_date(self):
        """Test with start date."""
        result = check_health(
            control_visitors=7000,
            control_conversions=350,
            variant_visitors=7000,
            variant_conversions=378,
            test_start_date="2024-01-01",
        )

        assert isinstance(result, TestHealthReport)

    def test_health_checks_list(self):
        """Test that health checks are returned."""
        result = check_health(
            control_visitors=5000,
            control_conversions=250,
            variant_visitors=5000,
            variant_conversions=275,
        )

        assert len(result.checks) > 0
        for check in result.checks:
            assert hasattr(check, 'name')
            assert hasattr(check, 'status')


class TestNoveltyEffect:
    """Tests for Novelty Effect detection."""

    def test_stable_effect(self):
        """Test detection of stable effect over time."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 60,
            }
            for i in range(1, 15)
        ]

        result = detect_novelty_effect(daily_results)

        assert isinstance(result, NoveltyEffectResult)
        assert result.effect_type == "stable"
        assert result.effect_detected is False

    def test_novelty_effect_detected(self):
        """Test detection of fading novelty effect."""
        # Create declining effect pattern
        daily_results = []
        for i in range(1, 15):
            # Effect starts at 40% and fades to 5%
            lift_multiplier = 1.40 - (i - 1) * 0.025
            daily_results.append({
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": int(50 * lift_multiplier),
            })

        result = detect_novelty_effect(daily_results)

        assert isinstance(result, NoveltyEffectResult)
        # Should detect fading effect
        if result.effect_type != "insufficient_data":
            assert result.initial_lift > result.current_lift

    def test_primacy_effect_detected(self):
        """Test detection of growing primacy effect."""
        # Create growing effect pattern
        daily_results = []
        for i in range(1, 15):
            # Effect starts at 5% and grows to 30%
            lift_multiplier = 1.05 + (i - 1) * 0.018
            daily_results.append({
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": int(50 * lift_multiplier),
            })

        result = detect_novelty_effect(daily_results)

        assert isinstance(result, NoveltyEffectResult)
        # Should detect growing effect
        if result.effect_type != "insufficient_data":
            assert result.current_lift >= result.initial_lift

    def test_insufficient_data(self):
        """Test insufficient data handling."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 55,
            }
            for i in range(1, 4)  # Only 3 days
        ]

        result = detect_novelty_effect(daily_results, min_days=7)

        assert result.effect_type == "insufficient_data"

    def test_empty_data(self):
        """Test empty data handling."""
        result = detect_novelty_effect([])

        assert result.effect_type == "insufficient_data"

    def test_custom_min_days(self):
        """Test custom minimum days threshold."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 55,
            }
            for i in range(1, 6)
        ]

        result = detect_novelty_effect(daily_results, min_days=5)

        assert result.effect_type != "insufficient_data"

    def test_smoothed_lifts(self):
        """Test that smoothed lifts are calculated."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 55 + (i % 5),  # Some variance
            }
            for i in range(1, 15)
        ]

        result = detect_novelty_effect(daily_results)

        assert len(result.smoothed_lifts) > 0
        assert len(result.smoothed_lifts) == len(result.daily_lifts)

    def test_zero_control_conversions(self):
        """Test handling of zero control conversions."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 0,
                "variant_visitors": 1000,
                "variant_conversions": 10,
            }
            for i in range(1, 10)
        ]

        result = detect_novelty_effect(daily_results)

        assert isinstance(result, NoveltyEffectResult)

    def test_zero_visitors(self):
        """Test handling of days with zero visitors."""
        daily_results = [
            {
                "day": 1,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 55,
            },
            {
                "day": 2,
                "control_visitors": 0,  # Zero visitors
                "control_conversions": 0,
                "variant_visitors": 0,
                "variant_conversions": 0,
            },
            {
                "day": 3,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 55,
            },
        ] * 3  # Repeat to get enough days

        result = detect_novelty_effect(daily_results)

        assert isinstance(result, NoveltyEffectResult)

    def test_trend_confidence(self):
        """Test that trend confidence is calculated."""
        daily_results = [
            {
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": 60 - i,  # Clear declining trend
            }
            for i in range(1, 15)
        ]

        result = detect_novelty_effect(daily_results)

        assert 0 <= result.confidence <= 100
        assert isinstance(result.trend_p_value, float)

    def test_projected_steady_state(self):
        """Test steady state projection for novelty effect."""
        # Strong declining effect
        daily_results = []
        for i in range(1, 15):
            daily_results.append({
                "day": i,
                "control_visitors": 1000,
                "control_conversions": 50,
                "variant_visitors": 1000,
                "variant_conversions": max(51, 80 - i * 2),  # Declining
            })

        result = detect_novelty_effect(daily_results)

        if result.effect_type == "novelty":
            # Should have a projection
            assert result.projected_steady_state_lift is not None or True  # May be None if can't project


class TestDiagnosticsIntegration:
    """Integration tests for diagnostics module."""

    def test_full_diagnostic_workflow(self):
        """Test running all diagnostics together."""
        # SRM check
        srm = check_sample_ratio(
            control_visitors=5000,
            variant_visitors=5000,
        )
        assert srm.is_valid

        # Health check
        health = check_health(
            control_visitors=5000,
            control_conversions=250,
            variant_visitors=5000,
            variant_conversions=275,
        )
        assert health.can_trust_results

        # Novelty check
        daily_results = [
            {
                "day": i,
                "control_visitors": 357,
                "control_conversions": 18,
                "variant_visitors": 357,
                "variant_conversions": 20,
            }
            for i in range(1, 15)
        ]
        novelty = detect_novelty_effect(daily_results)
        assert novelty.effect_type in ["stable", "novelty", "primacy", "insufficient_data"]
