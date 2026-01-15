# pyexptest

**Simple A/B testing tools for marketers, analysts, and product teams.**

No statistics PhD required. Just tell us your numbers, and we'll tell you what they mean.

## Installation

```bash
pip install pyexptest
```

## Quick Start

pyexptest has two modules:
- **`conversion_effect`** - for conversion rates (click rates, sign-up rates, purchase rates)
- **`numeric_effect`** - for revenue, average order value, time on page, etc.

Each module supports:
- **2-variant tests** (standard A/B tests) - `analyze()`
- **Multi-variant tests** (A/B/C/D...) - `analyze_multi()`
- **Sample size calculation** - `sample_size()`
- **Stakeholder reports** - `summarize()` / `summarize_multi()`

---

## 📐 Sample Size Calculator

### For Conversion Rate Tests

```python
from pyexptest import conversion_effect

# "I have a 5% conversion rate and want to detect a 10% improvement"
plan = conversion_effect.sample_size(
    current_rate=5,      # Current conversion rate (5%)
    lift_percent=10,     # Want to detect 10% lift
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
print(f"Total: {plan.total_visitors:,} visitors")

# Add daily traffic to estimate duration
plan.with_daily_traffic(5000)
print(f"Estimated duration: {plan.test_duration_days} days")
```

### For Multi-Variant Tests (3+ variants)

```python
# Planning an A/B/C test? You need more visitors:
plan = conversion_effect.sample_size(
    current_rate=5,
    lift_percent=10,
    num_variants=3,  # Control + 2 variants
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
print(f"Total: {plan.total_visitors:,} visitors")
```

### For Revenue / AOV Tests

```python
from pyexptest import numeric_effect

# "My AOV is $50 (std dev $25) and I want to detect a 5% lift"
plan = numeric_effect.sample_size(
    current_mean=50,     # Current average order value
    current_std=25,      # Standard deviation (ask your analyst)
    lift_percent=5,      # Want to detect 5% lift
)

print(f"You need {plan.visitors_per_variant:,} visitors per variant")
```

---

## 📊 Analyze Test Results (2 Variants)

### For Conversion Rate Tests

```python
from pyexptest import conversion_effect

result = conversion_effect.analyze(
    control_visitors=10000,
    control_conversions=500,      # 5.0% conversion rate
    variant_visitors=10000,
    variant_conversions=600,      # 6.0% conversion rate
)

print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
print(f"Significant: {result.is_significant}")
print(f"\n{result.recommendation}")
```

Output:
```
Lift: +20.0%
Winner: variant
Significant: True

**Test variant is significantly higher than control** (p-value: 0.0003).

_What this means:_ With 95% confidence, the difference between variant (6.00%)
and control (5.00%) is statistically real, not due to random chance. A p-value
of 0.0003 means there's only a 0.03% probability this result occurred by chance.
```

### For Revenue / AOV Tests

```python
from pyexptest import numeric_effect

result = numeric_effect.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)

print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
```

---

## 📊 Analyze Multi-Variant Tests (3+ Variants)

### For Conversion Rate Tests (Chi-Square)

```python
from pyexptest import conversion_effect

result = conversion_effect.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 550},
        {"name": "variant_b", "visitors": 10000, "conversions": 600},
        {"name": "variant_c", "visitors": 10000, "conversions": 480},
    ]
)

print(f"Best variant: {result.best_variant}")
print(f"Significant: {result.is_significant}")
print(f"P-value: {result.p_value:.4f}")

# See pairwise comparisons
for p in result.pairwise_comparisons:
    if p.is_significant:
        print(f"  {p.variant_a} vs {p.variant_b}: {p.lift_percent:+.1f}% (p={p.p_value_adjusted:.4f})")
```

### For Revenue Tests (ANOVA)

```python
from pyexptest import numeric_effect

result = numeric_effect.analyze_multi(
    variants=[
        {"name": "control", "visitors": 1000, "mean": 50, "std": 25},
        {"name": "new_layout", "visitors": 1000, "mean": 52, "std": 25},
        {"name": "premium_upsell", "visitors": 1000, "mean": 55, "std": 25},
    ]
)

print(f"Best variant: {result.best_variant}")
print(f"F-statistic: {result.f_statistic:.2f}")
print(f"P-value: {result.p_value:.4f}")
```

---

## 📋 Generate Stakeholder Reports

Get a nicely formatted markdown report you can share with your team:

### For 2-Variant Tests

```python
from pyexptest import conversion_effect

result = conversion_effect.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)

# Generate the report
print(conversion_effect.summarize(result, test_name="Homepage Button Test"))
```

### For Multi-Variant Tests

```python
result = conversion_effect.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "red_button", "visitors": 10000, "conversions": 550},
        {"name": "green_button", "visitors": 10000, "conversions": 600},
    ]
)

print(conversion_effect.summarize_multi(result, test_name="Button Color Test"))
```

Output:
```markdown
## 📊 Button Color Test Results

### ✅ Significant Differences Detected

**At least one variant performs differently from the others.**

### Variant Performance

| Variant | Visitors | Conversions | Rate |
|---------|----------|-------------|------|
| green_button 🏆 | 10,000 | 600 | 6.00% |
| red_button | 10,000 | 550 | 5.50% |
| control | 10,000 | 500 | 5.00% |

### Overall Test (Chi-Square)

- **Test statistic:** 19.48
- **Degrees of freedom:** 2
- **P-value:** 0.0001
- **Confidence level:** 95%

### Significant Pairwise Differences

- **green_button** beats **control** by 20.0% (p=0.0003)
- **green_button** beats **red_button** by 9.1% (p=0.0456)

### 📝 What This Means

With 95% confidence, there are real differences between your variants.
**green_button** has the highest conversion rate.
```

