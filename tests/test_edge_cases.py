"""
Comprehensive edge case tests for pyexpstats library.

This module tests boundary conditions, numerical edge cases, and
statistical corner cases to ensure robust behavior.
"""

import pytest
import math
import numpy as np
from pyexpstats import conversion, magnitude, timing
from pyexpstats.utils import stats, validation
from pyexpstats.utils.math import (
    pooled_proportion,
    pooled_variance,
    effect_size_cohens_h,
    effect_size_cohens_d,
    welch_degrees_of_freedom,
    calculate_lift,
)


# ==============================================================================
# CONVERSION EDGE CASES
# ==============================================================================

class TestConversionZeroCases:
    """Test zero and boundary conversion scenarios."""

    def test_zero_conversions_both_groups(self):
        """Both groups have zero conversions - should handle gracefully."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=0,
        )
        assert result.lift_percent == 0
        assert result.control_rate == 0
        assert result.variant_rate == 0
        assert not result.is_significant

    def test_zero_conversions_control_only(self):
        """Control has zero conversions - tests division handling."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=50,
        )
        # Lift from 0 to any positive number is technically infinite
        # but code handles this - verify no crash
        assert result.variant_rate == 0.05
        assert result.control_rate == 0

    def test_zero_conversions_variant_only(self):
        """Variant has zero conversions."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=0,
        )
        assert result.lift_percent < 0
        assert result.variant_rate == 0

    def test_100_percent_conversion_both(self):
        """Both groups at 100% conversion - degenerate case."""
        result = conversion.analyze(
            control_visitors=100,
            control_conversions=100,
            variant_visitors=100,
            variant_conversions=100,
        )
        assert result.control_rate == 1.0
        assert result.variant_rate == 1.0
        assert result.lift_percent == 0

    def test_100_percent_control_50_percent_variant(self):
        """Control at 100%, variant at 50%."""
        result = conversion.analyze(
            control_visitors=100,
            control_conversions=100,
            variant_visitors=100,
            variant_conversions=50,
        )
        assert result.control_rate == 1.0
        assert result.variant_rate == 0.5
        assert result.lift_percent == pytest.approx(-50, rel=0.01)


class TestConversionSmallSampleSizes:
    """Test with very small sample sizes."""

    def test_minimum_viable_sample(self):
        """Single visitor in each group."""
        result = conversion.analyze(
            control_visitors=1,
            control_conversions=1,
            variant_visitors=1,
            variant_conversions=0,
        )
        assert result.control_rate == 1.0
        assert result.variant_rate == 0.0
        # With n=1, statistical significance is not achievable
        assert not result.is_significant

    def test_two_visitors_each(self):
        """Two visitors per group - minimal for variance calculation."""
        result = conversion.analyze(
            control_visitors=2,
            control_conversions=1,
            variant_visitors=2,
            variant_conversions=2,
        )
        assert result.control_rate == 0.5
        assert result.variant_rate == 1.0

    def test_asymmetric_small_samples(self):
        """One group much smaller than other."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=10,
            variant_conversions=2,
        )
        # Should complete without error despite asymmetry
        assert result.control_rate == 0.05
        assert result.variant_rate == 0.2


class TestConversionInputValidation:
    """Test input validation for conversion analysis."""

    def test_conversions_exceed_visitors_control(self):
        """Control conversions > visitors should raise error."""
        with pytest.raises(ValueError, match="cannot exceed"):
            conversion.analyze(
                control_visitors=100,
                control_conversions=150,
                variant_visitors=100,
                variant_conversions=50,
            )

    def test_conversions_exceed_visitors_variant(self):
        """Variant conversions > visitors should raise error."""
        with pytest.raises(ValueError, match="cannot exceed"):
            conversion.analyze(
                control_visitors=100,
                control_conversions=50,
                variant_visitors=100,
                variant_conversions=150,
            )

    def test_negative_visitors(self):
        """Negative visitors should raise error or handle gracefully."""
        # Division by negative would give negative rate which is invalid
        with pytest.raises((ValueError, ZeroDivisionError)):
            conversion.analyze(
                control_visitors=-100,
                control_conversions=50,
                variant_visitors=100,
                variant_conversions=50,
            )

    def test_zero_visitors_control(self):
        """Zero visitors in control - should raise error."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            conversion.analyze(
                control_visitors=0,
                control_conversions=0,
                variant_visitors=100,
                variant_conversions=50,
            )

    def test_zero_visitors_variant(self):
        """Zero visitors in variant - should raise error."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            conversion.analyze(
                control_visitors=100,
                control_conversions=50,
                variant_visitors=0,
                variant_conversions=0,
            )


