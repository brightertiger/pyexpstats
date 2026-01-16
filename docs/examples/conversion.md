# Conversion Rate Test Examples

Real-world examples of using expstats for conversion rate A/B tests.

## Example 1: Signup Button Test

You're testing a new signup button color. After 2 weeks:

- **Control (blue):** 15,000 visitors, 450 signups
- **Variant (green):** 15,000 visitors, 525 signups

```python
from expstats import conversion

result = conversion.analyze(
    control_visitors=15000,
    control_conversions=450,
    variant_visitors=15000,
    variant_conversions=525,
)

print(f"Control rate: {result.control_rate:.2%}")
print(f"Variant rate: {result.variant_rate:.2%}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"P-value: {result.p_value:.4f}")
print(f"Winner: {result.winner}")
```

Output:
```
Control rate: 3.00%
Variant rate: 3.50%
Lift: +16.7%
P-value: 0.0042
Winner: variant
```

**Decision:** Implement the green button!

---

## Example 2: Email Subject Line Test

Testing two email subject lines:

- **Subject A:** "Don't miss out!"
  - Sent: 50,000
  - Opens: 12,500
- **Subject B:** "Your exclusive offer inside"
  - Sent: 50,000
  - Opens: 13,750

```python
result = conversion.analyze(
    control_visitors=50000,
    control_conversions=12500,
    variant_visitors=50000,
    variant_conversions=13750,
)

print(f"Open rate A: {result.control_rate:.2%}")
print(f"Open rate B: {result.variant_rate:.2%}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Significant: {result.is_significant}")
```

Output:
```
Open rate A: 25.00%
Open rate B: 27.50%
Lift: +10.0%
Significant: True
```

---

## Example 3: Checkout Flow Test (No Winner)

Testing a simplified checkout flow:

- **Control:** 8,000 visitors, 240 purchases
- **Variant:** 8,000 visitors, 256 purchases

```python
result = conversion.analyze(
    control_visitors=8000,
    control_conversions=240,
    variant_visitors=8000,
    variant_conversions=256,
)

print(f"Lift: {result.lift_percent:+.1f}%")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
print(f"Winner: {result.winner}")
```

Output:
```
Lift: +6.7%
P-value: 0.4281
Significant: False
Winner: no winner yet
```

**Decision:** Not enough evidence. Continue running or accept that variants are equivalent.

---

## Example 4: Planning a New Test

You want to test a new landing page. Your current conversion rate is 4% and you want to detect at least a 15% relative improvement.

```python
plan = conversion.sample_size(
    current_rate=4,       # 4% conversion rate
    lift_percent=15,      # detect 15% lift (4% → 4.6%)
    confidence=95,
    power=80,
)

print(f"Need {plan.visitors_per_variant:,} visitors per variant")
print(f"Total: {plan.total_visitors:,} visitors")

# With 5,000 visitors/day
plan.with_daily_traffic(5000)
print(f"Duration: {plan.test_duration_days} days")
```

Output:
```
Need 15,708 visitors per variant
Total: 31,416 visitors
Duration: 7 days
```

---

## Example 5: Stakeholder Report

Generate a report to share with your team:

```python
result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)

report = conversion.summarize(
    result,
    test_name="Homepage Hero Banner Test"
)
print(report)
```

Output:
```markdown
## 📊 Homepage Hero Banner Test Results

### ✅ Significant Result

**The test variant performed significantly higher than the control.**

- **Control conversion rate:** 5.00% (500 / 10,000)
- **Variant conversion rate:** 6.00% (600 / 10,000)
- **Relative lift:** +20.0% increase
- **P-value:** 0.0003
- **Confidence level:** 95%

### 📝 What This Means

With 95% confidence, the difference is statistically significant.
The p-value of **0.0003** indicates there's only a **0.03%** chance
this result is due to random variation.
The variant shows a **20.0%** improvement over control.
```

---

## Example 6: Confidence Interval

Understand the uncertainty in your conversion rate:

```python
ci = conversion.confidence_interval(
    visitors=5000,
    conversions=250,
    confidence=95,
)

print(f"Conversion rate: {ci.rate:.2%}")
print(f"95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")
print(f"Margin of error: ±{ci.margin_of_error:.2%}")
```

Output:
```
Conversion rate: 5.00%
95% CI: [4.43%, 5.63%]
Margin of error: ±0.60%
```

**Interpretation:** We're 95% confident the true conversion rate is between 4.43% and 5.63%.
