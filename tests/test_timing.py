import pytest
import numpy as np
from pyexpstats import timing


class TestSurvivalCurve:
    def test_basic_curve(self):
        times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        events = [1, 1, 0, 1, 0, 1, 1, 0, 1, 1]
        
        curve = timing.survival_curve(times=times, events=events)
        
        assert curve.total == 10
        assert curve.events == 7
        assert curve.censored == 3
        assert curve.survival_probabilities[0] == 1.0
        assert len(curve.times) == len(curve.survival_probabilities)
    
    def test_all_events(self):
        times = [1, 2, 3, 4, 5]
        events = [1, 1, 1, 1, 1]
        
        curve = timing.survival_curve(times=times, events=events)
        
        assert curve.events == 5
        assert curve.censored == 0
        assert curve.survival_probabilities[-1] == 0.0
    
    def test_all_censored(self):
        times = [1, 2, 3, 4, 5]
        events = [0, 0, 0, 0, 0]
        
        curve = timing.survival_curve(times=times, events=events)
        
        assert curve.events == 0
        assert curve.censored == 5
        assert all(s == 1.0 for s in curve.survival_probabilities)
    
    def test_median_calculation(self):
        times = list(range(1, 21))
        events = [1] * 20
        
        curve = timing.survival_curve(times=times, events=events)
        
        assert curve.median_time is not None
        assert 9 <= curve.median_time <= 11
    
    def test_confidence_intervals(self):
        times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        events = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        
        curve = timing.survival_curve(times=times, events=events)
        
        for i in range(len(curve.times)):
            assert curve.confidence_lower[i] <= curve.survival_probabilities[i]
            assert curve.survival_probabilities[i] <= curve.confidence_upper[i]
    
    def test_invalid_events(self):
        with pytest.raises(ValueError):
            timing.survival_curve(times=[1, 2, 3], events=[1, 2, 3])
    
    def test_empty_times(self):
        with pytest.raises(ValueError):
            timing.survival_curve(times=[], events=[])
    
    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            timing.survival_curve(times=[1, 2, 3], events=[1, 1])


class TestTimingAnalyze:
    def test_significant_difference(self):
        np.random.seed(42)
        control_times = np.random.exponential(20, 100).tolist()
        control_events = [1] * 100
        treatment_times = np.random.exponential(10, 100).tolist()
        treatment_events = [1] * 100
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        assert result.control_events == 100
        assert result.treatment_events == 100
        assert result.hazard_ratio != 1.0
        assert result.p_value < 0.05
        assert result.is_significant == True
    
    def test_non_significant_difference(self):
        np.random.seed(42)
        control_times = np.random.exponential(10, 30).tolist()
        control_events = [1] * 30
        treatment_times = np.random.exponential(10, 30).tolist()
        treatment_events = [1] * 30
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        assert result.p_value > 0.05 or result.is_significant is False
    
    def test_hazard_ratio_bounds(self):
        control_times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        control_events = [1] * 10
        treatment_times = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        treatment_events = [1] * 10
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        assert result.hazard_ratio > 0
        assert result.hazard_ratio_ci_lower < result.hazard_ratio
        assert result.hazard_ratio < result.hazard_ratio_ci_upper
    
    def test_time_saved_calculation(self):
        control_times = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        control_events = [1] * 10
        treatment_times = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        treatment_events = [1] * 10
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        if result.control_median_time and result.treatment_median_time:
            assert result.time_saved > 0
    
    def test_recommendation_includes_hazard_ratio(self):
        control_times = [1, 2, 3, 4, 5]
        control_events = [1] * 5
        treatment_times = [2, 4, 6, 8, 10]
        treatment_events = [1] * 5
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        assert "Hazard ratio" in result.recommendation or "hazard" in result.recommendation.lower()


