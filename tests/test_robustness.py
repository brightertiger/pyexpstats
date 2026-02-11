"""
Robustness tests for pyexpstats library.

These tests focus on:
1. Type safety and input validation
2. Error handling and graceful degradation
3. Statistical correctness verification
4. API consistency
"""

import pytest
import math
import numpy as np
from pyexpstats import conversion, magnitude, timing
from pyexpstats.utils import stats, validation
from pyexpstats.effects.outcome.conversion import ConversionEffect
from pyexpstats.effects.outcome.magnitude import MagnitudeEffect
from pyexpstats.effects.outcome.timing import TimingEffect


# ==============================================================================
# TYPE SAFETY TESTS
# ==============================================================================

class TestTypeSafetyConversion:
    """Test type handling for conversion analysis."""

    def test_integer_conversions_as_float(self):
        """Floats passed as integers should work."""
        result = conversion.analyze(
            control_visitors=1000.0,  # float
            control_conversions=50.0,  # float
            variant_visitors=1000.0,
            variant_conversions=60.0,
        )
        assert result.control_rate == 0.05

    def test_numpy_int_inputs(self):
        """Numpy integer types should work."""
        result = conversion.analyze(
            control_visitors=np.int64(1000),
            control_conversions=np.int64(50),
            variant_visitors=np.int64(1000),
            variant_conversions=np.int64(60),
        )
        assert result.control_rate == 0.05

    def test_string_inputs_raise_error(self):
        """String inputs should raise appropriate error."""
        with pytest.raises((TypeError, ValueError)):
            conversion.analyze(
                control_visitors="1000",
                control_conversions=50,
                variant_visitors=1000,
                variant_conversions=60,
            )