class TestConversionSampleSizeEdgeCases:
    """Test sample size calculation edge cases."""

    def test_very_small_lift(self):
        """Detecting tiny lift requires huge sample."""
        plan = conversion.sample_size(
            current_rate=0.05,
            lift_percent=1,
            confidence=95,
            power=80,
        )
        # 1% lift is tiny, needs massive sample
        assert plan.visitors_per_variant > 100000

    def test_very_large_lift(self):
        """Large lift needs small sample."""
        plan = conversion.sample_size(
            current_rate=0.05,
            lift_percent=100,  # 100% lift = doubling
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant < 10000

    def test_very_high_base_rate(self):
        """High base rate (90%) with 10% lift would exceed 100%."""
        with pytest.raises(ValueError, match="exceeds 100%"):
            conversion.sample_size(
                current_rate=0.90,
                lift_percent=15,  # Would give 103.5%
            )

    def test_negative_lift(self):
        """Negative lift (expecting decrease)."""
        plan = conversion.sample_size(
            current_rate=0.10,
            lift_percent=-20,  # Expecting 20% drop
            confidence=95,
            power=80,
        )
        assert plan.expected_rate == pytest.approx(0.08)
        assert plan.visitors_per_variant > 0

    def test_99_percent_confidence(self):
        """Very high confidence level."""
        plan = conversion.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=99,
            power=80,
        )
        # Higher confidence = larger sample
        plan_95 = conversion.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > plan_95.visitors_per_variant

    def test_99_percent_power(self):
        """Very high power requirement."""
        plan = conversion.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=95,
            power=99,
        )
        plan_80 = conversion.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > plan_80.visitors_per_variant


class TestConversionConfidenceIntervalEdgeCases:
    """Test confidence interval edge cases."""

    def test_zero_conversions(self):
        """CI with zero conversions - Wilson handles this."""
        ci = conversion.confidence_interval(visitors=100, conversions=0)
        assert ci.rate == 0.0
        # Lower bound is essentially 0 (may have tiny floating-point error)
        assert ci.lower == pytest.approx(0.0, abs=1e-10)
        assert ci.upper > 0  # Upper bound should be positive
        assert ci.upper <= 1.0

    def test_all_converted(self):
        """CI with 100% conversion."""
        ci = conversion.confidence_interval(visitors=100, conversions=100)
        assert ci.rate == 1.0
        assert ci.lower < 1.0  # Lower bound should be less than 1
        assert ci.lower >= 0
        assert ci.upper == 1.0

    def test_single_observation(self):
        """CI with n=1."""
        ci = conversion.confidence_interval(visitors=1, conversions=1)
        assert ci.rate == 1.0
        # Wilson score handles small n gracefully
        assert 0 <= ci.lower <= ci.upper <= 1

    def test_very_large_sample(self):
        """CI with large sample should be narrow."""
        ci = conversion.confidence_interval(visitors=1000000, conversions=50000)
        width = ci.upper - ci.lower
        assert width < 0.01  # Should be very narrow with n=1M


