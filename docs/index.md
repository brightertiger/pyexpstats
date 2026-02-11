<p align="center">
  <img src="assets/logo.png" alt="pyexpstats" width="400">
</p>

<p align="center">
  <strong>Measure what changed in user behavior, not just which test to run.</strong>
</p>

---

## Outcome Effects

pyexpstats models experimental impact across three fundamental **outcome dimensions**:

| Effect Type | Question Answered | Examples |
|-------------|-------------------|----------|
| **Conversion** | *Whether* something happens | Signup, purchase, click, trial start |
| **Magnitude** | *How much* it happens | Revenue, time spent, order value |
| **Timing** | *When* it happens | Time to purchase, time to churn |

This framework ensures experiments are interpreted in terms of **behavioral change**, not just statistical tests.

## Installation

```bash
pip install pyexpstats
```

## Quick Start

```python
from pyexpstats import conversion, magnitude, timing

# Conversion: Did the treatment change whether users purchase?
result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)
print(f"Conversion lift: {result.lift_percent:+.1f}%")

# Magnitude: Did the treatment change how much users spend?
result = magnitude.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)
print(f"Revenue lift: ${result.lift_absolute:+.2f}")

# Timing: Did the treatment change when users convert?
result = timing.analyze(
    control_times=[5, 8, 12, 15, 20],
    control_events=[1, 1, 1, 0, 1],
    treatment_times=[3, 6, 9, 12, 16],
    treatment_events=[1, 1, 1, 1, 1],
)
print(f"Hazard ratio: {result.hazard_ratio:.2f}")
```

Or use the fully-qualified path:

```python
from pyexpstats.effects.outcome import conversion, magnitude, timing
```

---

## 📊 Conversion Effects — *Whether* it happens

Use when your outcome is binary: did the user convert or not?

### Analyze a Test

```python
from pyexpstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,      # 5.0% conversion
    variant_visitors=10000,
    variant_conversions=600,      # 6.0% conversion
)

print(f"Control: {result.control_rate:.2%}")
print(f"Variant: {result.variant_rate:.2%}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Significant: {result.is_significant}")
print(f"Winner: {result.winner}")
```

### Calculate Sample Size

```python
plan = conversion.sample_size(
    current_rate=5,       # 5% baseline
    lift_percent=10,      # detect 10% relative lift
    confidence=95,
    power=80,
)

print(f"Need {plan.visitors_per_variant:,} per variant")
plan.with_daily_traffic(10000)
print(f"Duration: {plan.test_duration_days} days")
```

### Multi-Variant Tests (Chi-Square)

```python
result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 550},
        {"name": "variant_b", "visitors": 10000, "conversions": 600},
    ]
)

print(f"Best: {result.best_variant}")
print(f"P-value: {result.p_value:.4f}")
```

### Difference-in-Differences

```python
result = conversion.diff_in_diff(
    control_pre_visitors=5000, control_pre_conversions=250,
    control_post_visitors=5000, control_post_conversions=275,
    treatment_pre_visitors=5000, treatment_pre_conversions=250,
    treatment_post_visitors=5000, treatment_post_conversions=350,
)

print(f"DiD effect: {result.diff_in_diff:+.2%}")
```

---

## 📈 Magnitude Effects — *How much* it happens

Use when your outcome is a continuous value: revenue, time, count.

### Analyze a Test

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

print(f"Control: ${result.control_mean:.2f}")
print(f"Variant: ${result.variant_mean:.2f}")
print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"Significant: {result.is_significant}")
```

### Calculate Sample Size

```python
plan = magnitude.sample_size(
    current_mean=50,      # $50 average
    current_std=25,       # $25 std dev
    lift_percent=5,       # detect 5% lift
)

print(f"Need {plan.visitors_per_variant:,} per variant")
```

### Multi-Variant Tests (ANOVA)

```python
result = magnitude.analyze_multi(
    variants=[
        {"name": "control", "visitors": 1000, "mean": 50, "std": 25},
        {"name": "new_layout", "visitors": 1000, "mean": 52, "std": 25},
        {"name": "premium_upsell", "visitors": 1000, "mean": 55, "std": 25},
    ]
)

