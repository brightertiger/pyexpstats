# Quick Start

This guide will get you running your first A/B test analysis in under 5 minutes.

## Choose Your Module

pyexpstats has three main modules:

| Module | Use When |
|--------|----------|
| `conversion` | Your metric is a rate (clicks, signups, purchases) |
| `magnitude` | Your metric is a number (revenue, time, score) |
| `timing` | You care about *when* events happen (time to purchase, event rates) |

## Example 1: Conversion Rate Test

You ran an A/B test on your signup button. Here's what happened:

- **Control**: 10,000 visitors, 500 signups (5.0%)
- **Variant**: 10,000 visitors, 600 signups (6.0%)

```python
from pyexpstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)

print(f"Winner: {result.winner}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Significant: {result.is_significant}")
```

Output:
```
Winner: variant
Lift: +20.0%
Significant: True
```

## Example 2: Revenue Test

You tested a new checkout flow. Here's what happened:

- **Control**: 5,000 orders, $50 average, $25 std dev
- **Variant**: 5,000 orders, $52.50 average, $25 std dev

```python
from pyexpstats import magnitude

result = magnitude.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)

print(f"Winner: {result.winner}")
print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"Significant: {result.is_significant}")
```

## Example 3: Time-to-Event Analysis

You want to know if a new onboarding flow speeds up first purchase:

```python
from pyexpstats import timing

# Days until first purchase (1=purchased, 0=didn't purchase by day 30)
result = timing.analyze(
    control_times=[5, 10, 15, 20, 25, 30, 30, 30],
    control_events=[1, 1, 1, 1, 0, 1, 0, 0],
    treatment_times=[3, 7, 12, 16, 20, 25, 30, 30],
    treatment_events=[1, 1, 1, 1, 1, 0, 1, 0],
)

print(f"Control median: {result.control_median_time} days")
print(f"Treatment median: {result.treatment_median_time} days")
print(f"Hazard ratio: {result.hazard_ratio:.2f}")
print(f"Significant: {result.is_significant}")
```

## Example 4: Event Rate Comparison

Compare support ticket rates between two product versions:

```python
from pyexpstats import timing

result = timing.analyze_rates(
    control_events=45,          # 45 tickets
    control_exposure=100,       # over 100 user-days
    treatment_events=32,        # 32 tickets
    treatment_exposure=100,     # over 100 user-days
)

print(f"Control rate: {result.control_rate:.2f} tickets/day")
print(f"Treatment rate: {result.treatment_rate:.2f} tickets/day")
print(f"Rate reduction: {result.rate_difference_percent:.1f}%")
print(f"Significant: {result.is_significant}")
```

## Example 5: Plan Your Test

Before running a test, calculate how many visitors you need:

```python
from pyexpstats import conversion

plan = conversion.sample_size(
    current_rate=5,      # Your current 5% conversion rate
    lift_percent=10,     # You want to detect a 10% improvement
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
print(f"Total: {plan.total_visitors:,} visitors")

# Add daily traffic to estimate duration
plan.with_daily_traffic(10000)  # 10k visitors/day
print(f"Duration: {plan.test_duration_days} days")
```

## Example 6: Multi-Variant Test

Test multiple variants at once:

```python
from pyexpstats import conversion

result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 520},
        {"name": "variant_b", "visitors": 10000, "conversions": 580},
        {"name": "variant_c", "visitors": 10000, "conversions": 610},
    ]
)

print(f"Best variant: {result.best_variant}")
print(f"Significant overall: {result.is_significant}")
print(f"P-value: {result.p_value:.4f}")
```

## Example 7: Generate a Report

Create a shareable report for stakeholders:

```python
from pyexpstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)

report = conversion.summarize(result, test_name="Signup Button Test")
print(report)
```

Output:
```markdown
## 📊 Signup Button Test Results

### ✅ Significant Result

**The test variant performed significantly higher than the control.**

- **Control conversion rate:** 5.00% (500 / 10,000)
- **Variant conversion rate:** 6.00% (600 / 10,000)
- **Relative lift:** +20.0% increase
- **P-value:** 0.0003
- **Confidence level:** 95%

### 📝 What This Means

With 95% confidence, the difference is statistically significant.
The variant shows a **20.0%** improvement over control.
```

## Use the Web Interface

For a visual, interactive experience:

```bash
pyexpstats-server
# Open http://localhost:8000
```

The web interface includes:

- **Sample Size Calculator** — With explanations for each parameter
- **A/B Test Results** — For 2-variant and multi-variant tests
- **Timing & Rates** — Survival analysis and Poisson comparisons
- **Diff-in-Diff** — Quasi-experimental analysis
- **Confidence Intervals** — Precision estimation

## Next Steps

- [Sample Size Calculator](../guide/sample-size.md) - Plan your tests properly
- [Analyzing Results](../guide/analyzing-results.md) - Deep dive into analysis
- [Multi-Variant Tests](../guide/multi-variant.md) - Test 3+ variants at once
- [Timing Effects](../api/timing.md) - Survival and rate analysis
- [API Reference](../api/conversion.md) - Full function documentation