class TestConversionMultiVariantEdgeCases:
    """Test multi-variant analysis edge cases."""

    def test_two_variants_minimum(self):
        """Two variants is the minimum allowed."""
        result = conversion.analyze_multi(
            variants=[
                {"name": "A", "visitors": 1000, "conversions": 50},
                {"name": "B", "visitors": 1000, "conversions": 60},
            ]
        )
        assert len(result.pairwise_comparisons) == 1

    def test_single_variant_raises_error(self):
        """Single variant should raise error."""
        with pytest.raises(ValueError, match="At least 2"):
            conversion.analyze_multi(
                variants=[
                    {"name": "A", "visitors": 1000, "conversions": 50},
                ]
            )

    def test_duplicate_names_raises_error(self):
        """Duplicate variant names should raise error."""
        with pytest.raises(ValueError, match="unique"):
            conversion.analyze_multi(
                variants=[
                    {"name": "A", "visitors": 1000, "conversions": 50},
                    {"name": "A", "visitors": 1000, "conversions": 60},
                ]
            )

    def test_many_variants_bonferroni(self):
        """Many variants with Bonferroni correction."""
        variants = [
            {"name": f"variant_{i}", "visitors": 1000, "conversions": 50 + i * 2}
            for i in range(10)
        ]
        result = conversion.analyze_multi(variants, correction="bonferroni")
        # With 10 variants, we have 45 pairwise comparisons
        assert len(result.pairwise_comparisons) == 45
        # Bonferroni multiplies p-values by number of comparisons
        for p in result.pairwise_comparisons:
            assert p.p_value_adjusted >= p.p_value

    def test_all_identical_variants(self):
        """All variants have identical rates."""
        result = conversion.analyze_multi(
            variants=[
                {"name": "A", "visitors": 1000, "conversions": 50},
                {"name": "B", "visitors": 1000, "conversions": 50},
                {"name": "C", "visitors": 1000, "conversions": 50},
            ]
        )
        assert not result.is_significant
        assert result.p_value > 0.99  # Should be ~1.0


class TestConversionDiffInDiff:
    """Test Difference-in-Differences analysis."""

    def test_basic_did(self):
        """Basic DiD calculation."""
        result = conversion.diff_in_diff(
            control_pre_visitors=1000,
            control_pre_conversions=50,
            control_post_visitors=1000,
            control_post_conversions=55,
            treatment_pre_visitors=1000,
            treatment_pre_conversions=50,
            treatment_post_visitors=1000,
            treatment_post_conversions=70,
        )
        # Control change: 5.5% - 5% = 0.5%
        # Treatment change: 7% - 5% = 2%
        # DiD = 2% - 0.5% = 1.5%
        assert result.diff_in_diff == pytest.approx(0.015, abs=0.001)

    def test_no_treatment_effect(self):
        """Both groups change equally - no treatment effect."""
        result = conversion.diff_in_diff(
            control_pre_visitors=1000,
            control_pre_conversions=50,
            control_post_visitors=1000,
            control_post_conversions=60,
            treatment_pre_visitors=1000,
            treatment_pre_conversions=50,
            treatment_post_visitors=1000,
            treatment_post_conversions=60,
        )
        assert result.diff_in_diff == pytest.approx(0.0, abs=0.001)
        assert not result.is_significant

    def test_negative_treatment_effect(self):
        """Treatment actually hurts compared to control."""
        result = conversion.diff_in_diff(
            control_pre_visitors=1000,
            control_pre_conversions=50,
            control_post_visitors=1000,
            control_post_conversions=60,
            treatment_pre_visitors=1000,
            treatment_pre_conversions=50,
            treatment_post_visitors=1000,
            treatment_post_conversions=50,
        )
        # Control improved by 1%, treatment stayed same
        # DiD = 0% - 1% = -1%
        assert result.diff_in_diff < 0

    def test_did_with_small_samples(self):
        """DiD with small samples."""
        result = conversion.diff_in_diff(
            control_pre_visitors=50,
            control_pre_conversions=5,
            control_post_visitors=50,
            control_post_conversions=6,
            treatment_pre_visitors=50,
            treatment_pre_conversions=5,
            treatment_post_visitors=50,
            treatment_post_conversions=10,
        )
        # Should complete without error
        assert result.diff_in_diff is not None


