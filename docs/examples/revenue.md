# Revenue Test Examples

Real-world examples of using expstats for revenue and numeric metric A/B tests.

## Example 1: Average Order Value Test

You're testing a product recommendation feature. After 2 weeks:

- **Control:** 3,000 orders, $48.50 average, $22.00 std dev
- **Variant:** 3,000 orders, $52.30 average, $24.00 std dev

```python
from expstats import magnitude

result = magnitude.analyze(
    control_visitors=3000,
    control_mean=48.50,
    control_std=22.00,
    variant_visitors=3000,
    variant_mean=52.30,
    variant_std=24.00,
)

print(f"Control AOV: ${result.control_mean:.2f}")
print(f"Variant AOV: ${result.variant_mean:.2f}")
print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"P-value: {result.p_value:.4f}")
print(f"Winner: {result.winner}")
```

Output:
```
Control AOV: $48.50
Variant AOV: $52.30
Lift: +$3.80 (+7.8%)
P-value: 0.0001
Winner: variant
```

**Decision:** Implement the recommendation feature!

---

## Example 2: Session Duration Test

Testing a new content layout to increase engagement:

- **Control:** 5,000 sessions, 180 seconds average, 120 seconds std dev
- **Variant:** 5,000 sessions, 195 seconds average, 130 seconds std dev

```python
result = magnitude.analyze(
    control_visitors=5000,
    control_mean=180,
    control_std=120,
    variant_visitors=5000,
    variant_mean=195,
    variant_std=130,
)

print(f"Control: {result.control_mean:.0f}s ({result.control_mean/60:.1f} min)")
print(f"Variant: {result.variant_mean:.0f}s ({result.variant_mean/60:.1f} min)")
print(f"Lift: {result.lift_absolute:+.0f}s ({result.lift_percent:+.1f}%)")
print(f"Significant: {result.is_significant}")
```

Output:
```
Control: 180s (3.0 min)
Variant: 195s (3.2 min)
Lift: +15s (+8.3%)
Significant: True
```

---

## Example 3: Planning an AOV Test

You want to test a premium upsell feature. Your current AOV is $45 with a std dev of $30.

```python
plan = magnitude.sample_size(
    current_mean=45,      # $45 AOV
    current_std=30,       # $30 standard deviation
    lift_percent=5,       # detect 5% lift ($45 → $47.25)
    confidence=95,
    power=80,
)

print(f"Need {plan.visitors_per_variant:,} orders per variant")
print(f"Total: {plan.total_visitors:,} orders")

# With 500 orders/day
plan.with_daily_traffic(500)
print(f"Duration: {plan.test_duration_days} days")
```

Output:
```
Need 3,507 orders per variant
Total: 7,014 orders
Duration: 15 days
```

---

## Example 4: Test with No Winner

Testing a new pricing page:

- **Control:** 2,000 customers, $55.00 average, $28.00 std dev
- **Variant:** 2,000 customers, $56.50 average, $30.00 std dev

```python
result = magnitude.analyze(
    control_visitors=2000,
    control_mean=55.00,
    control_std=28.00,
    variant_visitors=2000,
    variant_mean=56.50,
    variant_std=30.00,
)

print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
print(f"Winner: {result.winner}")
```

Output:
```
Lift: +$1.50 (+2.7%)
P-value: 0.0872
Significant: False
Winner: no winner yet
```

**Decision:** Need more data, or the effect may be smaller than designed for.

---

## Example 5: Stakeholder Report

Generate a report in different currencies:

```python
result = magnitude.analyze(
    control_visitors=5000,
    control_mean=45.00,
    control_std=20.00,
    variant_visitors=5000,
    variant_mean=48.00,
    variant_std=22.00,
)

# Report in USD
report_usd = magnitude.summarize(
    result,
    test_name="Checkout Upsell Test",
    metric_name="Average Order Value",
    currency="$"
)

# Report in EUR
report_eur = magnitude.summarize(
    result,
    test_name="Checkout Upsell Test",
    metric_name="Average Order Value",
    currency="€"
)

print(report_usd)
```

Output:
```markdown
## 📊 Checkout Upsell Test Results

### ✅ Significant Result

**The test variant's average order value is significantly higher than control.**

- **Control average order value:** $45.00 (n=5,000, std=$20.00)
- **Variant average order value:** $48.00 (n=5,000, std=$22.00)
- **Relative lift:** +6.7% increase
- **Absolute difference:** +$3.00
- **P-value:** 0.0001
- **Confidence level:** 95%

### 📝 What This Means

With 95% confidence, the difference is statistically significant.
The variant shows a **$3.00** (6.7%) improvement over control.
```

---

## Example 6: Confidence Interval for AOV

Understand the uncertainty in your average order value:

```python
ci = magnitude.confidence_interval(
    visitors=1000,
    mean=50.00,
    std=25.00,
    confidence=95,
)

print(f"AOV: ${ci.mean:.2f}")
print(f"95% CI: [${ci.lower:.2f}, ${ci.upper:.2f}]")
print(f"Margin of error: ±${ci.margin_of_error:.2f}")
```

Output:
```
AOV: $50.00
95% CI: [$48.45, $51.55]
Margin of error: ±$1.55
```

**Interpretation:** We're 95% confident the true AOV is between $48.45 and $51.55.

---

## Example 7: Calculating Annual Impact

If your test wins, estimate the annual revenue impact:

```python
result = magnitude.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)

if result.is_significant and result.winner == "variant":
    # Assume 100,000 orders per year
    annual_orders = 100000
    annual_lift = result.lift_absolute * annual_orders
    
    # Using CI bounds for range
    low_impact = result.confidence_interval_lower * annual_orders
    high_impact = result.confidence_interval_upper * annual_orders
    
    print(f"Expected annual impact: ${annual_lift:,.0f}")
    print(f"95% CI: [${low_impact:,.0f}, ${high_impact:,.0f}]")
```

Output:
```
Expected annual impact: $250,000
95% CI: [$152,000, $348,000]
```
