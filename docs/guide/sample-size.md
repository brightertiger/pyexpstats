# Sample Size Calculator

Calculating the right sample size **before** you start a test is crucial. Too few visitors and you won't detect real effects. Too many and you're wasting time.

## Why Sample Size Matters

!!! warning "Don't Skip This Step"
    Running a test without calculating sample size first is the #1 cause of inconclusive results.

A proper sample size calculation ensures:

1. **High enough power** - You'll detect real effects when they exist
2. **Controlled false positive rate** - You won't declare winners that aren't real
3. **Efficient use of traffic** - You won't run tests longer than necessary

## For Conversion Rate Tests

```python
from expstats import conversion

plan = conversion.sample_size(
    current_rate=5,       # Your current conversion rate (5%)
    lift_percent=10,      # Minimum lift you want to detect (10%)
    confidence=95,        # Confidence level (default: 95%)
    power=80,             # Statistical power (default: 80%)
)

print(f"Visitors per variant: {plan.visitors_per_variant:,}")
print(f"Total visitors: {plan.total_visitors:,}")
```

### Understanding the Parameters

| Parameter | What It Means | Typical Values |
|-----------|---------------|----------------|
| `current_rate` | Your baseline conversion rate | 1-10% for most sites |
| `lift_percent` | Smallest improvement worth detecting | 5-20% relative lift |
| `confidence` | How sure you want to be (avoids false positives) | 95% (standard) |
| `power` | Chance of detecting a real effect | 80% (standard) |

### Estimating Test Duration

Add your daily traffic to get a duration estimate:

```python
plan.with_daily_traffic(10000)  # 10k visitors/day
print(f"Test duration: {plan.test_duration_days} days")
```

!!! tip "Run for at least 1-2 weeks"
    Even if you reach sample size sooner, run for at least a week to capture day-of-week effects.

## For Revenue / Numeric Tests

```python
from expstats import magnitude

plan = magnitude.sample_size(
    current_mean=50,      # Current average order value ($50)
    current_std=25,       # Standard deviation ($25)
    lift_percent=5,       # Minimum lift you want to detect (5%)
)

print(f"Visitors per variant: {plan.visitors_per_variant:,}")
```

### Getting Standard Deviation

Don't know your standard deviation? Here's how to estimate it:

```sql
-- SQL example
SELECT STDDEV(order_value) FROM orders WHERE date > '2024-01-01';
```

Or use this rule of thumb:

- For revenue: std is typically 50-100% of the mean
- For time metrics: std is typically 100-200% of the mean

## For Multi-Variant Tests

Testing 3+ variants requires more sample size:

```python
plan = conversion.sample_size(
    current_rate=5,
    lift_percent=10,
    num_variants=3,  # Control + 2 variants
)

print(f"Per variant: {plan.visitors_per_variant:,}")
print(f"Total: {plan.total_visitors:,}")  # ~50% more than 2-variant
```

## Sample Size Trade-offs

| If You Want To... | You Need... |
|-------------------|-------------|
| Detect smaller effects | More visitors |
| Higher confidence (99% vs 95%) | More visitors |
| Higher power (90% vs 80%) | More visitors |
| Test more variants | More visitors per variant |

## Generating a Report

Create a stakeholder-friendly plan:

```python
report = conversion.summarize_plan(
    plan, 
    test_name="Homepage CTA Test"
)
print(report)
```

Output:
```markdown
## 📋 Homepage CTA Test Sample Size Plan

### Test Parameters

- **Current conversion rate:** 5.00%
- **Minimum detectable lift:** +10%
- **Expected variant rate:** 5.50%
- **Confidence level:** 95%
- **Statistical power:** 80%

### Required Sample Size

- **Per variant:** 31,234 visitors
- **Total:** 62,468 visitors

### 📝 What This Means

If the variant truly improves conversion by 10% or more,
this test has an 80% chance of detecting it.
```