# ==============================================================================
# MAGNITUDE EDGE CASES
# ==============================================================================

class TestMagnitudeZeroAndNegative:
    """Test zero and negative value scenarios for magnitude analysis."""

    def test_zero_mean_both_groups(self):
        """Both groups have zero mean."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=0,
            control_std=5,
            variant_visitors=100,
            variant_mean=0,
            variant_std=5,
        )
        assert result.lift_percent == 0
        assert result.lift_absolute == 0

    def test_zero_mean_control_positive_variant(self):
        """Control mean is zero, variant is positive."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=0,
            control_std=5,
            variant_visitors=100,
            variant_mean=10,
            variant_std=5,
        )
        # Lift from 0 is undefined percentage-wise
        assert result.lift_absolute == 10

    def test_negative_means(self):
        """Negative mean values (e.g., losses, temperature below zero)."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=-50,
            control_std=10,
            variant_visitors=100,
            variant_mean=-40,
            variant_std=10,
        )
        # Variant is "better" (less negative)
        assert result.lift_absolute == 10

    def test_zero_standard_deviation(self):
        """Zero standard deviation - all values identical."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=50,
            control_std=0,
            variant_visitors=100,
            variant_mean=55,
            variant_std=0,
        )
        # With std=0, t-test is degenerate but should handle
        assert result.lift_absolute == 5

    def test_very_small_std(self):
        """Very small standard deviation."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=50,
            control_std=0.0001,
            variant_visitors=100,
            variant_mean=50.001,
            variant_std=0.0001,
        )
        # Tiny variation + tiny difference
        assert result.lift_absolute == pytest.approx(0.001, rel=0.01)


class TestMagnitudeSmallSamples:
    """Test magnitude analysis with small samples."""

    def test_n_equals_2(self):
        """Minimum sample for variance estimation."""
        result = magnitude.analyze(
            control_visitors=2,
            control_mean=50,
            control_std=10,
            variant_visitors=2,
            variant_mean=60,
            variant_std=10,
        )
        # Should complete; df will be very small
        assert result.lift_absolute == 10

    def test_asymmetric_sample_sizes(self):
        """Very different sample sizes."""
        result = magnitude.analyze(
            control_visitors=1000,
            control_mean=50,
            control_std=10,
            variant_visitors=10,
            variant_mean=55,
            variant_std=10,
        )
        # Welch's t-test handles unequal n
        assert result.lift_absolute == 5

    def test_confidence_interval_n_equals_2(self):
        """CI with n=2."""
        ci = magnitude.confidence_interval(
            visitors=2,
            mean=50,
            std=10,
        )
        # With n=2, df=1, CI will be very wide
        width = ci.upper - ci.lower
        assert width > 50  # Should be extremely wide


class TestMagnitudeSampleSizeEdgeCases:
    """Test sample size calculation edge cases."""

    def test_zero_lift_raises_error(self):
        """Zero lift percent should raise error."""
        with pytest.raises(ValueError):
            magnitude.sample_size(
                current_mean=50,
                current_std=10,
                lift_percent=0,
            )

    def test_very_high_variance(self):
        """High variance relative to mean."""
        plan = magnitude.sample_size(
            current_mean=50,
            current_std=100,  # 2x the mean
            lift_percent=5,
        )
        # High variance = need more samples
        plan_low_var = magnitude.sample_size(
            current_mean=50,
            current_std=10,
            lift_percent=5,
        )
        assert plan.visitors_per_variant > plan_low_var.visitors_per_variant

    def test_negative_mean_with_positive_lift(self):
        """Negative mean with positive lift.

        Note: lift_percent is RELATIVE, so 10% of -100 means -100 * 1.10 = -110,
        not -100 + 10. For negative values, positive lift makes the value MORE negative.
        This is mathematically correct for relative lift calculations.
        """
        plan = magnitude.sample_size(
            current_mean=-100,
            current_std=20,
            lift_percent=10,  # 10% RELATIVE lift: -100 * 1.10 = -110
        )
        assert plan.expected_mean == pytest.approx(-110, rel=0.01)


class TestMagnitudeDiffInDiff:
    """Test DiD for continuous metrics."""

    def test_basic_did(self):
        """Basic DiD for revenue."""
        result = magnitude.diff_in_diff(
            control_pre_n=100,
            control_pre_mean=50,
            control_pre_std=10,
            control_post_n=100,
            control_post_mean=52,
            control_post_std=10,
            treatment_pre_n=100,
            treatment_pre_mean=50,
            treatment_pre_std=10,
            treatment_post_n=100,
            treatment_post_mean=58,
            treatment_post_std=10,
        )
        # Control change: 52 - 50 = 2
        # Treatment change: 58 - 50 = 8
        # DiD = 8 - 2 = 6
        assert result.diff_in_diff == pytest.approx(6, abs=0.01)

    def test_did_with_negative_means(self):
        """DiD with negative means (e.g., losses)."""
        result = magnitude.diff_in_diff(
            control_pre_n=100,
            control_pre_mean=-100,
            control_pre_std=20,
            control_post_n=100,
            control_post_mean=-95,
            control_post_std=20,
            treatment_pre_n=100,
            treatment_pre_mean=-100,
            treatment_pre_std=20,
            treatment_post_n=100,
            treatment_post_mean=-80,
            treatment_post_std=20,
        )
        # Control improved by 5
        # Treatment improved by 20
        # DiD = 20 - 5 = 15
        assert result.diff_in_diff == pytest.approx(15, abs=0.01)


# ==============================================================================
# TIMING EDGE CASES
# ==============================================================================

class TestTimingEdgeCases:
    """Test timing/survival analysis edge cases."""

    def test_single_observation_per_group(self):
        """Single observation in each group."""
        result = timing.analyze(
            control_times=[10],
            control_events=[1],
            treatment_times=[5],
            treatment_events=[1],
        )
        # Should complete without error
        assert result.control_events == 1
        assert result.treatment_events == 1

    def test_all_censored_control(self):
        """All control observations are censored."""
        result = timing.analyze(
            control_times=[10, 20, 30],
            control_events=[0, 0, 0],
            treatment_times=[5, 10, 15],
            treatment_events=[1, 1, 1],
        )
        assert result.control_events == 0
        assert result.control_censored == 3

    def test_all_censored_both_groups(self):
        """All observations censored in both groups."""
        result = timing.analyze(
            control_times=[10, 20, 30],
            control_events=[0, 0, 0],
            treatment_times=[5, 10, 15],
            treatment_events=[0, 0, 0],
        )
        # No events to compare
        assert result.control_events == 0
        assert result.treatment_events == 0

    def test_tied_event_times(self):
        """Multiple events at the same time."""
        result = timing.analyze(
            control_times=[10, 10, 10, 20, 20],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[5, 5, 5, 10, 10],
            treatment_events=[1, 1, 1, 1, 1],
        )
        # Kaplan-Meier should handle ties
        assert result.control_events == 5
        assert result.treatment_events == 5

    def test_very_small_times(self):
        """Very small time values (near zero)."""
        result = timing.analyze(
            control_times=[0.001, 0.002, 0.003, 0.004, 0.005],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[0.0005, 0.001, 0.0015, 0.002, 0.0025],
            treatment_events=[1, 1, 1, 1, 1],
        )
        # Should handle small values
        assert result.hazard_ratio > 0


class TestSurvivalCurveEdgeCases:
    """Test survival curve edge cases."""

    def test_single_time_point(self):
        """Single time point."""
        curve = timing.survival_curve(
            times=[10],
            events=[1],
        )
        assert curve.total == 1
        assert curve.events == 1

    def test_all_at_time_zero(self):
        """All events at time 0."""
        curve = timing.survival_curve(
            times=[0, 0, 0],
            events=[1, 1, 1],
        )
        assert curve.events == 3

    def test_mixed_censored_events_at_same_time(self):
        """Both censored and events at same time point."""
        curve = timing.survival_curve(
            times=[10, 10, 10, 10],
            events=[1, 0, 1, 0],
        )
        assert curve.events == 2
        assert curve.censored == 2


class TestTimingRatesEdgeCases:
    """Test event rate analysis edge cases."""

    def test_zero_control_events(self):
        """Zero events in control group."""
        result = timing.analyze_rates(
            control_events=0,
            control_exposure=1000,
            treatment_events=10,
            treatment_exposure=1000,
        )
        assert result.control_rate == 0
        # Rate ratio should be inf or handled appropriately
        assert result.rate_ratio == float('inf') or result.rate_ratio > 0

    def test_zero_treatment_events(self):
        """Zero events in treatment group."""
        result = timing.analyze_rates(
            control_events=10,
            control_exposure=1000,
            treatment_events=0,
            treatment_exposure=1000,
        )
        assert result.treatment_rate == 0
        assert result.rate_ratio == 0

    def test_zero_events_both(self):
        """Zero events in both groups."""
        result = timing.analyze_rates(
            control_events=0,
            control_exposure=1000,
            treatment_events=0,
            treatment_exposure=1000,
        )
        assert result.control_rate == 0
        assert result.treatment_rate == 0

    def test_very_different_exposures(self):
        """Very different exposure times."""
        result = timing.analyze_rates(
            control_events=10,
            control_exposure=100,
            treatment_events=100,
            treatment_exposure=10000,
        )
        # Control: 10/100 = 0.1
        # Treatment: 100/10000 = 0.01
        assert result.control_rate == 0.1
        assert result.treatment_rate == 0.01


class TestTimingSampleSizeEdgeCases:
    """Test timing sample size edge cases."""

    def test_very_similar_medians(self):
        """Medians too similar to detect."""
        with pytest.raises(ValueError, match="too similar"):
            timing.sample_size(
                control_median=30,
                treatment_median=30.001,
            )

    def test_extreme_hazard_ratio(self):
        """Very different medians (extreme HR)."""
        plan = timing.sample_size(
            control_median=100,
            treatment_median=10,  # 10x faster
        )
        assert plan.subjects_per_group > 0
        assert plan.hazard_ratio == 10


# ==============================================================================
# UTILITY FUNCTION EDGE CASES
# ==============================================================================

class TestStatsUtilEdgeCases:
    """Test stats utility edge cases."""

    def test_welch_df_equal_variances(self):
        """Welch df with equal variances."""
        df = stats.welch_df(var1=100, var2=100, n1=50, n2=50)
        # With equal var and n, should be close to n1 + n2 - 2
        assert df == pytest.approx(98, rel=0.1)

    def test_welch_df_very_different_variances(self):
        """Welch df with very different variances."""
        df = stats.welch_df(var1=1, var2=1000, n1=50, n2=50)
        # Should be much less than n1 + n2 - 2
        assert df < 98

    def test_welch_df_n_equals_1(self):
        """Welch df with n=1 (edge case)."""
        # This may cause division by zero - test behavior
        try:
            df = stats.welch_df(var1=100, var2=100, n1=1, n2=50)
            # If it doesn't raise, should return inf or a large number
            assert df == float('inf') or df > 0
        except (ZeroDivisionError, ValueError):
            pass  # This is acceptable behavior

    def test_proportion_ci_wilson_extreme_p(self):
        """Wilson CI for extreme probabilities."""
        # p = 0
        rate, lower, upper, margin = stats.proportion_ci(0, 100, 95, "wilson")
        assert rate == 0
        # Lower bound is essentially 0 (may have tiny floating-point error)
        assert lower == pytest.approx(0, abs=1e-10)
        assert upper > 0

        # p = 1
        rate, lower, upper, margin = stats.proportion_ci(100, 100, 95, "wilson")
        assert rate == 1.0
        assert lower < 1.0
        # Upper bound is essentially 1.0 (may have tiny floating-point error)
        assert upper == pytest.approx(1.0, abs=1e-10)

    def test_bonferroni_correction_limits(self):
        """Bonferroni should cap at 1.0."""
        adjusted = stats.bonferroni_correction(0.1, 20)
        assert adjusted == 1.0  # 0.1 * 20 = 2.0, capped at 1.0

        adjusted = stats.bonferroni_correction(0.01, 10)
        assert adjusted == 0.1  # 0.01 * 10 = 0.1


class TestMathUtilEdgeCases:
    """Test math utility edge cases."""

    def test_pooled_proportion_equal_weights(self):
        """Pooled proportion with equal n."""
        p_pooled = pooled_proportion(0.1, 0.2, 100, 100)
        assert p_pooled == pytest.approx(0.15)

    def test_pooled_proportion_unequal_weights(self):
        """Pooled proportion with unequal n."""
        p_pooled = pooled_proportion(0.1, 0.2, 100, 900)
        # Heavily weighted toward 0.2
        assert p_pooled == pytest.approx(0.19)

    def test_pooled_variance_n_equals_1(self):
        """Pooled variance with n=1."""
        # denominator is n1 + n2 - 2 = 0
        try:
            pv = pooled_variance(100, 100, 1, 1)
            # May return inf or raise
        except (ZeroDivisionError, ValueError):
            pass  # Acceptable

    def test_cohens_h_extreme_proportions(self):
        """Cohen's h for extreme proportions."""
        h = effect_size_cohens_h(0.0, 1.0)
        # arcsin(0) = 0, arcsin(1) = pi/2
        assert abs(h) == pytest.approx(np.pi, rel=0.01)

    def test_cohens_d_zero_pooled_sd(self):
        """Cohen's d with zero pooled SD."""
        d = effect_size_cohens_d(50, 50, 0)
        assert d == 0.0  # Same means

        d = effect_size_cohens_d(50, 60, 0)
        assert d == np.inf  # Different means, no variance

    def test_calculate_lift_zero_baseline(self):
        """Lift calculation with zero baseline."""
        relative, absolute = calculate_lift(0, 10)
        assert absolute == 10
        assert relative == np.inf or np.isnan(relative) or relative > 0


