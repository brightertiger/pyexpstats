# Multi-Variant Tests

Sometimes you want to test more than one variant at a time. expstats supports multi-variant testing with proper statistical adjustments.

## When to Use Multi-Variant Tests

✅ **Good use cases:**
- Testing 2-3 different designs
- Comparing multiple pricing options
- Testing several copy variations

❌ **Bad use cases:**
- Testing 10+ variants (need too much traffic)
- Testing unrelated changes (run separate tests)

## Planning a Multi-Variant Test

Multi-variant tests need more sample size:

```python
from expstats import conversion

# 2-variant test
plan_2 = conversion.sample_size(current_rate=5, lift_percent=10, num_variants=2)
print(f"2 variants: {plan_2.total_visitors:,} total")

# 3-variant test
plan_3 = conversion.sample_size(current_rate=5, lift_percent=10, num_variants=3)
print(f"3 variants: {plan_3.total_visitors:,} total")

# 4-variant test
plan_4 = conversion.sample_size(current_rate=5, lift_percent=10, num_variants=4)
print(f"4 variants: {plan_4.total_visitors:,} total")
```

Output:
```
2 variants: 62,468 total
3 variants: 108,702 total  (+74%)
4 variants: 157,872 total  (+153%)
```

!!! warning "Traffic Requirements"
    Each additional variant significantly increases the required sample size. Stick to 3-4 variants max.

## Analyzing Conversion Rate Tests

Use Chi-square test for conversion rate multi-variant tests:

```python
from expstats import conversion

result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "red_button", "visitors": 10000, "conversions": 550},
        {"name": "green_button", "visitors": 10000, "conversions": 600},
        {"name": "blue_button", "visitors": 10000, "conversions": 480},
    ]
)

print(f"Overall significant: {result.is_significant}")
print(f"Best variant: {result.best_variant}")
print(f"P-value: {result.p_value:.4f}")
```

### Understanding the Results

The multi-variant test has two levels:

1. **Overall test (Chi-square):** Is there ANY difference between variants?
2. **Pairwise comparisons:** WHICH variants are different from each other?

```python
# Overall test
print(f"Chi-square statistic: {result.test_statistic:.2f}")
print(f"P-value: {result.p_value:.4f}")

# Pairwise comparisons
for p in result.pairwise_comparisons:
    status = "✓" if p.is_significant else " "
    print(f"{status} {p.variant_a} vs {p.variant_b}: {p.lift_percent:+.1f}% (p={p.p_value_adjusted:.4f})")
```

## Analyzing Revenue Tests

Use ANOVA for numeric metric multi-variant tests:

```python
from expstats import magnitude

result = magnitude.analyze_multi(
    variants=[
        {"name": "control", "visitors": 1000, "mean": 50, "std": 25},
        {"name": "simple_checkout", "visitors": 1000, "mean": 52, "std": 25},
        {"name": "premium_upsell", "visitors": 1000, "mean": 55, "std": 25},
    ]
)

print(f"F-statistic: {result.f_statistic:.2f}")
print(f"Best variant: {result.best_variant}")
```

## Bonferroni Correction

When making multiple comparisons, we adjust p-values to avoid false positives:

```python
# With correction (default)
result = conversion.analyze_multi(variants, correction="bonferroni")

# Without correction (not recommended)
result = conversion.analyze_multi(variants, correction="none")
```

!!! info "Why Bonferroni?"
    Testing 3 variants means 3 pairwise comparisons. Without correction, you have a ~14% chance of a false positive instead of 5%. Bonferroni adjusts p-values to maintain the 5% overall false positive rate.

## Generating Reports

```python
report = conversion.summarize_multi(
    result,
    test_name="Button Color Test"
)
print(report)
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
| blue_button | 10,000 | 480 | 4.80% |

### Overall Test (Chi-Square)

- **Test statistic:** 27.45
- **Degrees of freedom:** 3
- **P-value:** 0.0001
- **Confidence level:** 95%

### Significant Pairwise Differences

- **green_button** beats **control** by 20.0% (p=0.0003)
- **green_button** beats **blue_button** by 25.0% (p=0.0001)
- **red_button** beats **blue_button** by 14.6% (p=0.0234)

### 📝 What This Means

With 95% confidence, there are real differences between your variants.
**green_button** has the highest conversion rate.
```

## Best Practices

1. **Limit variants** - Stick to 3-4 variants max
2. **Use Bonferroni** - Always use correction for pairwise comparisons
3. **Plan traffic** - Calculate sample size before starting
4. **Overall first** - If overall test isn't significant, don't trust pairwise comparisons
5. **Pre-register** - Decide which comparisons matter before seeing results
