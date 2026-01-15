import pytest
from pyexptest import numeric_effect


class TestNumericSampleSize:
    def test_basic_calculation(self):
        plan = numeric_effect.sample_size(
            current_mean=50,
            current_std=25,
            lift_percent=5,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > 0
        assert plan.total_visitors == plan.visitors_per_variant * 2
        assert plan.expected_mean == pytest.approx(52.5)

    def test_higher_lift_needs_fewer_visitors(self):
        plan_small = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5)
        plan_large = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=10)
        assert plan_large.visitors_per_variant < plan_small.visitors_per_variant

    def test_higher_variance_needs_more_visitors(self):
        plan_low = numeric_effect.sample_size(current_mean=50, current_std=10, lift_percent=5)
        plan_high = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5)
        assert plan_high.visitors_per_variant > plan_low.visitors_per_variant

    def test_duration_estimation(self):
        plan = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5)
        plan.with_daily_traffic(1000)
        assert plan.test_duration_days is not None
        assert plan.test_duration_days > 0

    def test_invalid_std(self):
        with pytest.raises(ValueError):
            numeric_effect.sample_size(current_mean=50, current_std=-10, lift_percent=5)


class TestNumericAnalyze:
    def test_significant_result(self):
        result = numeric_effect.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        assert result.is_significant == True
        assert result.winner == "variant"
        assert result.lift_percent == pytest.approx(10, rel=0.1)

    def test_non_significant_result(self):
        result = numeric_effect.analyze(
            control_visitors=50,
            control_mean=50,
            control_std=25,
            variant_visitors=50,
            variant_mean=51,
            variant_std=25,
        )
        assert result.is_significant == False
        assert result.winner == "no winner yet"

    def test_confidence_interval(self):
        result = numeric_effect.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=52,
            variant_std=15,
        )
        assert result.confidence_interval_lower < result.confidence_interval_upper

    def test_recommendation_includes_pvalue(self):
        result = numeric_effect.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        assert "p-value" in result.recommendation.lower()
        assert "higher" in result.recommendation.lower() or "lower" in result.recommendation.lower()


class TestNumericConfidenceInterval:
    def test_basic_calculation(self):
        ci = numeric_effect.confidence_interval(visitors=100, mean=50, std=15)
        assert ci.mean == 50
        assert ci.lower < 50 < ci.upper

    def test_higher_confidence_wider_interval(self):
        ci_95 = numeric_effect.confidence_interval(visitors=100, mean=50, std=15, confidence=95)
        ci_99 = numeric_effect.confidence_interval(visitors=100, mean=50, std=15, confidence=99)
        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower
        assert width_99 > width_95


class TestNumericSummarize:
    def test_summary_is_markdown(self):
        result = numeric_effect.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=52,
            variant_std=15,
        )
        summary = numeric_effect.summarize(result)
        assert "##" in summary
        assert "**" in summary

    def test_summary_includes_pvalue_interpretation(self):
        result = numeric_effect.analyze(
            control_visitors=500,
            control_mean=50,
            control_std=15,
            variant_visitors=500,
            variant_mean=55,
            variant_std=15,
        )
        summary = numeric_effect.summarize(result)
        assert "p-value" in summary.lower()
        assert "chance" in summary.lower()

    def test_plan_summary_generation(self):
        plan = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5)
        summary = numeric_effect.summarize_plan(plan)
        assert "visitors" in summary.lower()
        assert "##" in summary


class TestNumericMultiVariant:
    def test_three_variant_analysis(self):
        result = numeric_effect.analyze_multi(
            variants=[
                {"name": "control", "visitors": 500, "mean": 50, "std": 15},
                {"name": "variant_a", "visitors": 500, "mean": 52, "std": 15},
                {"name": "variant_b", "visitors": 500, "mean": 55, "std": 15},
            ]
        )
        assert result.best_variant == "variant_b"
        assert result.worst_variant == "control"
        assert len(result.pairwise_comparisons) == 3

    def test_significant_multi_variant(self):
        result = numeric_effect.analyze_multi(
            variants=[
                {"name": "control", "visitors": 500, "mean": 50, "std": 15},
                {"name": "variant_a", "visitors": 500, "mean": 50, "std": 15},
                {"name": "variant_b", "visitors": 500, "mean": 60, "std": 15},
            ]
        )
        assert result.is_significant == True
        assert result.best_variant == "variant_b"

    def test_non_significant_multi_variant(self):
        result = numeric_effect.analyze_multi(
            variants=[
                {"name": "control", "visitors": 50, "mean": 50, "std": 25},
                {"name": "variant_a", "visitors": 50, "mean": 50.5, "std": 25},
                {"name": "variant_b", "visitors": 50, "mean": 51, "std": 25},
            ]
        )
        assert result.is_significant == False

    def test_pairwise_bonferroni_correction(self):
        result = numeric_effect.analyze_multi(
            variants=[
                {"name": "control", "visitors": 500, "mean": 50, "std": 15},
                {"name": "variant_a", "visitors": 500, "mean": 52, "std": 15},
                {"name": "variant_b", "visitors": 500, "mean": 55, "std": 15},
            ],
            correction="bonferroni",
        )
        for p in result.pairwise_comparisons:
            assert p.p_value_adjusted >= p.p_value

    def test_multi_summary_generation(self):
        result = numeric_effect.analyze_multi(
            variants=[
                {"name": "control", "visitors": 500, "mean": 50, "std": 15},
                {"name": "variant_a", "visitors": 500, "mean": 55, "std": 15},
            ]
        )
        summary = numeric_effect.summarize_multi(result)
        assert "control" in summary
        assert "variant_a" in summary
        assert "##" in summary
        assert "ANOVA" in summary

    def test_sample_size_multi_variant(self):
        plan_2 = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5, num_variants=2)
        plan_3 = numeric_effect.sample_size(current_mean=50, current_std=25, lift_percent=5, num_variants=3)
        assert plan_3.visitors_per_variant > plan_2.visitors_per_variant
        assert plan_3.total_visitors == plan_3.visitors_per_variant * 3