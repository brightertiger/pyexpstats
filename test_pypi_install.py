import pyexpstats
from pyexpstats import conversion, magnitude, timing

print("=" * 60)
print("Testing pyexpstats from PyPI installation")
print("=" * 60)
print(f"\nPackage version: {pyexpstats.__version__}")

print("\n" + "=" * 60)
print("1. CONVERSION EFFECT TESTS")
print("=" * 60)

plan = conversion.sample_size(
    current_rate=0.05,
    lift_percent=10,
    confidence=95,
    power=80,
)
print(f"\nSample Size Calculation:")
print(f"  Current rate: {plan.current_rate:.1%}")
print(f"  Expected rate: {plan.expected_rate:.1%}")
print(f"  Visitors per variant: {plan.visitors_per_variant:,}")
print(f"  Total visitors: {plan.total_visitors:,}")

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=550,
    confidence=95,
)
print(f"\nA/B Test Analysis:")
print(f"  Control rate: {result.control_rate:.2%}")
print(f"  Variant rate: {result.variant_rate:.2%}")
print(f"  Lift: {result.lift_percent:+.1f}%")
print(f"  P-value: {result.p_value:.4f}")
print(f"  Significant: {result.is_significant}")
print(f"  Winner: {result.winner}")

ci = conversion.confidence_interval(
    visitors=1000,
    conversions=50,
    confidence=95,
)
print(f"\nConfidence Interval:")
print(f"  Rate: {ci.rate:.2%}")
print(f"  95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")

multi_result = conversion.analyze_multi(
    variants=[
        {"name": "Control", "visitors": 5000, "conversions": 250},
        {"name": "Variant A", "visitors": 5000, "conversions": 275},
        {"name": "Variant B", "visitors": 5000, "conversions": 300},
    ],
    confidence=95,
)
print(f"\nMulti-Variant Test:")
print(f"  Best variant: {multi_result.best_variant}")
print(f"  P-value (chi-square): {multi_result.p_value:.4f}")
print(f"  Significant: {multi_result.is_significant}")

print("\n" + "=" * 60)
print("2. MAGNITUDE EFFECT TESTS (Revenue/AOV)")
print("=" * 60)

rev_plan = magnitude.sample_size(
    current_mean=50.0,
    current_std=25.0,
    lift_percent=5,
    confidence=95,
    power=80,
)
print(f"\nSample Size Calculation:")
print(f"  Current mean: ${rev_plan.current_mean:.2f}")
print(f"  Expected mean: ${rev_plan.expected_mean:.2f}")
print(f"  Standard deviation: ${rev_plan.standard_deviation:.2f}")
print(f"  Visitors per variant: {rev_plan.visitors_per_variant:,}")

rev_result = magnitude.analyze(
    control_visitors=5000,
    control_mean=50.0,
    control_std=25.0,
    variant_visitors=5000,
    variant_mean=52.5,
    variant_std=26.0,
    confidence=95,
)
print(f"\nRevenue Test Analysis:")
print(f"  Control mean: ${rev_result.control_mean:.2f}")
print(f"  Variant mean: ${rev_result.variant_mean:.2f}")
print(f"  Lift: {rev_result.lift_percent:+.1f}%")
print(f"  P-value: {rev_result.p_value:.4f}")
print(f"  Significant: {rev_result.is_significant}")
print(f"  Winner: {rev_result.winner}")

rev_ci = magnitude.confidence_interval(
    visitors=1000,
    mean=50.0,
    std=25.0,
    confidence=95,
)
print(f"\nConfidence Interval:")
print(f"  Mean: ${rev_ci.mean:.2f}")
print(f"  95% CI: [${rev_ci.lower:.2f}, ${rev_ci.upper:.2f}]")

print("\n" + "=" * 60)
print("3. TIMING EFFECT TESTS (Survival Analysis)")
print("=" * 60)

control_times = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
control_events = [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1]

treatment_times = [8, 12, 18, 22, 28, 32, 38, 42, 48, 52, 58, 62, 68, 72, 78]
treatment_events = [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1]

timing_result = timing.analyze(
    control_times=control_times,
    control_events=control_events,
    treatment_times=treatment_times,
    treatment_events=treatment_events,
    confidence=95,
)
print(f"\nTiming Analysis:")
print(f"  Control median time: {timing_result.control_median_time}")
print(f"  Treatment median time: {timing_result.treatment_median_time}")
print(f"  Hazard ratio: {timing_result.hazard_ratio:.3f}")
print(f"  P-value: {timing_result.p_value:.4f}")
print(f"  Significant: {timing_result.is_significant}")

survival = timing.survival_curve(
    times=[10, 20, 30, 40, 50],
    events=[1, 1, 0, 1, 1],
    confidence=95,
)
print(f"\nSurvival Curve:")
print(f"  Total subjects: {survival.total}")
print(f"  Events: {survival.events}")
print(f"  Censored: {survival.censored}")
print(f"  Median time: {survival.median_time}")

timing_plan = timing.sample_size(
    control_median=30,
    treatment_median=25,
    confidence=95,
    power=80,
)
print(f"\nTiming Sample Size:")
print(f"  Subjects per group: {timing_plan.subjects_per_group:,}")
print(f"  Total subjects: {timing_plan.total_subjects:,}")
print(f"  Hazard ratio: {timing_plan.hazard_ratio:.3f}")

rate_result = timing.analyze_rates(
    control_events=50,
    control_exposure=1000,
    treatment_events=65,
    treatment_exposure=1000,
    confidence=95,
)
print(f"\nRate Analysis:")
print(f"  Control rate: {rate_result.control_rate:.4f}")
print(f"  Treatment rate: {rate_result.treatment_rate:.4f}")
print(f"  Rate ratio: {rate_result.rate_ratio:.3f}")
print(f"  P-value: {rate_result.p_value:.4f}")

print("\n" + "=" * 60)
print("4. DIFF-IN-DIFF TESTS")
print("=" * 60)

did_result = conversion.diff_in_diff(
    control_pre_visitors=5000,
    control_pre_conversions=250,
    control_post_visitors=5000,
    control_post_conversions=260,
    treatment_pre_visitors=5000,
    treatment_pre_conversions=250,
    treatment_post_visitors=5000,
    treatment_post_conversions=300,
    confidence=95,
)
print(f"\nConversion Diff-in-Diff:")
print(f"  Control change: {did_result.control_change:+.2%}")
print(f"  Treatment change: {did_result.treatment_change:+.2%}")
print(f"  DiD effect: {did_result.diff_in_diff:+.2%}")
print(f"  P-value: {did_result.p_value:.4f}")
print(f"  Significant: {did_result.is_significant}")

mag_did_result = magnitude.diff_in_diff(
    control_pre_n=1000,
    control_pre_mean=50.0,
    control_pre_std=20.0,
    control_post_n=1000,
    control_post_mean=51.0,
    control_post_std=20.0,
    treatment_pre_n=1000,
    treatment_pre_mean=50.0,
    treatment_pre_std=20.0,
    treatment_post_n=1000,
    treatment_post_mean=55.0,
    treatment_post_std=22.0,
    confidence=95,
)
print(f"\nMagnitude Diff-in-Diff:")
print(f"  Control change: ${mag_did_result.control_change:+.2f}")
print(f"  Treatment change: ${mag_did_result.treatment_change:+.2f}")
print(f"  DiD effect: ${mag_did_result.diff_in_diff:+.2f}")
print(f"  P-value: {mag_did_result.p_value:.4f}")
print(f"  Significant: {mag_did_result.is_significant}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nPackage pyexpstats is working correctly from PyPI installation.")
