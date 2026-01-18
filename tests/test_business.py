"""
Tests for Business Module.

Tests Impact Projections and Guardrail Monitoring.
"""

import pytest
from expstats.business.impact import (
    project_impact,
    ImpactProjection,
)
from expstats.business.guardrails import (
    check_guardrails,
    GuardrailReport,
    GuardrailResult,
)


class TestImpactProjection:
    """Tests for revenue impact projections."""

    def test_basic_projection(self):
        """Test basic impact projection."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=2.0,
            lift_ci_upper=18.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert isinstance(result, ImpactProjection)
        assert result.monthly_revenue_lift > 0
        assert result.annual_revenue_lift == result.monthly_revenue_lift * 12

    def test_revenue_calculations(self):
        """Test revenue calculation accuracy."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.06,  # 20% lift
            lift_percent=20.0,
            lift_ci_lower=10.0,
            lift_ci_upper=30.0,
            monthly_visitors=100000,
            revenue_per_conversion=100.0,
        )

        # Control: 100K * 5% * $100 = $500K/month
        # Variant: 100K * 6% * $100 = $600K/month
        # Lift: $100K/month
        assert pytest.approx(result.monthly_revenue_lift, abs=1) == 100000

    def test_additional_conversions(self):
        """Test additional conversions calculation."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.06,
            lift_percent=20.0,
            lift_ci_lower=10.0,
            lift_ci_upper=30.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        # 100K * 6% - 100K * 5% = 1000 additional conversions
        assert pytest.approx(result.monthly_additional_conversions, abs=1) == 1000

    def test_negative_lift(self):
        """Test negative lift handling."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.04,
            lift_percent=-20.0,
            lift_ci_lower=-30.0,
            lift_ci_upper=-10.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert result.monthly_revenue_lift < 0
        assert result.probability_positive_impact < 0.5

    def test_confidence_interval_range(self):
        """Test revenue confidence interval."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=-5.0,  # Includes negative
            lift_ci_upper=25.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        lower, upper = result.revenue_lift_range
        assert lower < upper
        # Lower bound should be negative since CI includes negative lift
        assert lower < 0

    def test_probability_positive(self):
        """Test probability of positive impact."""
        # Clear positive result
        result_positive = project_impact(
            control_rate=0.05,
            variant_rate=0.06,
            lift_percent=20.0,
            lift_ci_lower=15.0,
            lift_ci_upper=25.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert result_positive.probability_positive_impact > 0.95

        # Clear negative result
        result_negative = project_impact(
            control_rate=0.05,
            variant_rate=0.04,
            lift_percent=-20.0,
            lift_ci_lower=-25.0,
            lift_ci_upper=-15.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert result_negative.probability_positive_impact < 0.05

    def test_incremental_value_per_visitor(self):
        """Test incremental value per visitor calculation."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.06,
            lift_percent=20.0,
            lift_ci_lower=10.0,
            lift_ci_upper=30.0,
            monthly_visitors=100000,
            revenue_per_conversion=100.0,
        )

        # Control: 5% * $100 = $5/visitor
        # Variant: 6% * $100 = $6/visitor
        # Incremental: $1/visitor
        assert pytest.approx(result.value_per_visitor_control, abs=0.01) == 5.0
        assert pytest.approx(result.value_per_visitor_variant, abs=0.01) == 6.0
        assert pytest.approx(result.incremental_value_per_visitor, abs=0.01) == 1.0

    def test_cost_of_change(self):
        """Test break-even with implementation cost."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=5.0,
            lift_ci_upper=15.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
            cost_of_change=50000,
        )

        assert isinstance(result.recommendation, str)
        # Recommendation should mention break-even if cost provided

    def test_percentage_inputs(self):
        """Test handling of percentage inputs."""
        result1 = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=2.0,
            lift_ci_upper=18.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        result2 = project_impact(
            control_rate=5,  # Percentage
            variant_rate=5.5,  # Percentage
            lift_percent=10.0,
            lift_ci_lower=2.0,
            lift_ci_upper=18.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert pytest.approx(result1.monthly_revenue_lift, abs=1) == result2.monthly_revenue_lift

    def test_expected_value(self):
        """Test expected value calculation."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=2.0,
            lift_ci_upper=18.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        # Expected value should be positive if probability positive is high
        assert result.expected_value >= 0

    def test_recommendation_generated(self):
        """Test that recommendation is generated."""
        result = project_impact(
            control_rate=0.05,
            variant_rate=0.055,
            lift_percent=10.0,
            lift_ci_lower=2.0,
            lift_ci_upper=18.0,
            monthly_visitors=100000,
            revenue_per_conversion=50.0,
        )

        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0


