"""
Tests for Planning Module.

Tests MDE calculation and Duration recommendations.
"""

import pytest
from expstats.planning.mde import (
    minimum_detectable_effect,
    MDEResult,
)
from expstats.planning.duration import (
    recommend_duration,
    DurationRecommendation,
)


class TestMDECalculation:
    """Tests for Minimum Detectable Effect calculation."""

    def test_basic_mde_calculation(self):
        """Test basic MDE calculation."""
        result = minimum_detectable_effect(
            sample_size_per_variant=5000,
            baseline_rate=0.05,
        )

        assert isinstance(result, MDEResult)
        assert result.minimum_detectable_effect > 0
        assert result.minimum_detectable_absolute > 0

    def test_mde_from_traffic(self):
        """Test MDE calculation from daily traffic and duration."""
        result = minimum_detectable_effect(
            daily_traffic=10000,
            test_duration_days=14,
            baseline_rate=0.05,
        )

        assert isinstance(result, MDEResult)
        # 70,000 per variant
        assert result.sample_size_per_variant == 70000

    def test_mde_decreases_with_more_sample(self):
        """Test that MDE decreases with larger sample size."""
        result_small = minimum_detectable_effect(
            sample_size_per_variant=1000,
            baseline_rate=0.05,
        )

        result_large = minimum_detectable_effect(
            sample_size_per_variant=100000,
            baseline_rate=0.05,
        )

        assert result_large.minimum_detectable_effect < result_small.minimum_detectable_effect

    def test_higher_baseline_lower_mde(self):
        """Test that higher baseline rates have lower MDE (in relative terms)."""
        result_low = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.01,  # 1%
        )

        result_high = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.20,  # 20%
        )

        # Higher baseline should have lower relative MDE
        assert result_high.minimum_detectable_effect < result_low.minimum_detectable_effect

    def test_detectable_variant_rate(self):
        """Test detectable variant rate calculation."""
        result = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.05,
        )

        expected_variant = 0.05 * (1 + result.minimum_detectable_effect / 100)
        assert pytest.approx(result.detectable_variant_rate, abs=0.001) == expected_variant

    def test_target_mde_achievable(self):
        """Test target MDE that is achievable."""
        result = minimum_detectable_effect(
            sample_size_per_variant=100000,
            baseline_rate=0.05,
            target_mde=20.0,  # 20% lift
        )

        assert result.minimum_detectable_effect < 20.0
        assert result.sample_needed_for_target is not None

    def test_target_mde_not_achievable(self):
        """Test target MDE that is not achievable."""
        result = minimum_detectable_effect(
            sample_size_per_variant=1000,
            baseline_rate=0.05,
            target_mde=5.0,  # 5% lift - hard to detect with small sample
        )

        # MDE is likely higher than target
        if result.minimum_detectable_effect > 5.0:
            assert result.sample_needed_for_target > 1000

    def test_is_practically_useful(self):
        """Test practical usefulness flag."""
        # Large sample = small MDE = useful
        result_useful = minimum_detectable_effect(
            sample_size_per_variant=100000,
            baseline_rate=0.05,
        )

        # Small sample = large MDE = not useful
        result_not_useful = minimum_detectable_effect(
            sample_size_per_variant=100,
            baseline_rate=0.05,
        )

        assert result_useful.is_practically_useful == True
        assert result_not_useful.is_practically_useful == False

    def test_confidence_and_power(self):
        """Test different confidence and power settings."""
        result_standard = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.05,
            confidence=95,
            power=80,
        )

        result_high = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.05,
            confidence=99,
            power=90,
        )

        # Higher confidence/power requires larger MDE
        assert result_high.minimum_detectable_effect > result_standard.minimum_detectable_effect

    def test_continuous_metric(self):
        """Test MDE for continuous metrics."""
        result = minimum_detectable_effect(
            sample_size_per_variant=5000,
            baseline_rate=100.0,  # Mean value
            metric_type="continuous",
            baseline_std=25.0,  # Standard deviation
        )

        assert isinstance(result, MDEResult)

    def test_percentage_input_handling(self):
        """Test that percentage inputs are handled correctly."""
        result1 = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.05,
        )

        result2 = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=5,  # 5% as percentage
        )

        assert pytest.approx(result1.minimum_detectable_effect, abs=0.1) == result2.minimum_detectable_effect

    def test_recommendation_generated(self):
        """Test that recommendation text is generated."""
        result = minimum_detectable_effect(
            sample_size_per_variant=10000,
            baseline_rate=0.05,
        )

        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_zero_sample_raises(self):
        """Test that zero sample size raises error."""
        with pytest.raises(ValueError):
            minimum_detectable_effect(
                sample_size_per_variant=0,
                baseline_rate=0.05,
            )

    def test_negative_sample_raises(self):
        """Test that negative sample size raises error."""
        with pytest.raises(ValueError):
            minimum_detectable_effect(
                sample_size_per_variant=-100,
                baseline_rate=0.05,
            )

    def test_missing_parameters_raises(self):
        """Test that missing parameters raise error."""
        with pytest.raises(ValueError):
            minimum_detectable_effect(
                baseline_rate=0.05,
                # Missing sample_size_per_variant and daily_traffic/duration
            )


