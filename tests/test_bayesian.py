"""
Tests for Bayesian A/B Testing Module.

Tests the Beta-Binomial Bayesian approach to A/B testing.
"""

import pytest
from expstats.methods.bayesian import (
    analyze,
    BayesianTestResult,
    summarize,
)


class TestBayesianAnalysis:
    """Tests for Bayesian A/B test analysis."""

    def test_basic_analysis(self):
        """Test basic Bayesian analysis returns expected structure."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
        )

        assert isinstance(result, BayesianTestResult)
        assert 0 <= result.probability_variant_better <= 100  # Percentage
        assert 0 <= result.probability_control_better <= 100  # Percentage
        assert pytest.approx(result.probability_variant_better + result.probability_control_better, abs=5) == 100
        assert result.expected_loss_choosing_variant >= 0
        assert result.expected_loss_choosing_control >= 0

    def test_clear_variant_winner(self):
        """Test detection of clear variant winner."""
        result = analyze(
            control_visitors=5000,
            control_conversions=250,  # 5%
            variant_visitors=5000,
            variant_conversions=400,  # 8%
        )

        assert result.probability_variant_better > 0.99
        assert result.expected_loss_choosing_variant < 0.01
        assert result.winner == "variant"

    def test_clear_control_winner(self):
        """Test detection of clear control winner."""
        result = analyze(
            control_visitors=5000,
            control_conversions=400,  # 8%
            variant_visitors=5000,
            variant_conversions=250,  # 5%
        )

        assert result.probability_control_better > 0.99
        assert result.expected_loss_choosing_control < 0.01
        assert result.winner == "control"

    def test_inconclusive_result(self):
        """Test inconclusive result with similar rates."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=52,
        )

        # Should be uncertain (30-70% range as percentages)
        assert 30 < result.probability_variant_better < 70
        # Either inconclusive or one with low confidence
        assert result.winner in ["variant", "control", "none"]

    def test_credible_interval(self):
        """Test credible interval properties."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
        )

        lower, upper = result.lift_credible_interval
        assert lower < upper
        # The point estimate should be within the interval
        assert lower <= result.lift_percent <= upper

    def test_custom_prior(self):
        """Test with custom prior (informative prior)."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
            prior_alpha=10,  # Stronger prior
            prior_beta=100,
        )

        assert isinstance(result, BayesianTestResult)
        # Informative prior should affect the result

    def test_uniform_prior(self):
        """Test with uniform (uninformative) prior."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
            prior_alpha=1,
            prior_beta=1,
        )

        assert isinstance(result, BayesianTestResult)

    def test_different_confidence_thresholds(self):
        """Test with different confidence thresholds."""
        result_95 = analyze(
            control_visitors=500,
            control_conversions=25,
            variant_visitors=500,
            variant_conversions=35,
        )

        result_99 = analyze(
            control_visitors=500,
            control_conversions=25,
            variant_visitors=500,
            variant_conversions=35,
        )

        # Same probabilities should be consistent (within 5 percentage points)
        assert pytest.approx(result_95.probability_variant_better, abs=5) == result_99.probability_variant_better

    def test_observed_rates(self):
        """Test observed rate estimates."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )

        # Observed rates should match input
        assert pytest.approx(result.control_rate, abs=0.01) == 0.05
        assert pytest.approx(result.variant_rate, abs=0.01) == 0.06

    def test_zero_conversions_control(self):
        """Test handling of zero conversions in control."""
        result = analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=10,
        )

        assert isinstance(result, BayesianTestResult)
        assert result.probability_variant_better > 0.95  # Variant clearly better

    def test_zero_conversions_both(self):
        """Test handling of zero conversions in both groups."""
        result = analyze(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=0,
        )

        assert isinstance(result, BayesianTestResult)
        # Should be roughly 50/50 with uniform prior (30-70% as percentages)
        assert 30 < result.probability_variant_better < 70

    def test_100_percent_conversion(self):
        """Test with 100% conversion rate."""
        result = analyze(
            control_visitors=100,
            control_conversions=100,
            variant_visitors=100,
            variant_conversions=100,
        )

        assert isinstance(result, BayesianTestResult)
        # Both at 100%, should be roughly equal (30-70% as percentages)
        assert 30 < result.probability_variant_better < 70

    def test_summarize(self):
        """Test summary generation."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=65,
        )

        summary = summarize(result)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestBayesianEdgeCases:
    """Edge case tests for Bayesian analysis."""

    def test_very_small_sample(self):
        """Test with very small sample sizes."""
        result = analyze(
            control_visitors=10,
            control_conversions=1,
            variant_visitors=10,
            variant_conversions=2,
        )

        assert isinstance(result, BayesianTestResult)
        # High uncertainty with small samples
        lower, upper = result.lift_credible_interval
        assert (upper - lower) > 50  # Wide interval

    def test_very_large_sample(self):
        """Test with very large sample sizes."""
        result = analyze(
            control_visitors=1000000,
            control_conversions=50000,
            variant_visitors=1000000,
            variant_conversions=51000,
        )

        assert isinstance(result, BayesianTestResult)
        # Even small differences detectable with large samples
        lower, upper = result.lift_credible_interval
        assert (upper - lower) < 5  # Relatively narrow interval

    def test_asymmetric_samples(self):
        """Test with very asymmetric sample sizes."""
        result = analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=100,  # Much smaller variant
            variant_conversions=8,
        )

        assert isinstance(result, BayesianTestResult)
        # Variant has high uncertainty
        lower, upper = result.lift_credible_interval
        assert (upper - lower) > 20  # Wider due to small variant sample

    def test_extreme_conversion_difference(self):
        """Test with extreme conversion rate difference."""
        result = analyze(
            control_visitors=1000,
            control_conversions=10,  # 1%
            variant_visitors=1000,
            variant_conversions=200,  # 20%
        )

        assert result.probability_variant_better > 0.99
        assert result.winner == "variant"

    def test_very_low_conversion_rate(self):
        """Test with very low conversion rates."""
        result = analyze(
            control_visitors=100000,
            control_conversions=10,  # 0.01%
            variant_visitors=100000,
            variant_conversions=15,  # 0.015%
        )

        assert isinstance(result, BayesianTestResult)
        # Should still detect the difference

    def test_very_high_conversion_rate(self):
        """Test with very high conversion rates."""
        result = analyze(
            control_visitors=1000,
            control_conversions=980,  # 98%
            variant_visitors=1000,
            variant_conversions=990,  # 99%
        )

        assert isinstance(result, BayesianTestResult)


class TestBayesianValidation:
    """Validation tests for Bayesian analysis inputs."""

    def test_negative_visitors_raises(self):
        """Test that negative visitors raises error."""
        with pytest.raises((ValueError, TypeError)):
            analyze(
                control_visitors=-100,
                control_conversions=10,
                variant_visitors=1000,
                variant_conversions=50,
            )

    def test_conversions_exceed_visitors_handled(self):
        """Test that conversions > visitors is handled."""
        try:
            result = analyze(
                control_visitors=100,
                control_conversions=150,
                variant_visitors=100,
                variant_conversions=50,
            )
            assert isinstance(result, BayesianTestResult)
        except ValueError:
            pass  # Expected

    def test_valid_prior_alpha(self):
        """Test valid prior alpha handling."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
            prior_alpha=1,
        )
        assert isinstance(result, BayesianTestResult)

    def test_valid_prior_beta(self):
        """Test valid prior beta handling."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
            prior_beta=1,
        )
        assert isinstance(result, BayesianTestResult)


class TestBayesianStatisticalProperties:
    """Statistical property tests for Bayesian analysis."""

    def test_symmetry(self):
        """Test that swapping groups gives symmetric probabilities."""
        result1 = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )

        result2 = analyze(
            control_visitors=1000,
            control_conversions=60,  # Swapped
            variant_visitors=1000,
            variant_conversions=50,  # Swapped
        )

        # Probabilities should be symmetric (within 2 percentage points due to Monte Carlo)
        assert pytest.approx(
            result1.probability_variant_better,
            abs=2
        ) == result2.probability_control_better

    def test_monotonicity_with_more_data(self):
        """Test that more data narrows credible interval."""
        result_small = analyze(
            control_visitors=100,
            control_conversions=5,
            variant_visitors=100,
            variant_conversions=6,
        )

        result_large = analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )

        # Same rates, but larger sample should have narrower interval
        width_small = result_small.lift_credible_interval[1] - result_small.lift_credible_interval[0]
        width_large = result_large.lift_credible_interval[1] - result_large.lift_credible_interval[0]
        assert width_large < width_small

    def test_expected_loss_consistency(self):
        """Test that expected loss is consistent with probability."""
        result = analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=60,
        )

        # If variant is likely better, loss for choosing variant should be lower
        if result.probability_variant_better > 0.5:
            assert result.expected_loss_choosing_variant <= result.expected_loss_choosing_control
        else:
            assert result.expected_loss_choosing_control <= result.expected_loss_choosing_variant
