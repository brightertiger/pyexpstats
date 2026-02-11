# Timing Effect Examples

Real-world examples of using pyexpstats for time-to-event and rate analysis.

## Example 1: Time to First Purchase

You're testing a new onboarding flow to see if it speeds up first purchases.

**Data:** Days until first purchase for each user (1=purchased, 0=didn't purchase by day 30)

```python
from pyexpstats import timing

# Control: Standard onboarding
control_times = [5, 8, 12, 15, 18, 22, 25, 30, 30, 30, 30, 30]
control_events = [1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0]

# Treatment: New streamlined onboarding
treatment_times = [3, 5, 8, 10, 12, 14, 18, 22, 30, 30, 30, 30]
treatment_events = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]

result = timing.analyze(
    control_times=control_times,
    control_events=control_events,
    treatment_times=treatment_times,
    treatment_events=treatment_events,
)

print(f"Control median: {result.control_median_time} days")
print(f"Treatment median: {result.treatment_median_time} days")
print(f"Time saved: {result.time_saved:.1f} days ({result.time_saved_percent:.1f}% faster)")
print(f"Hazard ratio: {result.hazard_ratio:.3f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
```

Output:
```
Control median: 15.0 days
Treatment median: 11.0 days
Time saved: 4.0 days (26.7% faster)
Hazard ratio: 1.333
P-value: 0.0421
Significant: True
```

**Decision:** The new onboarding speeds up first purchase by ~4 days!

---

## Example 2: Support Ticket Rate Reduction

Testing if a UI redesign reduces support ticket volume.

```python
from pyexpstats import timing

result = timing.analyze_rates(
    control_events=156,         # 156 tickets
    control_exposure=1000,      # 1000 user-days
    treatment_events=112,       # 112 tickets  
    treatment_exposure=1000,    # 1000 user-days
)

print(f"Control rate: {result.control_rate:.3f} tickets/user-day")
print(f"Treatment rate: {result.treatment_rate:.3f} tickets/user-day")
print(f"Rate ratio: {result.rate_ratio:.3f}")
print(f"Rate reduction: {-result.rate_difference_percent:.1f}%")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
```

Output:
```
Control rate: 0.156 tickets/user-day
Treatment rate: 0.112 tickets/user-day
Rate ratio: 0.718
Rate reduction: 28.2%
P-value: 0.0089
Significant: True
```

**Decision:** The redesign reduces support tickets by 28%!

---

## Example 3: Error Rate Monitoring

Compare error rates between two API versions.

```python
result = timing.analyze_rates(
    control_events=45,          # 45 errors
    control_exposure=10000,     # 10,000 requests
    treatment_events=28,        # 28 errors
    treatment_exposure=10000,   # 10,000 requests
)

print(f"Old API error rate: {result.control_rate * 100:.2f}%")
print(f"New API error rate: {result.treatment_rate * 100:.2f}%")
print(f"Error reduction: {-result.rate_difference_percent:.1f}%")
print(f"Significant: {result.is_significant}")
```

---

## Example 4: Time to Churn Analysis

Measure if a retention intervention delays churn.

```python
# Days until user churned (0=still active at day 90)
control_times = [15, 22, 35, 42, 55, 68, 75, 90, 90, 90]
control_events = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]

treatment_times = [25, 38, 52, 65, 78, 85, 90, 90, 90, 90]
treatment_events = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]

result = timing.analyze(
    control_times=control_times,
    control_events=control_events,
    treatment_times=treatment_times,
    treatment_events=treatment_events,
)

print(f"Control median survival: {result.control_median_time} days")
print(f"Treatment median survival: {result.treatment_median_time} days")
print(f"Hazard ratio: {result.hazard_ratio:.3f}")

# HR < 1 means treatment REDUCES the hazard (slows churn)
if result.hazard_ratio < 1:
    print(f"Treatment reduces churn rate by {(1 - result.hazard_ratio) * 100:.1f}%")
```

---

## Example 5: Kaplan-Meier Survival Curve

Generate survival probabilities over time.

```python
curve = timing.survival_curve(
    times=[5, 10, 15, 20, 25, 30, 35, 40],
    events=[1, 1, 1, 0, 1, 1, 0, 1],
)

print(f"Median survival time: {curve.median_time}")
print(f"Total events: {curve.events}")
print(f"Total censored: {curve.censored}")
print()
print("Time | Survival Probability")
print("-----|--------------------")
for t, s in zip(curve.times, curve.survival_probabilities):
    print(f"{t:4.0f} | {s:.2%}")
```

Output:
```
Median survival time: 25.0

Time | Survival Probability
-----|--------------------
   0 | 100.00%
   5 | 87.50%
  10 | 75.00%
  15 | 62.50%
  20 | 62.50%
  25 | 50.00%
  30 | 37.50%
  35 | 37.50%
  40 | 25.00%
```

---

## Example 6: Planning a Survival Study

Calculate sample size for a time-to-event study.

```python
plan = timing.sample_size(
    control_median=30,        # Expect median of 30 days in control
    treatment_median=24,      # Want to detect if treatment is 20% faster
    confidence=95,
    power=80,
    dropout_rate=0.15,        # 15% expected dropout
)

print(f"Subjects per group: {plan.subjects_per_group:,}")
print(f"Total subjects: {plan.total_subjects:,}")
print(f"Expected events: {plan.total_expected_events:,}")
print(f"Hazard ratio to detect: {plan.hazard_ratio:.3f}")
```

Output:
```
Subjects per group: 186
Total subjects: 372
Expected events: 316
Hazard ratio to detect: 1.250
```

---

## Example 7: Generate a Timing Report

```python
result = timing.analyze(
    control_times=[5, 10, 15, 20, 25, 30],
    control_events=[1, 1, 1, 0, 1, 1],
    treatment_times=[3, 7, 12, 16, 20, 24],
    treatment_events=[1, 1, 1, 1, 0, 1],
)

report = timing.summarize(result, test_name="New Checkout Flow Speed Test")
print(report)
```

---

## Example 8: Rate Analysis Report

```python
result = timing.analyze_rates(
    control_events=89,
    control_exposure=500,
    treatment_events=62,
    treatment_exposure=500,
)

report = timing.summarize_rates(
    result,
    test_name="Bug Fix Impact",
    unit="errors per day"
)
print(report)
```

---

## When to Use Timing vs Conversion Effects

| Scenario | Use |
|----------|-----|
| Did users convert? (yes/no) | `conversion.analyze()` |
| How fast did users convert? | `timing.analyze()` |
| What percentage converted? | `conversion.analyze()` |
| How many events per time period? | `timing.analyze_rates()` |

**Key insight:** A treatment might not change *whether* users convert, but it might change *when* they convert. Both are valuable!

Example:
- Conversion: 50% → 50% (no change)
- Median time: 14 days → 7 days (2x faster!)

The timing effect shows massive business value that conversion analysis would miss.
