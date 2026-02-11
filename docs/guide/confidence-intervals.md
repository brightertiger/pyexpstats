# Confidence Intervals

Confidence intervals tell you the range where your true metric likely falls. They're often more useful than just knowing if a result is "significant."

## Why Confidence Intervals Matter

A p-value only tells you "is there a difference?"

A confidence interval tells you "how big is the difference likely to be?"

!!! example "Example"
    Two tests both have p < 0.05 (significant):
    
    - **Test A:** Lift = +5%, CI = [+0.1%, +9.9%] - Could be tiny or substantial
    - **Test B:** Lift = +5%, CI = [+4.2%, +5.8%] - Reliably around 5%
    
    The confidence interval gives you much more information!

## Single Rate Confidence Interval

Get the range for a single conversion rate:

```python
from pyexpstats import conversion

ci = conversion.confidence_interval(
    visitors=1000,
    conversions=50,
    confidence=95,
)

print(f"Rate: {ci.rate:.2%}")
print(f"95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")
print(f"Margin of error: ±{ci.margin_of_error:.2%}")
```

Output:
```
Rate: 5.00%
95% CI: [3.81%, 6.51%]
Margin of error: ±1.35%
```

## Single Mean Confidence Interval

Get the range for a numeric metric:

```python
from pyexpstats import magnitude

ci = magnitude.confidence_interval(
    visitors=1000,
    mean=50.00,
    std=25.00,
    confidence=95,
)

print(f"Mean: ${ci.mean:.2f}")
print(f"95% CI: [${ci.lower:.2f}, ${ci.upper:.2f}]")
```

## Confidence Intervals in Test Results

Every test result includes confidence intervals for the **lift**:

```python
result = conversion.analyze(...)

print(f"Lift: {result.lift_absolute:.4f}")
print(f"CI: [{result.confidence_interval_lower:.4f}, {result.confidence_interval_upper:.4f}]")
```

### Interpreting the CI

| CI Range | Interpretation |
|----------|----------------|
| Both bounds positive | Variant is better (significant positive effect) |
| Both bounds negative | Control is better (significant negative effect) |
| Spans zero | No significant difference |

## Effect of Sample Size

Larger samples give narrower (more precise) confidence intervals:

```python
# Small sample
ci_small = conversion.confidence_interval(visitors=100, conversions=5)
print(f"n=100: [{ci_small.lower:.2%}, {ci_small.upper:.2%}]")

# Large sample
ci_large = conversion.confidence_interval(visitors=10000, conversions=500)
print(f"n=10000: [{ci_large.lower:.2%}, {ci_large.upper:.2%}]")
```

Output:
```
n=100: [2.16%, 11.18%]   (9% wide)
n=10000: [4.60%, 5.42%]  (0.8% wide)
```

## Choosing Confidence Level

Common choices:

| Level | Z-score | Use When |
|-------|---------|----------|
| 90% | 1.645 | Exploratory analysis |
| 95% | 1.96 | Standard for most tests |
| 99% | 2.576 | High-stakes decisions |

```python
ci_90 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=90)
ci_95 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=95)
ci_99 = conversion.confidence_interval(visitors=1000, conversions=50, confidence=99)

print(f"90% CI: [{ci_90.lower:.2%}, {ci_90.upper:.2%}]")
print(f"95% CI: [{ci_95.lower:.2%}, {ci_95.upper:.2%}]")
print(f"99% CI: [{ci_99.lower:.2%}, {ci_99.upper:.2%}]")
```

Higher confidence = wider interval.

## Methods Used

### For Conversion Rates

pyexpstats uses the **Wilson score interval**, which is more accurate than the normal approximation for:
- Small samples
- Rates near 0% or 100%

### For Numeric Metrics

pyexpstats uses the **t-distribution**, which accounts for uncertainty in the standard deviation estimate.

## Best Practices

1. **Always look at CIs** - Not just p-values
2. **Consider practical significance** - Is the lower bound of the CI large enough to matter?
3. **Use appropriate sample sizes** - Wider CIs = less certainty
4. **Report CIs in presentations** - They're more informative than p-values alone