---

## 📏 Confidence Intervals

Get the range where your true rate likely falls:

```python
from pyexptest import conversion_effect

ci = conversion_effect.confidence_interval(
    visitors=1000,
    conversions=50,
    confidence=95,
)

print(f"Conversion rate: {ci.rate:.2%}")
print(f"95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")
print(f"Margin of error: ±{ci.margin_of_error:.2%}")
```

---

## Web Interface

pyexptest also includes a web UI for those who prefer clicking over coding:

```bash
# Start the server
pyexptest-server

# Open http://localhost:8000 in your browser
```

---

## API Reference

### conversion_effect module

| Function | Purpose |
|----------|---------|
| `sample_size(current_rate, lift_percent, confidence=95, power=80, num_variants=2)` | Calculate required sample size |
| `analyze(control_visitors, control_conversions, variant_visitors, variant_conversions, confidence=95)` | Analyze 2-variant test |
| `analyze_multi(variants, confidence=95, correction="bonferroni")` | Analyze multi-variant test (Chi-square) |
| `confidence_interval(visitors, conversions, confidence=95)` | Calculate confidence interval |
| `summarize(result, test_name)` | Generate 2-variant report |
| `summarize_multi(result, test_name)` | Generate multi-variant report |

### numeric_effect module

| Function | Purpose |
|----------|---------|
| `sample_size(current_mean, current_std, lift_percent, confidence=95, power=80, num_variants=2)` | Calculate required sample size |
| `analyze(control_visitors, control_mean, control_std, variant_visitors, variant_mean, variant_std, confidence=95)` | Analyze 2-variant test |
| `analyze_multi(variants, confidence=95, correction="bonferroni")` | Analyze multi-variant test (ANOVA) |
| `confidence_interval(visitors, mean, std, confidence=95)` | Calculate confidence interval |
| `summarize(result, test_name, metric_name, currency)` | Generate 2-variant report |
| `summarize_multi(result, test_name, metric_name, currency)` | Generate multi-variant report |

---

## Parameters Explained

| Parameter | What it means | Typical values |
|-----------|---------------|----------------|
| `current_rate` | Your current conversion rate | 1-10% for most sites |
| `lift_percent` | Smallest improvement worth detecting | 5-20% |
| `confidence` | How sure you want to be (avoids false positives) | 95% (standard) |
| `power` | Chance of detecting a real effect | 80% (standard) |
| `current_std` | How much your metric varies | Ask your analyst |
| `num_variants` | Total number of variants (including control) | 2 for A/B, 3+ for multi |
| `correction` | Multiple comparison correction | "bonferroni" (recommended) |

---

## Understanding P-Values

The p-value tells you the probability of seeing your results **if there was no real difference**:

| P-value | Interpretation |
|---------|----------------|
| < 0.01 | Very strong evidence of a real difference |
| 0.01 - 0.05 | Strong evidence (typical threshold for "significant") |
| 0.05 - 0.10 | Weak evidence, consider more data |
| > 0.10 | Not enough evidence to conclude there's a difference |

**Example:** A p-value of 0.03 means there's only a 3% chance you'd see this result if the control and variant were actually identical. That's pretty unlikely, so we conclude the difference is real.

---

## Multi-Variant Testing Notes

When testing multiple variants:

1. **Use Bonferroni correction** (default) - This adjusts p-values to account for multiple comparisons, reducing false positives.

2. **Plan for more visitors** - Testing 3 variants needs ~1.5x the sample size of 2 variants to maintain the same statistical power.

3. **The overall test is a screening** - Chi-square/ANOVA tells you "something is different", then pairwise comparisons tell you "what specifically".

4. **Don't run too many variants** - Each additional variant requires more sample size. Stick to 3-4 variants max for most tests.

---

## Common Questions

### "How long should I run my test?"

Use `sample_size()` and divide by your daily traffic:

```python
plan = conversion_effect.sample_size(current_rate=5, lift_percent=10)
plan.with_daily_traffic(10000)  # 10k visitors/day
print(f"Run for at least {plan.test_duration_days} days")
```

### "Is my result significant?"

Check `result.is_significant` - if `True`, you have a winner!

```python
result = conversion_effect.analyze(...)
if result.is_significant:
    print(f"Winner: {result.winner}")
else:
    print("Keep running the test")
```

### "What if my test shows no winner?"

That's valuable information! It means the change doesn't have a meaningful impact. Either:
1. The variants are truly equivalent → ship whichever is easier
2. You need more visitors → check if you have enough sample size
3. The effect is smaller than you designed for → re-run with smaller `lift_percent`

---

## Best Practices

1. **Decide sample size BEFORE you start** - Don't peek and stop early
2. **Run for at least 1-2 weeks** - Capture weekly patterns
3. **Don't run too many tests at once** - They can interfere
4. **Statistical significance ≠ business significance** - A 0.1% lift might be "significant" but not worth the effort
5. **Look at confidence intervals, not just p-values** - They tell you the range of possible effects
6. **Use Bonferroni correction for multi-variant tests** - Prevents false positives

---

## License

MIT License

---

## Credits

Inspired by [Evan Miller's A/B Testing Tools](https://www.evanmiller.org/ab-testing/).