class TestTimingSampleSize:
    def test_basic_calculation(self):
        plan = timing.sample_size(
            control_median=30,
            treatment_median=20,
            confidence=95,
            power=80,
        )
        
        assert plan.subjects_per_group > 0
        assert plan.total_subjects == plan.subjects_per_group * 2
        assert plan.hazard_ratio == 30 / 20
    
    def test_larger_effect_needs_fewer_subjects(self):
        plan_small = timing.sample_size(control_median=30, treatment_median=28)
        plan_large = timing.sample_size(control_median=30, treatment_median=15)
        
        assert plan_large.subjects_per_group < plan_small.subjects_per_group
    
    def test_higher_power_needs_more_subjects(self):
        plan_80 = timing.sample_size(control_median=30, treatment_median=20, power=80)
        plan_90 = timing.sample_size(control_median=30, treatment_median=20, power=90)
        
        assert plan_90.subjects_per_group > plan_80.subjects_per_group
    
    def test_dropout_increases_sample_size(self):
        plan_no_dropout = timing.sample_size(control_median=30, treatment_median=20, dropout_rate=0)
        plan_dropout = timing.sample_size(control_median=30, treatment_median=20, dropout_rate=0.2)
        
        assert plan_dropout.subjects_per_group >= plan_no_dropout.subjects_per_group
    
    def test_invalid_median(self):
        with pytest.raises(ValueError):
            timing.sample_size(control_median=-10, treatment_median=20)
    
    def test_same_medians_raises_error(self):
        with pytest.raises(ValueError):
            timing.sample_size(control_median=30, treatment_median=30)


class TestTimingRates:
    def test_basic_rate_comparison(self):
        result = timing.analyze_rates(
            control_events=50,
            control_exposure=1000,
            treatment_events=30,
            treatment_exposure=1000,
        )
        
        assert result.control_rate == 0.05
        assert result.treatment_rate == 0.03
        assert result.rate_ratio < 1.0
    
    def test_significant_rate_difference(self):
        result = timing.analyze_rates(
            control_events=100,
            control_exposure=1000,
            treatment_events=50,
            treatment_exposure=1000,
        )
        
        assert result.p_value < 0.05
        assert result.is_significant == True
    
    def test_non_significant_rate_difference(self):
        result = timing.analyze_rates(
            control_events=10,
            control_exposure=1000,
            treatment_events=11,
            treatment_exposure=1000,
        )
        
        assert result.p_value > 0.05
        assert result.is_significant == False
    
    def test_rate_ratio_confidence_interval(self):
        result = timing.analyze_rates(
            control_events=50,
            control_exposure=1000,
            treatment_events=30,
            treatment_exposure=1000,
        )
        
        assert result.rate_ratio_ci_lower < result.rate_ratio
        assert result.rate_ratio < result.rate_ratio_ci_upper
    
    def test_invalid_events(self):
        with pytest.raises(ValueError):
            timing.analyze_rates(
                control_events=-5,
                control_exposure=1000,
                treatment_events=30,
                treatment_exposure=1000,
            )
    
    def test_invalid_exposure(self):
        with pytest.raises(ValueError):
            timing.analyze_rates(
                control_events=50,
                control_exposure=0,
                treatment_events=30,
                treatment_exposure=1000,
            )


class TestTimingSummarize:
    def test_summary_is_markdown(self):
        np.random.seed(42)
        control_times = np.random.exponential(20, 50).tolist()
        control_events = [1] * 50
        treatment_times = np.random.exponential(10, 50).tolist()
        treatment_events = [1] * 50
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        summary = timing.summarize(result, test_name="Time to Purchase Test")
        
        assert "##" in summary
        assert "Time to Purchase Test" in summary
        assert "Hazard ratio" in summary
    
    def test_rate_summary_is_markdown(self):
        result = timing.analyze_rates(
            control_events=50,
            control_exposure=1000,
            treatment_events=30,
            treatment_exposure=1000,
        )
        
        summary = timing.summarize_rates(result, test_name="Error Rate Test", unit="errors per hour")
        
        assert "##" in summary
        assert "Error Rate Test" in summary
        assert "errors per hour" in summary
    
    def test_summary_includes_pvalue(self):
        control_times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        control_events = [1] * 10
        treatment_times = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        treatment_events = [1] * 10
        
        result = timing.analyze(
            control_times=control_times,
            control_events=control_events,
            treatment_times=treatment_times,
            treatment_events=treatment_events,
        )
        
        summary = timing.summarize(result)
        
        assert "P-value" in summary