class TestGuardrails:
    """Tests for guardrail monitoring."""

    def test_all_guardrails_pass(self):
        """Test when all guardrails pass."""
        result = check_guardrails([
            {
                "name": "Page Load Time",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": [100, 110, 95, 105, 100] * 100,
                "variant_data": [102, 108, 97, 103, 101] * 100,  # Slight increase but within threshold
            },
            {
                "name": "Error Rate",
                "metric_type": "proportion",
                "direction": "increase_is_bad",
                "threshold_percent": 20,
                "control_data": {"count": 50, "total": 10000},
                "variant_data": {"count": 52, "total": 10000},
            },
        ])

        assert isinstance(result, GuardrailReport)
        assert result.all_passed is True
        assert result.can_ship is True
        assert len(result.failures) == 0

    def test_guardrail_failure(self):
        """Test guardrail failure detection."""
        result = check_guardrails([
            {
                "name": "Page Load Time",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 5,
                "critical_threshold_percent": 10,
                "control_data": [100] * 500,
                "variant_data": [120] * 500,  # 20% increase - critical
            },
        ])

        assert result.has_failures is True
        assert result.can_ship is False
        assert "Page Load Time" in result.failures

    def test_guardrail_warning(self):
        """Test guardrail warning detection."""
        result = check_guardrails([
            {
                "name": "Error Rate",
                "metric_type": "proportion",
                "direction": "increase_is_bad",
                "threshold_percent": 5,
                "critical_threshold_percent": 20,
                "control_data": {"count": 100, "total": 10000},
                "variant_data": {"count": 110, "total": 10000},  # 10% increase - warning
            },
        ])

        assert result.has_warnings is True
        assert result.can_ship is True  # Warnings don't block shipping

    def test_decrease_is_bad_direction(self):
        """Test decrease_is_bad direction."""
        result = check_guardrails([
            {
                "name": "Revenue Per User",
                "metric_type": "ratio",
                "direction": "decrease_is_bad",
                "threshold_percent": 5,
                "control_data": {"total_value": 10000, "count": 100},
                "variant_data": {"total_value": 8000, "count": 100},  # 20% decrease
            },
        ])

        assert result.has_failures or result.has_warnings

    def test_increase_is_bad_direction(self):
        """Test increase_is_bad direction (default)."""
        result = check_guardrails([
            {
                "name": "Bounce Rate",
                "metric_type": "proportion",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": {"count": 500, "total": 10000},
                "variant_data": {"count": 600, "total": 10000},  # 20% increase
            },
        ])

        # Should detect the increase as bad
        assert len(result.results) == 1
        assert result.results[0].change_percent > 0

    def test_mean_metric_type(self):
        """Test mean metric type calculation."""
        result = check_guardrails([
            {
                "name": "Session Duration",
                "metric_type": "mean",
                "direction": "decrease_is_bad",
                "threshold_percent": 10,
                "control_data": [120, 150, 130, 140, 135] * 50,
                "variant_data": [125, 145, 135, 142, 138] * 50,
            },
        ])

        assert isinstance(result.results[0], GuardrailResult)
        assert isinstance(result.results[0].control_value, float)

    def test_proportion_metric_type(self):
        """Test proportion metric type calculation."""
        result = check_guardrails([
            {
                "name": "Click Rate",
                "metric_type": "proportion",
                "direction": "decrease_is_bad",
                "threshold_percent": 10,
                "control_data": {"count": 500, "total": 10000},
                "variant_data": {"count": 480, "total": 10000},
            },
        ])

        assert isinstance(result.results[0], GuardrailResult)
        assert 0 <= result.results[0].control_value <= 1

    def test_ratio_metric_type(self):
        """Test ratio metric type calculation."""
        result = check_guardrails([
            {
                "name": "Revenue Per Session",
                "metric_type": "ratio",
                "direction": "decrease_is_bad",
                "threshold_percent": 5,
                "control_data": {"total_value": 50000, "count": 1000},
                "variant_data": {"total_value": 49000, "count": 1000},
            },
        ])

        assert isinstance(result.results[0], GuardrailResult)

    def test_custom_alpha(self):
        """Test custom significance level."""
        result = check_guardrails(
            [
                {
                    "name": "Error Rate",
                    "metric_type": "proportion",
                    "direction": "increase_is_bad",
                    "threshold_percent": 10,
                    "control_data": {"count": 100, "total": 10000},
                    "variant_data": {"count": 105, "total": 10000},
                },
            ],
            alpha=0.01,
        )

        assert isinstance(result.results[0].p_value, float)

    def test_multiple_guardrails(self):
        """Test multiple guardrails together."""
        result = check_guardrails([
            {
                "name": "Page Load Time",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": [100] * 100,
                "variant_data": [105] * 100,
            },
            {
                "name": "Error Rate",
                "metric_type": "proportion",
                "direction": "increase_is_bad",
                "threshold_percent": 20,
                "control_data": {"count": 50, "total": 10000},
                "variant_data": {"count": 55, "total": 10000},
            },
            {
                "name": "Revenue",
                "metric_type": "mean",
                "direction": "decrease_is_bad",
                "threshold_percent": 5,
                "control_data": [50, 60, 55, 45, 50] * 100,
                "variant_data": [52, 58, 54, 47, 51] * 100,
            },
        ])

        assert len(result.results) == 3
        assert len(result.passed) + len(result.warnings) + len(result.failures) == 3

    def test_empty_guardrails(self):
        """Test empty guardrails list."""
        result = check_guardrails([])

        assert result.all_passed is True
        assert result.can_ship is True

    def test_recommendation_generated(self):
        """Test that recommendation is generated."""
        result = check_guardrails([
            {
                "name": "Page Load Time",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": [100] * 100,
                "variant_data": [105] * 100,
            },
        ])

        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_interpretation_generated(self):
        """Test that interpretation is generated for each result."""
        result = check_guardrails([
            {
                "name": "Test Metric",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": [100] * 100,
                "variant_data": [105] * 100,
            },
        ])

        assert isinstance(result.results[0].interpretation, str)


class TestBusinessIntegration:
    """Integration tests for business module."""

    def test_impact_and_guardrails_workflow(self):
        """Test using impact projection with guardrails."""
        # Check guardrails first
        guardrails = check_guardrails([
            {
                "name": "Page Load",
                "metric_type": "mean",
                "direction": "increase_is_bad",
                "threshold_percent": 10,
                "control_data": [100] * 200,
                "variant_data": [102] * 200,
            },
        ])

        # If guardrails pass, project impact
        if guardrails.can_ship:
            impact = project_impact(
                control_rate=0.05,
                variant_rate=0.06,
                lift_percent=20.0,
                lift_ci_lower=10.0,
                lift_ci_upper=30.0,
                monthly_visitors=100000,
                revenue_per_conversion=50.0,
            )

            assert impact.annual_revenue_lift > 0

        assert guardrails.can_ship is True