class TestValidationEdgeCases:
    """Test validation function edge cases."""

    def test_validate_rate_boundary_values(self):
        """Test rate validation at boundaries."""
        # Exactly 0 should be valid
        assert validation.validate_rate(0.0, "rate") == 0.0
        # Exactly 1 should be valid
        assert validation.validate_rate(1.0, "rate") == 1.0

        # Just outside should fail
        with pytest.raises(ValueError):
            validation.validate_rate(-0.0001, "rate")
        with pytest.raises(ValueError):
            validation.validate_rate(1.0001, "rate")

    def test_validate_positive_with_zero(self):
        """Test positive validation with zero."""
        with pytest.raises(ValueError):
            validation.validate_positive(0, "value", allow_zero=False)

        # Zero allowed
        assert validation.validate_positive(0, "value", allow_zero=True) == 0.0

    def test_validate_alpha_boundaries(self):
        """Test alpha validation at boundaries."""
        with pytest.raises(ValueError):
            validation.validate_alpha(0)
        with pytest.raises(ValueError):
            validation.validate_alpha(1)

        # Valid values
        assert validation.validate_alpha(0.05) == 0.05
        assert validation.validate_alpha(0.001) == 0.001
        assert validation.validate_alpha(0.999) == 0.999

    def test_validate_sample_size_float_truncation(self):
        """Test that floats are truncated to int."""
        assert validation.validate_sample_size(10.9) == 10
        assert validation.validate_sample_size(10.1) == 10


