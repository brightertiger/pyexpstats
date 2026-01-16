# Understanding P-Values

P-values are widely used but often misunderstood. This guide explains what they actually mean and how to interpret them correctly.

## What a P-Value Is

The p-value is the probability of seeing results **as extreme as yours** if there was **no real difference** between control and variant.

!!! info "In Plain English"
    "If the variant was actually identical to control, how likely would I be to see this result just by chance?"

## Interpreting P-Values

| P-value | Interpretation |
|---------|----------------|
| < 0.01 | Very strong evidence of a real difference |
| 0.01 - 0.05 | Strong evidence (significant at 95% confidence) |
| 0.05 - 0.10 | Weak evidence, consider more data |
| > 0.10 | Not enough evidence to conclude there's a difference |

### Example

```python
from expstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,    # 5.0%
    variant_visitors=10000,
    variant_conversions=600,    # 6.0%
)

print(f"P-value: {result.p_value:.4f}")
```

Output: `P-value: 0.0003`

**Interpretation:** There's only a 0.03% chance of seeing a 1 percentage point difference (or larger) if the variant was actually the same as control. This is very unlikely, so we conclude the variant really is different.

## What P-Values Do NOT Mean

❌ **Wrong:** "There's a 0.03% chance the variant isn't better"

❌ **Wrong:** "The variant is 99.97% likely to be better"

❌ **Wrong:** "The effect is large"

✅ **Right:** "If there was no real difference, we'd only see results this extreme 0.03% of the time"

## The 0.05 Threshold

The conventional threshold is p < 0.05 (5%), which corresponds to 95% confidence.

```python
if result.p_value < 0.05:
    print("Statistically significant at 95% confidence")
else:
    print("Not statistically significant")
```

!!! warning "0.05 is arbitrary"
    The 0.05 threshold is a convention, not a law of nature. A p-value of 0.051 isn't meaningfully different from 0.049.

## Relationship to Confidence Level

| Confidence Level | P-value Threshold |
|------------------|-------------------|
| 90% | < 0.10 |
| 95% | < 0.05 |
| 99% | < 0.01 |

```python
# 95% confidence (default)
result_95 = conversion.analyze(..., confidence=95)
# Significant if p < 0.05

# 99% confidence
result_99 = conversion.analyze(..., confidence=99)
# Significant if p < 0.01
```

## Common Mistakes

### Mistake 1: Peeking and Stopping Early

**Problem:** Checking results daily and stopping when p < 0.05.

**Why it's wrong:** The more you check, the more likely you'll see p < 0.05 by chance.

**Solution:** Calculate sample size before starting and don't peek.

### Mistake 2: Ignoring Effect Size

**Problem:** A test shows p = 0.01 with a 0.1% lift.

**Why it's wrong:** Statistical significance doesn't mean business significance.

**Solution:** Always look at confidence intervals and consider if the effect is worth implementing.

### Mistake 3: Multiple Comparisons

**Problem:** Running 20 tests and declaring 1 winner (p = 0.04).

**Why it's wrong:** With 20 tests, you expect ~1 false positive at p < 0.05.

**Solution:** Use Bonferroni correction for multi-variant tests.

## P-Value vs. Confidence Interval

P-values tell you: "Is there a difference?"

Confidence intervals tell you: "How big is the difference?"

```python
result = conversion.analyze(...)

# P-value approach
if result.p_value < 0.05:
    print("Significant!")

# CI approach (more informative)
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"CI: [{result.confidence_interval_lower:.4f}, {result.confidence_interval_upper:.4f}]")
```

!!! tip "Best practice"
    Report both the p-value AND the confidence interval. The CI tells stakeholders the likely range of the true effect.

## One-Tailed vs. Two-Tailed

expstats uses **two-tailed** tests by default, which is appropriate when you want to detect effects in either direction.

| Test Type | Detects | Use When |
|-----------|---------|----------|
| Two-tailed | Effects in either direction | Most A/B tests |
| One-tailed | Effects in only one direction | Rarely appropriate |

## Summary

1. **P-value** = Probability of seeing your results if there's no real difference
2. **p < 0.05** is the conventional threshold for "significant"
3. **Don't peek** - Calculate sample size first
4. **Look at CIs** - They're more informative than p-values alone
5. **Consider business impact** - Statistical significance ≠ business significance
