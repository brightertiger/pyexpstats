# Analyzing Results

Once your test has collected enough data, it's time to analyze the results.

## Basic Analysis

### Conversion Rate Test

```python
from pyexpstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,      # 5.0%
    variant_visitors=10000,
    variant_conversions=600,      # 6.0%
)

# Key metrics
print(f"Control rate: {result.control_rate:.2%}")
print(f"Variant rate: {result.variant_rate:.2%}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
print(f"Winner: {result.winner}")
```

### Revenue Test

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

print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"Winner: {result.winner}")
```

## Understanding the Results

### Is It Significant?

Check `result.is_significant`:

```python
if result.is_significant:
    print(f"Winner: {result.winner}")
else:
    print("No winner yet - need more data")
```

!!! info "What 'significant' means"
    Statistical significance means the observed difference is unlikely to be due to random chance. It does NOT mean the difference is large or important.

### Reading the P-Value

The p-value tells you the probability of seeing your results if there was **no real difference**:

| P-value | Interpretation |
|---------|----------------|
| < 0.01 | Very strong evidence |
| 0.01 - 0.05 | Strong evidence (significant at 95% confidence) |
| 0.05 - 0.10 | Weak evidence |
| > 0.10 | Not enough evidence |

### Confidence Intervals

The confidence interval tells you the likely range of the true effect:

```python
print(f"95% CI: [{result.confidence_interval_lower:.4f}, {result.confidence_interval_upper:.4f}]")
```

If the CI doesn't include zero, the result is significant.

## The Recommendation

Every result includes a plain-English recommendation:

```python
print(result.recommendation)
```

Example output:
```
**Test variant is significantly higher than control** (p-value: 0.0003).

_What this means:_ With 95% confidence, the difference between variant (6.00%)
and control (5.00%) is statistically real, not due to random chance. A p-value
of 0.0003 means there's only a 0.03% probability this result occurred by chance.
```

## Generating Reports

Create shareable reports for stakeholders:

```python
report = conversion.summarize(
    result,
    test_name="Homepage CTA Test"
)
print(report)
```

For revenue tests, customize the metric name and currency:

```python
report = magnitude.summarize(
    result,
    test_name="Checkout Flow Test",
    metric_name="Average Order Value",
    currency="€"
)
```

## Common Scenarios

### Scenario 1: Clear Winner

```python
result.is_significant  # True
result.winner          # "variant"
result.lift_percent    # +20.0%
```

**Action:** Implement the variant!

### Scenario 2: No Significant Difference

```python
result.is_significant  # False
result.p_value         # 0.35
```

**Action:** Either:
- Run the test longer to collect more data
- Accept that the variants are equivalent
- The effect may be smaller than you designed for

### Scenario 3: Significant, But Small Effect

```python
result.is_significant  # True
result.lift_percent    # +1.2%
```

**Action:** Consider if a 1.2% improvement is worth the implementation effort.

### Scenario 4: Control Wins

```python
result.is_significant  # True
result.winner          # "control"
result.lift_percent    # -15.0%
```

**Action:** Don't implement the variant—it hurts performance!

## Best Practices

1. **Don't peek** - Decide your sample size before starting and stick to it
2. **Run full weeks** - Capture day-of-week patterns
3. **Look at confidence intervals** - They tell you the range of possible effects
4. **Consider business impact** - Statistical significance ≠ business significance