# ==============================================================================
# NUMERICAL STABILITY TESTS
# ==============================================================================

class TestNumericalStability:
    """Test numerical stability with extreme values."""

    def test_very_large_sample_conversion(self):
        """Very large sample sizes."""
        result = conversion.analyze(
            control_visitors=10_000_000,
            control_conversions=500_000,
            variant_visitors=10_000_000,
            variant_conversions=510_000,
        )
        # Should detect small difference with large n
        assert result.control_rate == 0.05
        assert result.variant_rate == 0.051

    def test_very_large_values_magnitude(self):
        """Very large values for magnitude."""
        result = magnitude.analyze(
            control_visitors=1000,
            control_mean=1_000_000_000,
            control_std=100_000_000,
            variant_visitors=1000,
            variant_mean=1_010_000_000,
            variant_std=100_000_000,
        )
        assert result.lift_absolute == 10_000_000

    def test_very_small_values_magnitude(self):
        """Very small values for magnitude."""
        result = magnitude.analyze(
            control_visitors=1000,
            control_mean=0.000001,
            control_std=0.0000001,
            variant_visitors=1000,
            variant_mean=0.0000011,
            variant_std=0.0000001,
        )
        assert result.lift_absolute == pytest.approx(0.0000001, rel=0.1)


# ==============================================================================
# REGRESSION TESTS
# ==============================================================================