class TestTypeSafetyMagnitude:
    """Test type handling for magnitude analysis."""

    def test_numpy_float_inputs(self):
        """Numpy float types should work."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=np.float64(50.0),
            control_std=np.float64(10.0),
            variant_visitors=100,
            variant_mean=np.float64(55.0),
            variant_std=np.float64(10.0),
        )
        assert result.lift_absolute == 5.0

    def test_mixed_int_float(self):
        """Mixed int and float should work."""
        result = magnitude.analyze(
            control_visitors=100,
            control_mean=50,  # int
            control_std=10.0,  # float
            variant_visitors=100,
            variant_mean=55.5,  # float
            variant_std=10,  # int
        )
        assert result.lift_absolute == 5.5


class TestTypeSafetyTiming:
    """Test type handling for timing analysis."""

    def test_list_inputs(self):
        """Standard list inputs."""
        result = timing.analyze(
            control_times=[1, 2, 3, 4, 5],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[0.5, 1, 1.5, 2, 2.5],
            treatment_events=[1, 1, 1, 1, 1],
        )
        assert result.control_events == 5

    def test_numpy_array_inputs(self):
        """Numpy array inputs."""
        result = timing.analyze(
            control_times=np.array([1, 2, 3, 4, 5]),
            control_events=np.array([1, 1, 1, 1, 1]),
            treatment_times=np.array([0.5, 1, 1.5, 2, 2.5]),
            treatment_events=np.array([1, 1, 1, 1, 1]),
        )
        assert result.control_events == 5

    def test_tuple_inputs(self):
        """Tuple inputs should work (converted to array internally)."""
        result = timing.analyze(
            control_times=(1, 2, 3, 4, 5),
            control_events=(1, 1, 1, 1, 1),
            treatment_times=(0.5, 1, 1.5, 2, 2.5),
            treatment_events=(1, 1, 1, 1, 1),
        )
        assert result.control_events == 5


# ==============================================================================
# ERROR HANDLING TESTS
# ==============================================================================

class TestErrorMessagesConversion:
    """Test that error messages are helpful."""

    def test_error_message_conversions_exceed(self):
        """Error message for conversions > visitors."""
        with pytest.raises(ValueError) as exc_info:
            conversion.analyze(
                control_visitors=100,
                control_conversions=150,
                variant_visitors=100,
                variant_conversions=50,
            )
        assert "cannot exceed" in str(exc_info.value).lower()

    def test_error_message_invalid_rate(self):
        """Error message for invalid rate.

        Note: Values > 1 are interpreted as percentages (e.g., 5 -> 0.05).
        So 1.5 becomes 0.015 which is valid. To test invalid rates,
        we need values that are truly invalid after conversion.
        """
        # Rate of 101 (as percentage) would give 1.01 which is invalid
        with pytest.raises(ValueError) as exc_info:
            conversion.sample_size(current_rate=101, lift_percent=10)
        # Should mention the rate is out of bounds
        assert "rate" in str(exc_info.value).lower() or "100%" in str(exc_info.value)

    def test_rate_conversion_from_percentage(self):
        """Values > 1 are treated as percentages."""
        # 5 is interpreted as 5%, not 500%
        plan = conversion.sample_size(current_rate=5, lift_percent=10)
        assert plan.current_rate == 0.05

        # 1.5 is interpreted as 1.5%
        plan = conversion.sample_size(current_rate=1.5, lift_percent=10)
        assert plan.current_rate == 0.015

    def test_error_message_expected_rate_exceeds(self):
        """Error message when expected rate exceeds 100%."""
        with pytest.raises(ValueError) as exc_info:
            conversion.sample_size(current_rate=0.9, lift_percent=20)
        assert "exceeds 100%" in str(exc_info.value) or "exceed" in str(exc_info.value).lower()


class TestErrorMessagesMagnitude:
    """Test error messages for magnitude analysis."""

    def test_error_message_negative_visitors(self):
        """Error message for negative visitors."""
        with pytest.raises(ValueError) as exc_info:
            magnitude.analyze(
                control_visitors=-100,
                control_mean=50,
                control_std=10,
                variant_visitors=100,
                variant_mean=55,
                variant_std=10,
            )
        assert "positive" in str(exc_info.value).lower() or "visitors" in str(exc_info.value).lower()

    def test_error_message_negative_std(self):
        """Error message for negative std."""
        with pytest.raises(ValueError) as exc_info:
            magnitude.analyze(
                control_visitors=100,
                control_mean=50,
                control_std=-10,
                variant_visitors=100,
                variant_mean=55,
                variant_std=10,
            )
        assert "negative" in str(exc_info.value).lower() or "std" in str(exc_info.value).lower()


class TestErrorMessagesTiming:
    """Test error messages for timing analysis."""

    def test_error_message_length_mismatch(self):
        """Error message for mismatched array lengths."""
        with pytest.raises(ValueError) as exc_info:
            timing.survival_curve(
                times=[1, 2, 3],
                events=[1, 1],  # Wrong length
            )
        assert "same length" in str(exc_info.value).lower() or "mismatch" in str(exc_info.value).lower()

    def test_error_message_invalid_events(self):
        """Error message for invalid event values."""
        with pytest.raises(ValueError) as exc_info:
            timing.survival_curve(
                times=[1, 2, 3],
                events=[0, 1, 2],  # 2 is invalid
            )
        assert "0" in str(exc_info.value) and "1" in str(exc_info.value)

    def test_error_message_empty_times(self):
        """Error message for empty times array."""
        with pytest.raises(ValueError) as exc_info:
            timing.survival_curve(times=[], events=[])
        assert "empty" in str(exc_info.value).lower()


# ==============================================================================
# STATISTICAL CONSISTENCY TESTS
# ==============================================================================

class TestStatisticalConsistency:
    """Test that statistical properties hold."""

    def test_p_value_bounds(self):
        """P-values should always be in [0, 1]."""
        # Significant case
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )
        assert 0 <= result.p_value <= 1

        # Non-significant case
        result = conversion.analyze(
            control_visitors=100,
            control_conversions=5,
            variant_visitors=100,
            variant_conversions=5,
        )
        assert 0 <= result.p_value <= 1

    def test_confidence_interval_contains_point_estimate(self):
        """CI should contain the point estimate."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        # Point estimate is lift_absolute
        assert result.confidence_interval_lower <= result.lift_absolute <= result.confidence_interval_upper

    def test_higher_confidence_wider_ci(self):
        """Higher confidence should give wider CI."""
        ci_90 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=90)
        ci_95 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=95)
        ci_99 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=99)

        width_90 = ci_90.upper - ci_90.lower
        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower

        assert width_90 < width_95 < width_99

    def test_larger_sample_narrower_ci(self):
        """Larger sample should give narrower CI."""
        ci_100 = conversion.confidence_interval(visitors=100, conversions=5)
        ci_1000 = conversion.confidence_interval(visitors=1000, conversions=50)
        ci_10000 = conversion.confidence_interval(visitors=10000, conversions=500)

        width_100 = ci_100.upper - ci_100.lower
        width_1000 = ci_1000.upper - ci_1000.lower
        width_10000 = ci_10000.upper - ci_10000.lower

        assert width_100 > width_1000 > width_10000

    def test_symmetric_lift(self):
        """Swapping control/variant should give opposite lift."""
        result1 = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        result2 = conversion.analyze(
            control_visitors=1000,
            control_conversions=60,
            variant_visitors=1000,
            variant_conversions=50,
        )
        # Absolute lifts should be opposite
        assert result1.lift_absolute == pytest.approx(-result2.lift_absolute, abs=0.0001)

    def test_identical_groups_not_significant(self):
        """Identical groups should never be significant."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=50,
        )
        assert not result.is_significant
        assert result.p_value > 0.99  # Should be ~1.0


class TestStatisticalConsistencyMagnitude:
    """Statistical consistency for magnitude analysis."""

    def test_p_value_bounds_magnitude(self):
        """P-values should be in [0, 1]."""
        result = magnitude.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        assert 0 <= result.p_value <= 1

    def test_ci_contains_estimate_magnitude(self):
        """CI should contain point estimate."""
        result = magnitude.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        assert result.confidence_interval_lower <= result.lift_absolute <= result.confidence_interval_upper

    def test_symmetric_lift_magnitude(self):
        """Swapping groups should give opposite lift."""
        result1 = magnitude.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        result2 = magnitude.analyze(
            control_visitors=500,
            control_mean=55,
            control_std=15,
            variant_visitors=500,
            variant_mean=50,
            variant_std=15,
        )
        assert result1.lift_absolute == pytest.approx(-result2.lift_absolute, abs=0.01)


class TestStatisticalConsistencyTiming:
    """Statistical consistency for timing analysis."""

    def test_hazard_ratio_symmetry(self):
        """HR of A vs B should be inverse of B vs A."""
        result1 = timing.analyze(
            control_times=[10, 20, 30, 40, 50],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[5, 10, 15, 20, 25],
            treatment_events=[1, 1, 1, 1, 1],
        )
        result2 = timing.analyze(
            control_times=[5, 10, 15, 20, 25],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[10, 20, 30, 40, 50],
            treatment_events=[1, 1, 1, 1, 1],
        )
        # HR should be inverse
        assert result1.hazard_ratio * result2.hazard_ratio == pytest.approx(1.0, rel=0.1)

    def test_rate_ratio_symmetry(self):
        """Rate ratio symmetry."""
        result1 = timing.analyze_rates(
            control_events=50,
            control_exposure=1000,
            treatment_events=100,
            treatment_exposure=1000,
        )
        result2 = timing.analyze_rates(
            control_events=100,
            control_exposure=1000,
            treatment_events=50,
            treatment_exposure=1000,
        )
        # Rate ratios should be inverse
        assert result1.rate_ratio * result2.rate_ratio == pytest.approx(1.0, rel=0.01)


# ==============================================================================
# SAMPLE SIZE POWER TESTS
# ==============================================================================

class TestSampleSizePowerRelationships:
    """Test relationships between sample size, power, and effect size."""

    def test_power_increases_sample_size(self):
        """Higher power requires larger sample."""
        plans = [
            conversion.sample_size(current_rate=0.05, lift_percent=10, power=p)
            for p in [50, 60, 70, 80, 90, 95]
        ]
        sample_sizes = [p.visitors_per_variant for p in plans]
        # Should be strictly increasing
        for i in range(len(sample_sizes) - 1):
            assert sample_sizes[i] < sample_sizes[i + 1]

    def test_effect_size_decreases_sample_size(self):
        """Larger effect size requires smaller sample."""
        plans = [
            conversion.sample_size(current_rate=0.05, lift_percent=lift)
            for lift in [5, 10, 20, 50, 100]
        ]
        sample_sizes = [p.visitors_per_variant for p in plans]
        # Should be strictly decreasing
        for i in range(len(sample_sizes) - 1):
            assert sample_sizes[i] > sample_sizes[i + 1]

    def test_confidence_increases_sample_size(self):
        """Higher confidence requires larger sample."""
        plans = [
            conversion.sample_size(current_rate=0.05, lift_percent=10, confidence=c)
            for c in [80, 90, 95, 99]
        ]
        sample_sizes = [p.visitors_per_variant for p in plans]
        # Should be strictly increasing
        for i in range(len(sample_sizes) - 1):
            assert sample_sizes[i] < sample_sizes[i + 1]


class TestSampleSizePowerRelationshipsMagnitude:
    """Sample size relationships for magnitude analysis."""

    def test_variance_increases_sample_size(self):
        """Higher variance requires larger sample."""
        plans = [
            magnitude.sample_size(current_mean=50, current_std=std, lift_percent=5)
            for std in [5, 10, 20, 50]
        ]
        sample_sizes = [p.visitors_per_variant for p in plans]
        # Should be strictly increasing with variance
        for i in range(len(sample_sizes) - 1):
            assert sample_sizes[i] < sample_sizes[i + 1]


# ==============================================================================
# OUTPUT FORMAT TESTS
# ==============================================================================

class TestOutputFormats:
    """Test output format consistency."""

    def test_summary_markdown_headers(self):
        """Summaries should have proper markdown headers."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        summary = conversion.summarize(result)
        assert "## " in summary  # H2 headers
        assert "**" in summary  # Bold text

    def test_summary_includes_key_metrics(self):
        """Summary should include all key metrics."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        summary = conversion.summarize(result)
        assert "p-value" in summary.lower()
        assert "confidence" in summary.lower()
        assert "%" in summary  # Percentage values

    def test_multi_variant_summary_table(self):
        """Multi-variant summary should include a table."""
        result = conversion.analyze_multi(
            variants=[
                {"name": "A", "visitors": 1000, "conversions": 50},
                {"name": "B", "visitors": 1000, "conversions": 60},
                {"name": "C", "visitors": 1000, "conversions": 70},
            ]
        )
        summary = conversion.summarize_multi(result)
        assert "|" in summary  # Table formatting
        assert "A" in summary
        assert "B" in summary
        assert "C" in summary


# ==============================================================================
# CLASS INTERFACE TESTS
# ==============================================================================

class TestClassInterface:
    """Test that class interfaces work correctly."""

    def test_conversion_effect_class(self):
        """ConversionEffect class methods."""
        effect = ConversionEffect()

        plan = effect.sample_size(current_rate=0.05, lift_percent=10)
        assert plan.visitors_per_variant > 0

        result = effect.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        assert result.control_rate == 0.05

    def test_magnitude_effect_class(self):
        """MagnitudeEffect class methods."""
        effect = MagnitudeEffect()

        plan = effect.sample_size(current_mean=50, current_std=10, lift_percent=5)
        assert plan.visitors_per_variant > 0

        result = effect.analyze(
            control_visitors=100,
            control_mean=50,
            control_std=10,
            variant_visitors=100,
            variant_mean=55,
            variant_std=10,
        )
        assert result.lift_absolute == 5

    def test_timing_effect_class(self):
        """TimingEffect class methods."""
        effect = TimingEffect()

        result = effect.analyze(
            control_times=[1, 2, 3, 4, 5],
            control_events=[1, 1, 1, 1, 1],
            treatment_times=[0.5, 1, 1.5, 2, 2.5],
            treatment_events=[1, 1, 1, 1, 1],
        )
        assert result.control_events == 5


# ==============================================================================
# DATA CLASS PROPERTY TESTS
# ==============================================================================

class TestDataClassProperties:
    """Test dataclass properties and computed values."""

    def test_conversion_result_properties(self):
        """ConversionTestResults properties."""
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )
        assert result.point_estimate == result.lift_absolute
        assert result.effect_size == result.lift_percent

    def test_conversion_ci_properties(self):
        """ConversionConfidenceInterval properties."""
        ci = conversion.confidence_interval(visitors=1000, conversions=50)
        assert ci.point_estimate == ci.rate
        assert ci.lower_bound == ci.lower
        assert ci.upper_bound == ci.upper

    def test_conversion_variant_rate_property(self):
        """ConversionVariant.rate property."""
        from pyexpstats.effects.outcome.conversion import ConversionVariant

        variant = ConversionVariant(name="test", visitors=1000, conversions=100)
        assert variant.rate == 0.1

        # Zero visitors edge case
        variant_zero = ConversionVariant(name="zero", visitors=0, conversions=0)
        assert variant_zero.rate == 0

    def test_sample_size_plan_properties(self):
        """SampleSizePlan properties."""
        plan = conversion.sample_size(current_rate=0.05, lift_percent=10)
        assert plan.subjects_per_group == plan.visitors_per_variant
        assert plan.total_subjects == plan.total_visitors

    def test_with_daily_traffic_mutation(self):
        """with_daily_traffic should mutate and return self."""
        plan = conversion.sample_size(current_rate=0.05, lift_percent=10)
        returned = plan.with_daily_traffic(1000)
        assert returned is plan  # Should return same object
        assert plan.test_duration_days is not None


# ==============================================================================
# VALIDATION FUNCTION TESTS
# ==============================================================================

class TestValidationFunctions:
    """Comprehensive validation function tests."""

    def test_validate_rate_type_error(self):
        """Non-numeric rate should raise TypeError."""
        with pytest.raises(TypeError):
            validation.validate_rate("0.5", "rate")

    def test_validate_positive_type_error(self):
        """Non-numeric value should raise TypeError."""
        with pytest.raises(TypeError):
            validation.validate_positive("100", "value")

    def test_validate_alpha_type_error(self):
        """Non-numeric alpha should raise TypeError."""
        with pytest.raises(TypeError):
            validation.validate_alpha("0.05")

    def test_validate_power_type_error(self):
        """Non-numeric power should raise TypeError."""
        with pytest.raises(TypeError):
            validation.validate_power("0.80")

    def test_validate_sample_size_type_error(self):
        """Non-numeric sample size should raise TypeError."""
        with pytest.raises(TypeError):
            validation.validate_sample_size("100", "n")

    def test_validate_sidedness_values(self):
        """Valid sidedness values."""
        assert validation.validate_sidedness("one-sided") == "one-sided"
        assert validation.validate_sidedness("two-sided") == "two-sided"

        with pytest.raises(ValueError):
            validation.validate_sidedness("both-sided")

    def test_validate_allocation_ratio(self):
        """Allocation ratio validation."""
        assert validation.validate_allocation_ratio(1.0) == 1.0
        assert validation.validate_allocation_ratio(0.5) == 0.5
        assert validation.validate_allocation_ratio(2) == 2.0

        with pytest.raises(ValueError):
            validation.validate_allocation_ratio(0)
        with pytest.raises(ValueError):
            validation.validate_allocation_ratio(-1)


# ==============================================================================
# EDGE CASE COMBINATION TESTS
# ==============================================================================

class TestEdgeCaseCombinations:
    """Test combinations of edge cases."""

    def test_small_sample_high_conversion(self):
        """Small sample with high conversion rate."""
        result = conversion.analyze(
            control_visitors=10,
            control_conversions=9,
            variant_visitors=10,
            variant_conversions=10,
        )
        assert result.control_rate == 0.9
        assert result.variant_rate == 1.0

    def test_large_sample_tiny_difference(self):
        """Large sample with tiny difference."""
        result = conversion.analyze(
            control_visitors=1000000,
            control_conversions=50000,
            variant_visitors=1000000,
            variant_conversions=50100,
        )
        # 0.01% difference with n=1M each
        # Should likely be significant
        assert 0 <= result.p_value <= 1

    def test_multi_variant_with_zero_conversions(self):
        """Multi-variant where one variant has zero conversions."""
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 1000, "conversions": 50},
                {"name": "variant_a", "visitors": 1000, "conversions": 0},
                {"name": "variant_b", "visitors": 1000, "conversions": 100},
            ]
        )
        assert result.worst_variant == "variant_a"
        assert result.best_variant == "variant_b"

    def test_did_with_negative_change(self):
        """DiD where both groups decline."""
        result = conversion.diff_in_diff(
            control_pre_visitors=1000,
            control_pre_conversions=100,
            control_post_visitors=1000,
            control_post_conversions=80,  # Decline
            treatment_pre_visitors=1000,
            treatment_pre_conversions=100,
            treatment_post_visitors=1000,
            treatment_post_conversions=60,  # Bigger decline
        )
        # Control declined 2%, treatment declined 4%
        # DiD = -4% - (-2%) = -2%
        assert result.diff_in_diff < 0
