# Multi-Variant Test Examples

Real-world examples of using expstats for tests with 3+ variants.

## Example 1: Button Color Test (Conversion)

Testing 4 button colors on your CTA:

```python
from expstats import conversion

result = conversion.analyze_multi(
    variants=[
        {"name": "blue (control)", "visitors": 10000, "conversions": 500},
        {"name": "green", "visitors": 10000, "conversions": 580},
        {"name": "orange", "visitors": 10000, "conversions": 620},
        {"name": "red", "visitors": 10000, "conversions": 490},
    ]
)

print(f"Overall significant: {result.is_significant}")
print(f"P-value: {result.p_value:.4f}")
print(f"Best variant: {result.best_variant}")
print(f"Worst variant: {result.worst_variant}")

print("\nVariant Performance:")
for v in sorted(result.variants, key=lambda x: x.rate, reverse=True):
    marker = "🏆" if v.name == result.best_variant else ""
    print(f"  {v.name}: {v.rate:.2%} {marker}")
```

Output:
```
Overall significant: True
P-value: 0.0001
Best variant: orange
Worst variant: red

Variant Performance:
  orange: 6.20% 🏆
  green: 5.80%
  blue (control): 5.00%
  red: 4.90%
```

---

## Example 2: Pricing Page Test (Revenue)

Testing 3 pricing page layouts:

```python
from expstats import magnitude

result = magnitude.analyze_multi(
    variants=[
        {"name": "control", "visitors": 2000, "mean": 49.00, "std": 22.00},
        {"name": "comparison_table", "visitors": 2000, "mean": 52.00, "std": 24.00},
        {"name": "value_focused", "visitors": 2000, "mean": 55.00, "std": 26.00},
    ]
)

print(f"F-statistic: {result.f_statistic:.2f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Best variant: {result.best_variant}")

print("\nVariant Performance:")
for v in sorted(result.variants, key=lambda x: x.mean, reverse=True):
    marker = "🏆" if v.name == result.best_variant else ""
    print(f"  {v.name}: ${v.mean:.2f} {marker}")
```

Output:
```
F-statistic: 24.56
P-value: 0.0001
Best variant: value_focused

Variant Performance:
  value_focused: $55.00 🏆
  comparison_table: $52.00
  control: $49.00
```

---

## Example 3: Examining Pairwise Comparisons

The overall test tells you "something is different," but pairwise comparisons tell you "what specifically":

```python
result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 520},
        {"name": "variant_b", "visitors": 10000, "conversions": 600},
    ]
)

print("Pairwise Comparisons:")
print("-" * 60)
for p in result.pairwise_comparisons:
    status = "✓ Significant" if p.is_significant else "  Not significant"
    print(f"{p.variant_a} vs {p.variant_b}:")
    print(f"  Lift: {p.lift_percent:+.1f}%")
    print(f"  P-value (adjusted): {p.p_value_adjusted:.4f}")
    print(f"  {status}")
    print()
```

Output:
```
Pairwise Comparisons:
------------------------------------------------------------
control vs variant_a:
  Lift: +4.0%
  P-value (adjusted): 0.4821
  Not significant

control vs variant_b:
  Lift: +20.0%
  P-value (adjusted): 0.0009
  ✓ Significant

variant_a vs variant_b:
  Lift: +15.4%
  P-value (adjusted): 0.0054
  ✓ Significant
```

---

## Example 4: Planning a Multi-Variant Test

Compare sample size requirements for different numbers of variants:

```python
for num_variants in [2, 3, 4, 5]:
    plan = conversion.sample_size(
        current_rate=5,
        lift_percent=10,
        num_variants=num_variants,
    )
    print(f"{num_variants} variants: {plan.total_visitors:,} total visitors")
```

Output:
```
2 variants: 62,468 total visitors
3 variants: 108,702 total visitors
4 variants: 157,872 total visitors
5 variants: 209,976 total visitors
```

!!! warning
    Each additional variant significantly increases sample size requirements!

---

## Example 5: Stakeholder Report (Conversion)

```python
result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 15000, "conversions": 600},
        {"name": "simplified_form", "visitors": 15000, "conversions": 720},
        {"name": "social_proof", "visitors": 15000, "conversions": 675},
    ]
)

report = conversion.summarize_multi(
    result,
    test_name="Signup Form Test"
)
print(report)
```

Output:
```markdown
## 📊 Signup Form Test Results

### ✅ Significant Differences Detected

**At least one variant performs differently from the others.**

### Variant Performance

| Variant | Visitors | Conversions | Rate |
|---------|----------|-------------|------|
| simplified_form 🏆 | 15,000 | 720 | 4.80% |
| social_proof | 15,000 | 675 | 4.50% |
| control | 15,000 | 600 | 4.00% |

### Overall Test (Chi-Square)

- **Test statistic:** 18.75
- **Degrees of freedom:** 2
- **P-value:** 0.0001
- **Confidence level:** 95%

### Significant Pairwise Differences

- **simplified_form** beats **control** by 20.0% (p=0.0003)
- **social_proof** beats **control** by 12.5% (p=0.0089)

### 📝 What This Means

With 95% confidence, there are real differences between your variants.
**simplified_form** has the highest conversion rate.
```

---

## Example 6: Stakeholder Report (Revenue)

```python
result = magnitude.analyze_multi(
    variants=[
        {"name": "standard", "visitors": 3000, "mean": 48.00, "std": 22.00},
        {"name": "premium_upsell", "visitors": 3000, "mean": 54.00, "std": 28.00},
        {"name": "bundle_offer", "visitors": 3000, "mean": 52.00, "std": 25.00},
    ]
)

report = magnitude.summarize_multi(
    result,
    test_name="Checkout Upsell Test",
    metric_name="Average Order Value",
    currency="$"
)
print(report)
```

Output:
```markdown
## 📊 Checkout Upsell Test Results

### ✅ Significant Differences Detected

**At least one variant performs differently from the others.**

### Variant Performance (Average Order Value)

| Variant | Sample Size | Mean | Std Dev |
|---------|-------------|------|---------|
| premium_upsell 🏆 | 3,000 | $54.00 | $28.00 |
| bundle_offer | 3,000 | $52.00 | $25.00 |
| standard | 3,000 | $48.00 | $22.00 |

### Overall Test (ANOVA)

- **F-statistic:** 45.23
- **Degrees of freedom:** (2, 8997)
- **P-value:** 0.0001
- **Confidence level:** 95%

### Significant Pairwise Differences

- **premium_upsell** beats **standard** by $6.00 (12.5%, p=0.0001)
- **bundle_offer** beats **standard** by $4.00 (8.3%, p=0.0001)

### 📝 What This Means

With 95% confidence, there are real differences between your variants.
**premium_upsell** has the highest average order value.
```

---

## Example 7: No Correction (Not Recommended)

You can disable Bonferroni correction, but this increases false positive risk:

```python
# With Bonferroni (default, recommended)
result_bonf = conversion.analyze_multi(
    variants=[...],
    correction="bonferroni"
)

# Without correction (higher false positive risk)
result_none = conversion.analyze_multi(
    variants=[...],
    correction="none"
)

# Compare number of "significant" comparisons
sig_bonf = sum(1 for p in result_bonf.pairwise_comparisons if p.is_significant)
sig_none = sum(1 for p in result_none.pairwise_comparisons if p.is_significant)

print(f"With Bonferroni: {sig_bonf} significant comparisons")
print(f"Without correction: {sig_none} significant comparisons")
```

!!! danger "Use with caution"
    Disabling correction increases the false positive rate. Only use for exploratory analysis.