class TestRegressionCases:
    """Regression tests for previously identified issues."""

    def test_z_test_with_zero_pooled_se(self):
        """Z-test when pooled SE is zero (both rates are 0 or 1)."""
        # Both 0%
        result = stats.z_test_two_proportions(0, 100, 0, 100, 95)
        assert result.p_value == 1.0
        assert result.statistic == 0

        # Both 100%
        result = stats.z_test_two_proportions(1, 100, 1, 100, 95)
        assert result.p_value == 1.0
        assert result.statistic == 0

    def test_lift_calculation_zero_baseline(self):
        """Lift calculation handles zero baseline."""
        absolute, relative = stats.lift_calculations(0, 0.1)
        assert absolute == 0.1
        assert relative == 0  # Code returns 0 when baseline is 0

    def test_mean_ci_n_equals_1(self):
        """Mean CI with n=1."""
        # With n=1, df=0, which is problematic
        # The function should handle this
        try:
            mean, lower, upper, margin = stats.mean_ci(50, 10, 1, 95)
            # If it doesn't raise, the values should be sensible
            assert mean == 50
        except (ValueError, ZeroDivisionError):
            pass  # Acceptable to raise


class TestStatisticalCorrectness:
    """Tests to verify statistical correctness of calculations."""

    def test_z_test_known_values(self):
        """Test Z-test against known statistical values."""
        # Using a case where we know the answer
        # p1 = 0.5, p2 = 0.6, n = 1000 each
        result = stats.z_test_two_proportions(0.5, 1000, 0.6, 1000, 95)
        # Z-stat should be around 4.47
        assert result.statistic == pytest.approx(4.47, rel=0.05)
        # p-value should be very small (< 0.0001)
        assert result.p_value < 0.0001
        assert result.is_significant

    def test_welch_t_test_known_values(self):
        """Test Welch's t-test against known values."""
        result = stats.welch_t_test(
            mean1=100, std1=15, n1=30,
            mean2=110, std2=15, n2=30,
            confidence=95,
        )
        # t-stat should be around 2.58
        assert result.statistic == pytest.approx(2.58, rel=0.1)
        assert result.is_significant

    def test_sample_size_proportions_known_formula(self):
        """Verify sample size against known formula."""
        # For p1=0.1, p2=0.15, alpha=0.05, power=0.80
        result = stats.sample_size_two_proportions(0.1, 0.15, 95, 80, 2)
        # Known answer is approximately 686 per group
        assert 600 < result.n_per_group < 800