print(f"Best: {result.best_variant}")
print(f"F-statistic: {result.f_statistic:.2f}")
```

### Difference-in-Differences

```python
result = magnitude.diff_in_diff(
    control_pre_n=1000, control_pre_mean=50, control_pre_std=25,
    control_post_n=1000, control_post_mean=51, control_post_std=25,
    treatment_pre_n=1000, treatment_pre_mean=50, treatment_pre_std=25,
    treatment_post_n=1000, treatment_post_mean=55, treatment_post_std=26,
)

print(f"DiD effect: ${result.diff_in_diff:+.2f}")
```

---

## ⏱️ Timing Effects — *When* it happens

Use when you care about time-to-event: time to purchase, time to churn, event rates.

### Survival Analysis

```python
from pyexpstats import timing

result = timing.analyze(
    control_times=[5, 8, 12, 15, 18, 22, 25, 30],
    control_events=[1, 1, 1, 0, 1, 1, 0, 1],      # 1=event, 0=censored
    treatment_times=[3, 6, 9, 12, 14, 16, 20, 24],
    treatment_events=[1, 1, 1, 1, 0, 1, 1, 1],
)

print(f"Control median time: {result.control_median_time}")
print(f"Treatment median time: {result.treatment_median_time}")
print(f"Hazard ratio: {result.hazard_ratio:.3f}")
print(f"Significant: {result.is_significant}")
```

### Kaplan-Meier Survival Curves

```python
curve = timing.survival_curve(
    times=[5, 10, 15, 20, 25, 30],
    events=[1, 1, 0, 1, 1, 0],
    confidence=95,
)

print(f"Median survival time: {curve.median_time}")
print(f"Survival probabilities: {curve.survival_probabilities}")
```

### Event Rate Analysis (Poisson)

```python
result = timing.analyze_rates(
    control_events=45,
    control_exposure=100,      # 100 days of observation
    treatment_events=38,
    treatment_exposure=100,
)

print(f"Rate ratio: {result.rate_ratio:.3f}")
print(f"Significant: {result.is_significant}")
```

---

## 📋 Generate Stakeholder Reports

Every effect type includes `summarize()` for markdown reports:

```python
result = conversion.analyze(...)
report = conversion.summarize(result, test_name="Signup Button Test")
print(report)
```

---

## 🌐 Web Interface

pyexpstats includes a web UI for interactive analysis:

```bash
pyexpstats-server
# Open http://localhost:8000
```

Features include:

- **Sample Size Calculator** — Plan tests with intuitive parameter explanations
- **A/B Test Results** — Analyze 2-variant and multi-variant tests
- **Timing & Rates** — Survival analysis and Poisson rate comparisons
- **Diff-in-Diff** — Quasi-experimental causal inference
- **Confidence Intervals** — Estimate precision of your metrics

---

## Why "Outcome Effects"?

Traditional A/B testing tools are **test-centric**: "Which statistical test should I use?"

pyexpstats is **effect-centric**: "What changed about user behavior?"

This means:

1. **Matches how stakeholders think** — "Did conversion increase?" not "Did we reject the null hypothesis?"
2. **Avoids false equivalence** — A conversion effect and a magnitude effect are different things
3. **Generalizes naturally** — Timing, variance, and durability effects fit cleanly

---

## Best Practices

1. **Decide sample size BEFORE starting** — Don't peek and stop early
2. **Run for at least 1-2 weeks** — Capture weekly patterns
3. **Look at confidence intervals** — Not just p-values
4. **Statistical significance ≠ business significance** — A 0.1% lift might be "significant" but not worth it
5. **Use Bonferroni correction** — For multi-variant tests

---

## License

MIT License

---

## Credits

Inspired by [Evan Miller's A/B Testing Tools](https://www.evanmiller.org/ab-testing/).
