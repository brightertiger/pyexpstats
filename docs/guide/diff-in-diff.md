# Difference-in-Differences (DiD)

Difference-in-Differences is a statistical technique used to estimate causal effects in quasi-experimental designs. It's particularly useful when randomization isn't possible.

## When to Use DiD

✅ **Good use cases:**

- Policy changes that affect some regions/groups but not others
- Feature rollouts to specific user segments
- Natural experiments (e.g., regulatory changes)
- Historical data analysis where you can't randomize

❌ **Not appropriate when:**

- You can run a proper randomized A/B test
- The "parallel trends" assumption is clearly violated
- There's no good control group

## The DiD Formula

The DiD estimator removes time trends that affect both groups:

```
DiD = (Treatment_post - Treatment_pre) - (Control_post - Control_pre)
```

This isolates the treatment effect by subtracting out the natural trend observed in the control group.

## Conversion Rate DiD

### Basic Example

```python
from pyexpstats import conversion

# You launched a new feature to West Coast users
# East Coast users serve as the control group

result = conversion.diff_in_diff(
    # Control (East Coast) - no feature
    control_pre_visitors=10000,
    control_pre_conversions=500,     # 5% before
    control_post_visitors=10000,
    control_post_conversions=525,    # 5.25% after (natural trend)
    
    # Treatment (West Coast) - got the feature
    treatment_pre_visitors=10000,
    treatment_pre_conversions=500,   # 5% before
    treatment_post_visitors=10000,
    treatment_post_conversions=650,  # 6.5% after
)

print(f"Control change: {result.control_change:+.2%}")
print(f"Treatment change: {result.treatment_change:+.2%}")
print(f"DiD effect: {result.diff_in_diff:+.2%}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
```

Output:
```
Control change: +0.25%
Treatment change: +1.50%
DiD effect: +1.25%
P-value: 0.0012
Significant: True
```

### Interpreting Results

The DiD effect (+1.25%) represents the causal impact of the treatment:

- Treatment group improved by 1.50%
- Control group improved by 0.25% (natural trend)
- Net treatment effect: 1.50% - 0.25% = 1.25%

Without DiD, you might have claimed a 1.50% improvement, but 0.25% of that was just a natural trend!

## Revenue/Numeric DiD

### Basic Example

```python
from pyexpstats import magnitude

# Testing a premium checkout experience
# Rolled out to "Gold" tier customers first

result = magnitude.diff_in_diff(
    # Control (Silver customers) - standard checkout
    control_pre_n=2000,
    control_pre_mean=75.00,
    control_pre_std=30.00,
    control_post_n=2000,
    control_post_mean=77.00,      # $2 natural increase
    control_post_std=32.00,
    
    # Treatment (Gold customers) - premium checkout
    treatment_pre_n=1500,
    treatment_pre_mean=120.00,
    treatment_pre_std=45.00,
    treatment_post_n=1500,
    treatment_post_mean=130.00,   # $10 increase
    treatment_post_std=48.00,
)

print(f"Control change: ${result.control_change:+.2f}")
print(f"Treatment change: ${result.treatment_change:+.2f}")
print(f"DiD effect: ${result.diff_in_diff:+.2f}")
print(f"Significant: {result.is_significant}")
```

Output:
```
Control change: +$2.00
Treatment change: +$10.00
DiD effect: +$8.00
Significant: True
```

## Generating Reports

### Conversion Rate Report

```python
report = conversion.summarize_diff_in_diff(
    result,
    test_name="West Coast Feature Launch"
)
print(report)
```

Output:
```markdown
## 📊 West Coast Feature Launch

### ✅ Significant Treatment Effect

**The treatment caused a significant increase in conversion rate.**

### Conversion Rates

| Group | Pre-Period | Post-Period | Change |
|-------|------------|-------------|--------|
| Control | 5.00% | 5.25% | +0.25% |
| Treatment | 5.00% | 6.50% | +1.50% |

### Difference-in-Differences Estimate

- **DiD Effect:** +1.25% (+25.0% relative)
- **95% CI:** [0.52%, 1.98%]
- **Z-statistic:** 3.35
- **P-value:** 0.0008
- **Confidence level:** 95%

### 📝 What This Means

The treatment group's conversion rate changed by **+1.50%**
while the control group changed by **+0.25%**.
After accounting for the control group's trend, the treatment effect is **+1.25%**.
This effect is statistically significant at the 95% confidence level.
```

### Revenue Report

```python
report = magnitude.summarize_diff_in_diff(
    result,
    test_name="Premium Checkout Analysis",
    metric_name="Average Order Value",
    currency="$"
)
print(report)
```

## The Parallel Trends Assumption

!!! warning "Critical Assumption"
    DiD assumes that without the treatment, both groups would have followed similar trends. This is called the "parallel trends" assumption.

### Checking Parallel Trends

Before applying DiD, verify that:

1. **Historical trends are similar**: Plot both groups' metrics over time before the treatment
2. **No anticipation effects**: The treatment group didn't change behavior before the treatment started
3. **No contamination**: Control group wasn't affected by the treatment spillover

### What Violates Parallel Trends

- **Seasonality differences**: One region has different seasonal patterns
- **Selection bias**: Treatment group was chosen because they were already improving
- **Confounding events**: Something else happened to one group at the same time

## Best Practices

1. **Collect enough pre-period data** - Multiple time points help validate parallel trends
2. **Choose a similar control group** - The more similar, the better
3. **Check for spillover effects** - Make sure control isn't affected by treatment
4. **Report confidence intervals** - They show the uncertainty in your estimate
5. **Consider placebo tests** - Apply DiD to periods before treatment as a sanity check

## Limitations

1. **Cannot prove causation** - DiD is correlational; parallel trends may not hold
2. **Sensitive to timing** - Results can vary based on when you measure
3. **Assumes linear trends** - Non-linear dynamics may bias estimates
4. **Requires good control group** - Hard to find in practice

## When DiD Beats A/B Testing

| Scenario | Use DiD | Use A/B Test |
|----------|---------|--------------|
| Can randomize | ❌ | ✅ |
| Policy/regulation change | ✅ | ❌ |
| Historical analysis | ✅ | ❌ |
| Feature rollout with holdout | ✅ | ✅ |
| Need causal certainty | ❌ | ✅ |