class TestDurationRecommendation:
    """Tests for test duration recommendations."""

    def test_basic_recommendation(self):
        """Test basic duration recommendation."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
        )

        assert isinstance(result, DurationRecommendation)
        assert result.recommended_days > 0
        assert result.minimum_days > 0
        assert result.ideal_days >= result.recommended_days

    def test_minimum_days_includes_weekly_cycle(self):
        """Test that minimum days includes weekly cycle by default."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=100000,  # High traffic = quick stat minimum
            include_weekly_cycle=True,
        )

        assert result.weekly_cycle_days == 7
        assert result.minimum_days >= 7

    def test_no_weekly_cycle(self):
        """Test without weekly cycle requirement."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=100000,
            include_weekly_cycle=False,
        )

        assert result.weekly_cycle_days == 1

    def test_monthly_cycle(self):
        """Test with monthly cycle consideration."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=10000,
            include_monthly_cycle=True,
        )

        assert result.monthly_consideration is True

    def test_low_traffic_longer_duration(self):
        """Test that low traffic requires longer duration."""
        result_low = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=100,  # Low traffic
        )

        result_high = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=100000,  # High traffic
        )

        assert result_low.recommended_days > result_high.recommended_days

    def test_smaller_mde_longer_duration(self):
        """Test that smaller MDE requires longer duration."""
        result_small = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.05,  # 5% lift
            daily_traffic=5000,
        )

        result_large = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.20,  # 20% lift
            daily_traffic=5000,
        )

        assert result_small.recommended_days > result_large.recommended_days

    def test_ecommerce_business_type(self):
        """Test e-commerce specific recommendations."""
        result = recommend_duration(
            baseline_rate=0.03,
            minimum_detectable_effect=0.10,
            daily_traffic=10000,
            business_type="ecommerce",
        )

        assert isinstance(result.recommendation, str)
        # E-commerce should recommend at least 2 weeks
        assert result.recommended_days >= 14

    def test_saas_business_type(self):
        """Test SaaS specific recommendations."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
            business_type="saas",
        )

        assert isinstance(result.recommendation, str)

    def test_content_business_type(self):
        """Test content site specific recommendations."""
        result = recommend_duration(
            baseline_rate=0.10,
            minimum_detectable_effect=0.05,
            daily_traffic=50000,
            business_type="content",
        )

        assert isinstance(result.recommendation, str)

    def test_sample_size_calculation(self):
        """Test that sample sizes are calculated correctly."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=10000,
        )

        assert result.required_sample_per_variant > 0
        assert result.expected_sample_per_variant > 0
        # Expected should be based on recommended days
        expected = (10000 // 2) * result.recommended_days
        assert result.expected_sample_per_variant == expected

    def test_risk_assessment(self):
        """Test risk assessment generation."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
        )

        assert isinstance(result.risk_if_stopped_early, str)
        assert len(result.risk_if_stopped_early) > 0

    def test_confidence_at_durations(self):
        """Test confidence calculations at different durations."""
        result = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
        )

        assert 0 <= result.confidence_at_minimum <= 100
        assert 0 <= result.confidence_at_recommended <= 100
        # Recommended should have higher confidence
        assert result.confidence_at_recommended >= result.confidence_at_minimum

    def test_percentage_input_handling(self):
        """Test that percentage inputs are handled."""
        result1 = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
        )

        result2 = recommend_duration(
            baseline_rate=5,  # 5% as percentage
            minimum_detectable_effect=10,  # 10% as percentage
            daily_traffic=5000,
        )

        assert result1.recommended_days == result2.recommended_days

    def test_different_confidence_power(self):
        """Test different confidence and power levels."""
        result_standard = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
            confidence=95,
            power=80,
        )

        result_high = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.10,
            daily_traffic=5000,
            confidence=99,
            power=90,
        )

        # Higher requirements = longer duration
        assert result_high.recommended_days >= result_standard.recommended_days


class TestPlanningIntegration:
    """Integration tests for planning module."""

    def test_mde_to_duration_workflow(self):
        """Test using MDE to inform duration."""
        # First check MDE at current traffic
        mde = minimum_detectable_effect(
            daily_traffic=5000,
            test_duration_days=14,
            baseline_rate=0.05,
        )

        # Then get duration recommendation for target MDE
        duration = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=mde.minimum_detectable_effect / 100,  # Convert to decimal
            daily_traffic=5000,
        )

        # Duration should be around 14 days since that's what we used for MDE
        assert abs(duration.statistical_minimum_days - 14) < 5

    def test_plan_realistic_test(self):
        """Test planning a realistic A/B test."""
        # Scenario: E-commerce site, 5% conversion, want to detect 15% lift
        mde = minimum_detectable_effect(
            daily_traffic=10000,
            test_duration_days=21,  # 3 weeks
            baseline_rate=0.05,
            target_mde=15.0,
        )

        duration = recommend_duration(
            baseline_rate=0.05,
            minimum_detectable_effect=0.15,
            daily_traffic=10000,
            business_type="ecommerce",
        )

        # Should be achievable
        assert mde.minimum_detectable_effect <= 15.0
        assert duration.recommended_days <= 21
