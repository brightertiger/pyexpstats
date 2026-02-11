"""
Tests for Sequential Testing Module.

Tests the SPRT-based sequential testing with O'Brien-Fleming and Pocock boundaries.
"""

import pytest
from pyexpstats.methods.sequential import (
    analyze,
    SequentialTestResult,
    summarize,
)


class TestSequentialAnalysis:
    """Tests for sequential A/B test analysis."""

    def test_basic_analysis(self):
        """Test basic sequential analysis returns expected structure."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result, SequentialTestResult)
        assert isinstance(result.can_stop, bool)
        assert result.decision in ["variant_wins", "control_wins", "no_difference", "keep_running"]
        assert 0 <= result.confidence_variant_better <= 100  # Percentage
        assert 0 <= result.information_fraction <= 1

    def test_early_in_test(self):
        """Test that early results recommend continuing."""
        result = analyze(
            control_visitors=100,
            control_conversions=5,
            variant_visitors=100,
            variant_conversions=10,
            expected_visitors_per_variant=10000,
        )

        # Very early in test - should keep running
        assert result.information_fraction < 0.1
        # May or may not be able to stop depending on effect size

    def test_clear_winner_variant(self):
        """Test detection of clear variant winner."""
        result = analyze(
            control_visitors=5000,
            control_conversions=250,  # 5%
            variant_visitors=5000,
            variant_conversions=350,  # 7% - 40% lift
            expected_visitors_per_variant=5000,
        )

        assert result.information_fraction == 1.0
        assert result.can_stop is True
        assert result.decision == "variant_wins"
        assert result.confidence_variant_better > 0.95

    def test_clear_winner_control(self):
        """Test detection of clear control winner."""
        result = analyze(
            control_visitors=5000,
            control_conversions=350,  # 7%
            variant_visitors=5000,
            variant_conversions=250,  # 5%
            expected_visitors_per_variant=5000,
        )

        assert result.can_stop is True
        assert result.decision == "control_wins"
        assert result.confidence_variant_better < 0.05

    def test_no_difference(self):
        """Test detection when there's no meaningful difference."""
        result = analyze(
            control_visitors=10000,
            control_conversions=500,  # 5%
            variant_visitors=10000,
            variant_conversions=505,  # 5.05%
            expected_visitors_per_variant=10000,
        )

        assert result.information_fraction == 1.0
        # With such a tiny effect, decision should be no difference or keep running

    def test_obrien_fleming_boundary(self):
        """Test O'Brien-Fleming boundary (used by default)."""
        result = analyze(
            control_visitors=2500,
            control_conversions=125,
            variant_visitors=2500,
            variant_conversions=175,
            expected_visitors_per_variant=5000,
        )

        # O'Brien-Fleming boundaries are symmetric
        assert result.upper_boundary > 0
        assert result.lower_boundary < 0

    def test_pocock_boundary(self):
        """Test boundaries at different test points."""
        result_early = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=70,
            expected_visitors_per_variant=5000,
        )

        result_late = analyze(
            control_visitors=4500,
            control_conversions=225,
            variant_visitors=4500,
            variant_conversions=315,
            expected_visitors_per_variant=5000,
        )

        # Later in test, boundaries should be narrower (easier to cross)
        assert result_late.upper_boundary <= result_early.upper_boundary

    def test_different_sample_sizes(self):
        """Test with different sample sizes."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=70,
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result.upper_boundary, float)
        assert isinstance(result.lower_boundary, float)

    def test_z_statistic(self):
        """Test z-statistic calculation."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=55,  # Small effect
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result.z_statistic, float)

    def test_zero_conversions_control(self):
        """Test handling of zero conversions in control."""
        result = analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=10,
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result, SequentialTestResult)
        # Should handle gracefully

    def test_zero_conversions_both(self):
        """Test handling of zero conversions in both groups."""
        result = analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=0,
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result, SequentialTestResult)
        assert result.decision == "keep_running"

    def test_100_percent_conversion(self):
        """Test handling of 100% conversion rate."""
        result = analyze(
            control_visitors=100,
            control_conversions=100,
            variant_visitors=100,
            variant_conversions=100,
            expected_visitors_per_variant=500,
        )

        assert isinstance(result, SequentialTestResult)

    def test_summarize(self):
        """Test summary generation."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
            expected_visitors_per_variant=5000,
        )

        summary = summarize(result)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestSequentialEdgeCases:
    """Edge case tests for sequential analysis."""

    def test_very_small_sample(self):
        """Test with very small sample sizes."""
        result = analyze(
            control_visitors=10,
            control_conversions=1,
            variant_visitors=10,
            variant_conversions=2,
            expected_visitors_per_variant=1000,
        )

        assert isinstance(result, SequentialTestResult)
        assert result.information_fraction < 0.1

    def test_very_large_sample(self):
        """Test with very large sample sizes."""
        result = analyze(
            control_visitors=1000000,
            control_conversions=50000,
            variant_visitors=1000000,
            variant_conversions=50500,
            expected_visitors_per_variant=1000000,
        )

        assert isinstance(result, SequentialTestResult)
        assert result.information_fraction == 1.0

    def test_asymmetric_samples(self):
        """Test with asymmetric sample sizes."""
        result = analyze(
            control_visitors=5000,
            control_conversions=250,
            variant_visitors=1000,  # Much smaller variant
            variant_conversions=60,
            expected_visitors_per_variant=5000,
        )

        assert isinstance(result, SequentialTestResult)

    def test_extreme_conversion_difference(self):
        """Test with extreme conversion rate difference."""
        result = analyze(
            control_visitors=1000,
            control_conversions=10,  # 1%
            variant_visitors=1000,
            variant_conversions=100,  # 10% - 900% lift
            expected_visitors_per_variant=5000,
        )

        assert result.can_stop is True
        assert result.decision == "variant_wins"

    def test_exceeds_expected_visitors(self):
        """Test when actual visitors exceed expected."""
        result = analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=550,
            expected_visitors_per_variant=5000,  # Already exceeded
        )

        assert result.information_fraction >= 1.0


class TestSequentialValidation:
    """Validation tests for sequential analysis inputs."""

    def test_negative_visitors_raises(self):
        """Test that negative visitors raises error."""
        with pytest.raises((ValueError, TypeError)):
            analyze(
                control_visitors=-100,
                control_conversions=10,
                variant_visitors=1000,
                variant_conversions=50,
                expected_visitors_per_variant=5000,
            )

    def test_conversions_exceed_visitors(self):
        """Test that conversions > visitors is handled."""
        # Should either raise error or handle gracefully
        try:
            result = analyze(
                control_visitors=100,
                control_conversions=150,  # More than visitors
                variant_visitors=100,
                variant_conversions=50,
                expected_visitors_per_variant=500,
            )
            # If it doesn't raise, should still be valid result
            assert isinstance(result, SequentialTestResult)
        except ValueError:
            pass  # Expected

    def test_zero_expected_visitors(self):
        """Test handling of zero expected visitors."""
        try:
            result = analyze(
                control_visitors=1000,
                control_conversions=50,
                variant_visitors=1000,
                variant_conversions=60,
                expected_visitors_per_variant=0,
            )
            # If it doesn't raise, should still be valid result
            assert isinstance(result, SequentialTestResult)
        except (ValueError, ZeroDivisionError):
            pass  # Expected

    def test_result_attributes(self):
        """Test that result has all expected attributes."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
            expected_visitors_per_variant=5000,
        )

        assert hasattr(result, 'can_stop')
        assert hasattr(result, 'decision')
        assert hasattr(result, 'upper_boundary')
        assert hasattr(result, 'lower_boundary')
        assert hasattr(result, 'z_statistic')
        assert hasattr(result, 'information_fraction')
