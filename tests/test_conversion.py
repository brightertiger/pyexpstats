import pytest
from pyexpstats import conversion


class TestConversionSampleSize:
    def test_basic_calculation(self):
        plan = conversion.sample_size(
            current_rate=0.05,
            lift_percent=10,
            confidence=95,
            power=80,
        )
        assert plan.visitors_per_variant > 0
        assert plan.total_visitors == plan.visitors_per_variant * 2
        assert plan.expected_rate == pytest.approx(0.055)

    def test_accepts_percentage_input(self):
        plan = conversion.sample_size(current_rate=5, lift_percent=10)
        assert plan.current_rate == 0.05
        assert plan.expected_rate == pytest.approx(0.055)

    def test_higher_lift_needs_fewer_visitors(self):
        plan_small = conversion.sample_size(current_rate=0.05, lift_percent=5)
        plan_large = conversion.sample_size(current_rate=0.05, lift_percent=20)
        assert plan_large.visitors_per_variant < plan_small.visitors_per_variant

    def test_higher_confidence_needs_more_visitors(self):
        plan_95 = conversion.sample_size(current_rate=0.05, lift_percent=10, confidence=95)
        plan_99 = conversion.sample_size(current_rate=0.05, lift_percent=10, confidence=99)
        assert plan_99.visitors_per_variant > plan_95.visitors_per_variant

    def test_duration_estimation(self):
        plan = conversion.sample_size(current_rate=0.05, lift_percent=10)
        plan.with_daily_traffic(1000)
        assert plan.test_duration_days is not None
        assert plan.test_duration_days > 0

    def test_invalid_rate(self):
        with pytest.raises(ValueError):
            conversion.sample_size(current_rate=-0.1, lift_percent=10)
        with pytest.raises(ValueError):
            conversion.sample_size(current_rate=101, lift_percent=10)


class TestConversionAnalyze:
    def test_significant_result(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )
        assert result.is_significant == True
        assert result.winner == "variant"
        assert result.lift_percent == pytest.approx(20, rel=0.01)

    def test_non_significant_result(self):
        result = conversion.analyze(
            control_visitors=1000,
            control_conversions=50,
            variant_visitors=1000,
            variant_conversions=52,
        )
        assert result.is_significant == False
        assert result.winner == "no winner yet"

    def test_negative_lift(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=600,
            variant_visitors=10000,
            variant_conversions=500,
        )
        assert result.lift_percent < 0
        if result.is_significant:
            assert result.winner == "control"

    def test_confidence_interval(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=550,
        )
        assert result.confidence_interval_lower < result.confidence_interval_upper
        assert result.confidence_interval_lower < result.lift_absolute < result.confidence_interval_upper

    def test_recommendation_includes_pvalue(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )
        assert "p-value" in result.recommendation.lower()
        assert "higher" in result.recommendation.lower() or "lower" in result.recommendation.lower()


class TestConversionConfidenceInterval:
    def test_basic_calculation(self):
        ci = conversion.confidence_interval(visitors=1000, conversions=50)
        assert ci.rate == 0.05
        assert ci.lower < 0.05 < ci.upper

    def test_higher_confidence_wider_interval(self):
        ci_95 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=95)
        ci_99 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=99)
        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower
        assert width_99 > width_95

    def test_bounds_within_0_1(self):
        ci = conversion.confidence_interval(visitors=100, conversions=5)
        assert ci.lower >= 0
        assert ci.upper <= 1


class TestConversionSummarize:
    def test_summary_is_markdown(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=550,
        )
        summary = conversion.summarize(result)
        assert "##" in summary
        assert "**" in summary

    def test_summary_includes_pvalue_interpretation(self):
        result = conversion.analyze(
            control_visitors=10000,
            control_conversions=500,
            variant_visitors=10000,
            variant_conversions=600,
        )
        summary = conversion.summarize(result)
        assert "p-value" in summary.lower()
        assert "chance" in summary.lower()

    def test_plan_summary_generation(self):
        plan = conversion.sample_size(current_rate=0.05, lift_percent=10)
        summary = conversion.summarize_plan(plan)
        assert "visitors" in summary.lower()
        assert "##" in summary


class TestConversionMultiVariant:
    def test_three_variant_analysis(self):
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 10000, "conversions": 500},
                {"name": "variant_a", "visitors": 10000, "conversions": 550},
                {"name": "variant_b", "visitors": 10000, "conversions": 600},
            ]
        )
        assert result.best_variant == "variant_b"
        assert result.worst_variant == "control"
        assert len(result.pairwise_comparisons) == 3

    def test_significant_multi_variant(self):
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 10000, "conversions": 500},
                {"name": "variant_a", "visitors": 10000, "conversions": 500},
                {"name": "variant_b", "visitors": 10000, "conversions": 700},
            ]
        )
        assert result.is_significant == True
        assert result.best_variant == "variant_b"

    def test_non_significant_multi_variant(self):
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 1000, "conversions": 50},
                {"name": "variant_a", "visitors": 1000, "conversions": 51},
                {"name": "variant_b", "visitors": 1000, "conversions": 52},
            ]
        )
        assert result.is_significant == False

    def test_pairwise_bonferroni_correction(self):
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 10000, "conversions": 500},
                {"name": "variant_a", "visitors": 10000, "conversions": 550},
                {"name": "variant_b", "visitors": 10000, "conversions": 600},
            ],
            correction="bonferroni",
        )
        for p in result.pairwise_comparisons:
            assert p.p_value_adjusted >= p.p_value

    def test_multi_summary_generation(self):
        result = conversion.analyze_multi(
            variants=[
                {"name": "control", "visitors": 10000, "conversions": 500},
                {"name": "variant_a", "visitors": 10000, "conversions": 600},
            ]
        )
        summary = conversion.summarize_multi(result)
        assert "control" in summary
        assert "variant_a" in summary
        assert "##" in summary

    def test_sample_size_multi_variant(self):
        plan_2 = conversion.sample_size(current_rate=0.05, lift_percent=10, num_variants=2)
        plan_3 = conversion.sample_size(current_rate=0.05, lift_percent=10, num_variants=3)
        assert plan_3.visitors_per_variant > plan_2.visitors_per_variant
        assert plan_3.total_visitors == plan_3.visitors_per_variant * 3
