<p align="center">
  <img src="static/logo.png" alt="pyexpstats - Python A/B Testing and Experiment Analysis Library" width="400">
</p>

<h1 align="center">pyexpstats</h1>

<p align="center">
  <strong>A/B Testing Calculator & Statistical Significance Analysis for Python</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/pyexpstats/"><img src="https://img.shields.io/pypi/v/pyexpstats.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/pyexpstats/"><img src="https://img.shields.io/pypi/pyversions/pyexpstats.svg" alt="Python versions"></a>
  <a href="https://github.com/ujjwal-ibm/pyexpstats/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://pyexpstats.vercel.app"><strong>🚀 Try the Live Calculator → pyexpstats.vercel.app</strong></a>
</p>

---

## What is pyexpstats?

**pyexpstats** is a Python library and web-based A/B testing calculator for experiment analysis, sample size calculation, and statistical significance testing. Whether you're running conversion rate optimization (CRO) experiments, analyzing split tests, or calculating statistical power, pyexpstats provides the tools you need.

### Key Features

- **A/B Test Significance Calculator** — Analyze experiments with Z-tests, t-tests, and chi-square tests
- **Sample Size Calculator** — Plan experiments with proper statistical power (80%, 90%, etc.)
- **Multi-Variant Testing (A/B/n)** — Compare multiple variants with automatic Bonferroni correction
- **Conversion Rate Analysis** — Binary outcome testing for signups, purchases, clicks
- **Revenue & Magnitude Testing** — Continuous metrics like AOV, time on site, order value
- **Survival Analysis** — Time-to-event analysis with Kaplan-Meier curves and log-rank tests
- **Difference-in-Differences** — Causal inference for quasi-experimental designs
- **Confidence Intervals** — Visualize uncertainty in your experiment results
- **Stakeholder Reports** — Generate plain-language markdown summaries

---

## Live Demo — Free Online A/B Test Calculator

No installation needed! Use our **free online A/B testing calculator** at:

### **[pyexpstats.vercel.app](https://pyexpstats.vercel.app)**

<p align="center">
  <img src="static/interface.png" alt="A/B Test Calculator - Sample Size and Statistical Significance Calculator Interface" width="700">
</p>

Calculate sample sizes, analyze experiment results, and determine statistical significance — all in your browser.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Conversion Effects](#-conversion-effects--whether-it-happens) — Binary outcomes (signup, purchase, click)
- [Magnitude Effects](#-magnitude-effects--how-much-it-happens) — Continuous metrics (revenue, time)
- [Timing Effects](#️-timing-effects--when-it-happens) — Survival analysis, event rates
- [Sequential Testing](#-sequential-testing) — Early stopping with valid statistics
- [Bayesian A/B Testing](#-bayesian-ab-testing) — Probability-based decisions
- [Diagnostics](#-diagnostics) — SRM detection, test health, novelty effects
- [Planning](#-planning) — MDE calculator, duration recommendations
- [Business Impact](#-business-impact) — Revenue projections, guardrails
- [Segment Analysis](#-segment-analysis) — Analyze effects by user segment
- [Generate Reports](#-generate-stakeholder-reports)
- [Web Interface](#-web-interface)
- [API Reference](#api-reference)
- [Understanding Results](#understanding-results) — P-values, confidence intervals explained
- [Best Practices](#best-practices)
- [License](#license)

---

## Why pyexpstats?

| Traditional Tools | pyexpstats |
|-------------------|-----------|
| "Which statistical test?" | "What changed in user behavior?" |
| Test-centric | Effect-centric |
| Complex statistics | Plain-language results |

pyexpstats models experimental impact across three fundamental **outcome dimensions**:

| Effect Type | Question Answered | Examples |
|-------------|-------------------|----------|
| **Conversion** | *Whether* something happens | Signup, purchase, click, trial start |
| **Magnitude** | *How much* it happens | Revenue, time spent, order value |
| **Timing** | *When* it happens | Time to purchase, time to churn |

---

## Installation

```bash
pip install pyexpstats
```

**Requirements:** Python 3.8+

---

## Quick Start

```python
from pyexpstats import conversion, magnitude, timing

# Conversion: Did the treatment change whether users purchase?
result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)
print(f"Conversion lift: {result.lift_percent:+.1f}%")

# Magnitude: Did the treatment change how much users spend?
result = magnitude.analyze(
    control_visitors=5000,
    control_mean=50.00,
    control_std=25.00,
    variant_visitors=5000,
    variant_mean=52.50,
    variant_std=25.00,
)
print(f"Revenue lift: ${result.lift_absolute:+.2f}")

# Timing: Did the treatment change when users convert?
result = timing.analyze(
    control_times=[5, 8, 12, 15, 20],
    control_events=[1, 1, 1, 0, 1],
    treatment_times=[3, 6, 9, 12, 16],
    treatment_events=[1, 1, 1, 1, 1],
)
print(f"Hazard ratio: {result.hazard_ratio:.2f}")
```

---

## 📊 Conversion Effects — *Whether* it happens

Use for **binary outcomes**: did the user convert or not? Perfect for analyzing signup rates, purchase rates, click-through rates, and trial conversions.

### Analyze an A/B Test

```python
from pyexpstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,      # 5.0% conversion
    variant_visitors=10000,
    variant_conversions=600,      # 6.0% conversion
)

print(f"Control: {result.control_rate:.2%}")
print(f"Variant: {result.variant_rate:.2%}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Significant: {result.is_significant}")
print(f"Winner: {result.winner}")
```

### Calculate Sample Size for A/B Test

How many visitors do you need to detect a statistically significant difference?

```python
plan = conversion.sample_size(
    current_rate=5,       # 5% baseline conversion rate
    lift_percent=10,      # detect 10% relative lift
    confidence=95,        # 95% confidence level
    power=80,             # 80% statistical power
)

print(f"Need {plan.visitors_per_variant:,} per variant")
plan.with_daily_traffic(10000)
print(f"Duration: {plan.test_duration_days} days")
```

### Multi-Variant Tests (A/B/n Testing with Chi-Square)

```python
result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 550},
        {"name": "variant_b", "visitors": 10000, "conversions": 600},
    ]
)

print(f"Best: {result.best_variant}")
print(f"P-value: {result.p_value:.4f}")
```

**Note:** Variant names must be unique. Duplicate names will raise a `ValueError`.

### Difference-in-Differences (Causal Inference)

```python
result = conversion.diff_in_diff(
    control_pre_visitors=5000, control_pre_conversions=250,
    control_post_visitors=5000, control_post_conversions=275,
    treatment_pre_visitors=5000, treatment_pre_conversions=250,
    treatment_post_visitors=5000, treatment_post_conversions=350,
)

print(f"DiD effect: {result.diff_in_diff:+.2%}")
```

---

## 📈 Magnitude Effects — *How much* it happens

Use for **continuous metrics**: revenue per user, average order value, time on site, pages per session.

### Analyze Revenue or Continuous Metrics

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

print(f"Control: ${result.control_mean:.2f}")
print(f"Variant: ${result.variant_mean:.2f}")
print(f"Lift: ${result.lift_absolute:+.2f} ({result.lift_percent:+.1f}%)")
print(f"Significant: {result.is_significant}")
```

### Sample Size for Revenue Tests

```python
plan = magnitude.sample_size(
    current_mean=50,      # $50 average order value
    current_std=25,       # $25 standard deviation
    lift_percent=5,       # detect 5% lift in AOV
)

print(f"Need {plan.visitors_per_variant:,} per variant")
```

### Multi-Variant Tests (ANOVA)

```python
result = magnitude.analyze_multi(
    variants=[
        {"name": "control", "visitors": 1000, "mean": 50, "std": 25},
        {"name": "new_layout", "visitors": 1000, "mean": 52, "std": 25},
        {"name": "premium_upsell", "visitors": 1000, "mean": 55, "std": 25},
    ]
)

print(f"Best: {result.best_variant}")
print(f"F-statistic: {result.f_statistic:.2f}")
```

**Note:** Variant names must be unique. Duplicate names will raise a `ValueError`.

### Difference-in-Differences

```python
result = magnitude.diff_in_diff(
    control_pre_n=1000, control_pre_mean=50, control_pre_std=25,
    control_post_n=1000, control_post_mean=51, control_post_std=25,
    treatment_pre_n=1000, treatment_pre_mean=50, treatment_pre_std=25,
    treatment_post_n=1000, treatment_post_mean=55, treatment_post_std=26,
)

print(f"DiD effect: ${result.diff_in_diff:+.2f}")
```

---

## ⏱️ Timing Effects — *When* it happens

Use for **time-to-event analysis**: time to purchase, time to churn, subscription duration, support ticket rates.

### Survival Analysis (Log-Rank Test)

```python
from pyexpstats import timing

result = timing.analyze(
    control_times=[5, 8, 12, 15, 18, 22, 25, 30],
    control_events=[1, 1, 1, 0, 1, 1, 0, 1],      # 1=event, 0=censored
    treatment_times=[3, 6, 9, 12, 14, 16, 20, 24],
    treatment_events=[1, 1, 1, 1, 0, 1, 1, 1],
)

print(f"Control median time: {result.control_median_time}")
print(f"Treatment median time: {result.treatment_median_time}")
print(f"Hazard ratio: {result.hazard_ratio:.3f}")
print(f"Time saved: {result.time_saved:.1f} ({result.time_saved_percent:.1f}%)")
print(f"Significant: {result.is_significant}")
```

### Kaplan-Meier Survival Curves

```python
curve = timing.survival_curve(
    times=[5, 10, 15, 20, 25, 30],
    events=[1, 1, 0, 1, 1, 0],
    confidence=95,
)

print(f"Median survival time: {curve.median_time}")
print(f"Survival probabilities: {curve.survival_probabilities}")
```

### Event Rate Analysis (Poisson Test)

Compare event rates between groups (e.g., support tickets per day, errors per hour):

```python
result = timing.analyze_rates(
    control_events=45,
    control_exposure=100,      # 100 days of observation
    treatment_events=38,
    treatment_exposure=100,
)

print(f"Control rate: {result.control_rate:.4f} events/day")
print(f"Treatment rate: {result.treatment_rate:.4f} events/day")
print(f"Rate ratio: {result.rate_ratio:.3f}")
print(f"Rate change: {result.rate_difference_percent:+.1f}%")
print(f"Significant: {result.is_significant}")
```

### Sample Size for Survival Studies

```python
plan = timing.sample_size(
    control_median=30,        # Expected median for control
    treatment_median=24,      # Expected median for treatment
    confidence=95,
    power=80,
    dropout_rate=0.1,         # 10% expected dropout
)

print(f"Need {plan.subjects_per_group:,} per group")
print(f"Expected events: {plan.total_expected_events:,}")
```

---

## 🔄 Sequential Testing

Stop your A/B tests early with valid statistics using Sequential Probability Ratio Test (SPRT) with O'Brien-Fleming boundaries.

### Check If You Can Stop Early

```python
from pyexpstats.methods import sequential

result = sequential.analyze(
    control_visitors=2500,
    control_conversions=125,
    variant_visitors=2500,
    variant_conversions=175,
    expected_visitors_per_variant=5000,  # Your planned sample size
)

print(f"Can stop: {result.can_stop}")
print(f"Decision: {result.decision}")  # 'variant_wins', 'control_wins', 'no_difference', 'keep_running'
print(f"Progress: {result.information_fraction:.0%} through test")
print(f"Confidence: {result.confidence_variant_better:.1f}%")
```

**Why Sequential Testing?**

- **No peeking penalty** — Check results as often as you want without inflating false positives
- **Stop early for clear winners** — Save time and traffic when effects are obvious
- **Valid confidence intervals** — Always maintain proper statistical guarantees

---

## 🎲 Bayesian A/B Testing

Get intuitive probability-based results instead of confusing p-values.

### Bayesian Analysis

```python
from pyexpstats.methods import bayesian

result = bayesian.analyze(
    control_visitors=1000,
    control_conversions=50,
    variant_visitors=1000,
    variant_conversions=65,
)

print(f"Probability variant is better: {result.probability_variant_better:.1f}%")
print(f"Expected loss if choosing variant: {result.expected_loss_choosing_variant:.4f}")
print(f"Lift credible interval: {result.lift_credible_interval}")
print(f"Winner: {result.winner}")
```

**Why Bayesian Testing?**

- **Intuitive results** — "94% probability variant is better" vs "p < 0.05"
- **No fixed sample size** — Can check results anytime
- **Risk quantification** — Expected loss tells you the cost of being wrong
- **Credible intervals** — Direct probability statements about the true effect

---

## 🔍 Diagnostics

Validate your A/B test before trusting the results.

### Sample Ratio Mismatch (SRM) Detection

SRM indicates bugs in your experiment setup that can invalidate results:

```python
from pyexpstats.diagnostics import check_sample_ratio

result = check_sample_ratio(
    control_visitors=10500,
    variant_visitors=9500,
    expected_ratio=0.5,  # Expected 50/50 split
)

print(f"Valid: {result.is_valid}")
print(f"Severity: {result.severity}")  # 'ok', 'warning', 'critical'
print(f"Deviation: {result.deviation_percent:.1f}%")
```

### Test Health Dashboard

Comprehensive health check for your experiment:

```python
from pyexpstats.diagnostics import check_health

health = check_health(
    control_visitors=5000,
    control_conversions=250,
    variant_visitors=5000,
    variant_conversions=275,
)

print(f"Status: {health.overall_status}")  # 'healthy', 'warning', 'unhealthy'
print(f"Score: {health.score}/100")
print(f"Can trust results: {health.can_trust_results}")

for check in health.checks:
    print(f"  {check.name}: {check.status}")
```

### Novelty Effect Detection

Detect if your experiment effect is fading over time:

```python
from pyexpstats.diagnostics import detect_novelty_effect

daily_results = [
    {"day": 1, "control_visitors": 1000, "control_conversions": 50,
     "variant_visitors": 1000, "variant_conversions": 70},
    {"day": 2, "control_visitors": 1000, "control_conversions": 50,
     "variant_visitors": 1000, "variant_conversions": 65},
    # ... more days
]

result = detect_novelty_effect(daily_results)

print(f"Effect type: {result.effect_type}")  # 'novelty', 'primacy', 'stable'
print(f"Initial lift: {result.initial_lift:+.1f}%")
print(f"Current lift: {result.current_lift:+.1f}%")
if result.projected_steady_state_lift:
    print(f"Projected steady state: {result.projected_steady_state_lift:+.1f}%")
```

---

## 📐 Planning

Plan your A/B tests before running them.

### Minimum Detectable Effect (MDE) Calculator

Understand what effects you can detect with your traffic:

```python
from pyexpstats.planning import minimum_detectable_effect

result = minimum_detectable_effect(
    daily_traffic=5000,
    test_duration_days=14,
    baseline_rate=0.05,
)

print(f"MDE: {result.minimum_detectable_effect:.1f}% lift")
print(f"Can detect variant rate: {result.detectable_variant_rate:.2%}")
print(f"Is practically useful: {result.is_practically_useful}")
```

### Duration Recommendations

Get recommendations for how long to run your test:

```python
from pyexpstats.planning import recommend_duration

result = recommend_duration(
    baseline_rate=0.05,
    minimum_detectable_effect=0.10,  # 10% lift
    daily_traffic=5000,
    business_type="ecommerce",
)

print(f"Recommended: {result.recommended_days} days")
print(f"Minimum: {result.minimum_days} days")
print(f"Ideal: {result.ideal_days} days")
print(f"Sample needed: {result.required_sample_per_variant:,} per variant")
```

---

## 💰 Business Impact

Translate A/B test results into business value.

### Revenue Impact Projections

```python
from pyexpstats.business import project_impact

projection = project_impact(
    control_rate=0.05,
    variant_rate=0.055,
    lift_percent=10.0,
    lift_ci_lower=2.0,
    lift_ci_upper=18.0,
    monthly_visitors=100000,
    revenue_per_conversion=50.0,
)

print(f"Monthly revenue lift: ${projection.monthly_revenue_lift:,.0f}")
print(f"Annual revenue lift: ${projection.annual_revenue_lift:,.0f}")
print(f"Probability of positive impact: {projection.probability_positive_impact:.1%}")
```

### Guardrail Metrics

Monitor metrics you want to protect during experiments:

```python
from pyexpstats.business import check_guardrails

report = check_guardrails([
    {
        "name": "Page Load Time",
        "metric_type": "mean",
        "direction": "increase_is_bad",
        "threshold_percent": 10,
        "control_data": [100, 110, 95, 105] * 100,
        "variant_data": [105, 115, 100, 108] * 100,
    },
    {
        "name": "Error Rate",
        "metric_type": "proportion",
        "direction": "increase_is_bad",
        "threshold_percent": 20,
        "control_data": {"count": 50, "total": 10000},
        "variant_data": {"count": 55, "total": 10000},
    },
])

print(f"Can ship: {report.can_ship}")
print(f"Passed: {report.passed}")
print(f"Warnings: {report.warnings}")
print(f"Failures: {report.failures}")
```

---

## 📊 Segment Analysis

Analyze how your A/B test performs across different user segments.

### Analyze by Segment

```python
from pyexpstats.segments import analyze_segments

report = analyze_segments([
    {
        "segment_name": "device",
        "segment_value": "mobile",
        "control_visitors": 5000,
        "control_conversions": 250,
        "variant_visitors": 5000,
        "variant_conversions": 350,
    },
    {
        "segment_name": "device",
        "segment_value": "desktop",
        "control_visitors": 3000,
        "control_conversions": 180,
        "variant_visitors": 3000,
        "variant_conversions": 190,
    },
])

print(f"Overall lift: {report.overall_lift:+.1f}%")
print(f"Best segment: {report.best_segment}")
print(f"Heterogeneity detected: {report.heterogeneity_detected}")
print(f"Simpson's paradox risk: {report.simpsons_paradox_risk}")

for segment in report.segments:
    print(f"  {segment.segment_value}: {segment.lift_percent:+.1f}% (sig: {segment.is_significant})")
```

**Features:**

- **Bonferroni/Holm correction** — Automatic correction for multiple comparisons
- **Heterogeneity detection** — Find when effects vary significantly by segment
- **Simpson's Paradox warnings** — Detect when overall results mislead

---

## 📋 Generate Stakeholder Reports

Every effect type includes `summarize()` to generate plain-language markdown reports for stakeholders:

```python
result = conversion.analyze(...)
report = conversion.summarize(result, test_name="Signup Button Test")
print(report)
```

Output:

```markdown
## 📊 Signup Button Test Results

### ✅ Significant Result

**The test variant performed significantly higher than the control.**

- **Control conversion rate:** 5.00% (500 / 10,000)
- **Variant conversion rate:** 6.00% (600 / 10,000)
- **Relative lift:** +20.0% increase
- **P-value:** 0.0003

### 📝 What This Means

With 95% confidence, the variant shows a **20.0%** improvement.
```

---

## 🌐 Web Interface

pyexpstats includes a beautiful web UI for interactive experiment analysis:

```bash
pyexpstats-server
# Open http://localhost:8000
```

Or use the hosted version at **[pyexpstats.vercel.app](https://pyexpstats.vercel.app)**

### Configuration

Configure the API server using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed origins |

For production, set appropriate CORS origins:

```bash
CORS_ORIGINS="https://yourdomain.com" pyexpstats-server
```

### Web Calculator Features

| Tool | Description |
|------|-------------|
| **Sample Size Calculator** | Plan A/B tests with proper statistical power |
| **A/B Test Significance Calculator** | Analyze 2-variant and multi-variant experiments |
| **Timing & Rate Analysis** | Survival analysis and Poisson rate comparisons |
| **Diff-in-Diff Calculator** | Quasi-experimental causal inference |
| **Confidence Interval Calculator** | Estimate precision of your metrics |

The web interface includes:

- **Visual metric type selection** with examples (Conversion Rate vs Revenue)
- **Helpful hints** explaining statistical concepts
- **Plain-language interpretations** of p-values and confidence intervals
- **Multi-variant testing** with automatic Bonferroni correction
- **Interactive visualizations** of experiment results

---

## API Reference

### conversion module

| Function | Purpose |
|----------|---------|
| `sample_size(current_rate, lift_percent, ...)` | Sample size calculation for conversion tests |
| `analyze(control_visitors, control_conversions, ...)` | 2-variant A/B test (Z-test) |
| `analyze_multi(variants, ...)` | Multi-variant test (Chi-square) |
| `diff_in_diff(...)` | Difference-in-Differences analysis |
| `confidence_interval(visitors, conversions, ...)` | Confidence interval for a conversion rate |
| `summarize(result, test_name)` | Generate markdown report |

### magnitude module

| Function | Purpose |
|----------|---------|
| `sample_size(current_mean, current_std, lift_percent, ...)` | Sample size for continuous metrics |
| `analyze(control_visitors, control_mean, control_std, ...)` | 2-variant test (Welch's t-test) |
| `analyze_multi(variants, ...)` | Multi-variant test (ANOVA) |
| `diff_in_diff(...)` | Difference-in-Differences analysis |
| `confidence_interval(visitors, mean, std, ...)` | Confidence interval for a mean |
| `summarize(result, test_name, metric_name, currency)` | Generate markdown report |

### timing module

| Function | Purpose |
|----------|---------|
| `analyze(control_times, control_events, ...)` | Survival analysis (log-rank test) |
| `survival_curve(times, events, ...)` | Kaplan-Meier survival curve |
| `analyze_rates(control_events, control_exposure, ...)` | Poisson rate comparison |
| `sample_size(control_median, treatment_median, ...)` | Sample size for survival studies |
| `summarize(result, test_name)` | Generate markdown report |
| `summarize_rates(result, test_name, unit)` | Rate analysis report |

### methods.sequential module

| Function | Purpose |
|----------|---------|
| `analyze(control_visitors, control_conversions, ..., expected_visitors_per_variant)` | Sequential test with early stopping |
| `summarize(result)` | Generate markdown report |

### methods.bayesian module

| Function | Purpose |
|----------|---------|
| `analyze(control_visitors, control_conversions, ...)` | Bayesian A/B test analysis |
| `summarize(result)` | Generate markdown report |

### diagnostics module

| Function | Purpose |
|----------|---------|
| `check_sample_ratio(control_visitors, variant_visitors, ...)` | SRM detection |
| `check_health(control_visitors, control_conversions, ...)` | Comprehensive test health check |
| `detect_novelty_effect(daily_results, ...)` | Detect fading/growing effects |

### planning module

| Function | Purpose |
|----------|---------|
| `minimum_detectable_effect(sample_size_per_variant, ...)` | Calculate MDE |
| `recommend_duration(baseline_rate, minimum_detectable_effect, daily_traffic, ...)` | Duration recommendations |

### business module

| Function | Purpose |
|----------|---------|
| `project_impact(control_rate, variant_rate, lift_percent, ...)` | Revenue impact projection |
| `check_guardrails(guardrails)` | Monitor guardrail metrics |

### segments module

| Function | Purpose |
|----------|---------|
| `analyze_segments(segments_data, ...)` | Segment-level analysis with correction |

---

## Module Structure

```
pyexpstats/
  effects/
    outcome/
      conversion.py    # Binary outcomes (signup, purchase, click)
      magnitude.py     # Continuous metrics (revenue, time, value)
      timing.py        # Time-to-event (survival, rates)
  methods/
    sequential.py      # Sequential testing with early stopping
    bayesian.py        # Bayesian A/B testing
  diagnostics/
    srm.py             # Sample Ratio Mismatch detection
    health.py          # Test health dashboard
    novelty.py         # Novelty effect detection
  planning/
    mde.py             # Minimum Detectable Effect calculator
    duration.py        # Test duration recommendations
  business/
    impact.py          # Revenue impact projections
    guardrails.py      # Guardrail metrics monitoring
  segments/
    analysis.py        # Segment-level analysis
```

---

## Understanding Results

### P-Values Explained

| P-value | Interpretation |
|---------|----------------|
| < 0.01 | Very strong evidence (highly significant) |
| 0.01 - 0.05 | Strong evidence (statistically significant at 95%) |
| 0.05 - 0.10 | Weak evidence (marginally significant) |
| > 0.10 | Not enough evidence (not significant) |

### Confidence Intervals

A 95% confidence interval means: if you ran this experiment 100 times, about 95 of those intervals would contain the true effect.

### Hazard Ratios (Survival Analysis)

| Hazard Ratio | Interpretation |
|--------------|----------------|
| HR < 1 | Treatment slows events (protective effect) |
| HR = 1 | No effect on timing |
| HR > 1 | Treatment speeds up events |

### Rate Ratios (Poisson)

| Rate Ratio | Interpretation |
|------------|----------------|
| RR < 1 | Treatment reduces event rate |
| RR = 1 | No effect on rate |
| RR > 1 | Treatment increases event rate |

---

## Best Practices for A/B Testing

1. **Calculate sample size BEFORE starting** — Don't peek and stop early (p-hacking)
2. **Run for at least 1-2 full weeks** — Capture day-of-week and seasonal patterns
3. **Look at confidence intervals** — Not just p-values
4. **Statistical significance ≠ business significance** — A 0.1% lift might be "significant" but not worth implementing
5. **Use Bonferroni correction** — For multi-variant tests (automatic in `analyze_multi`)
6. **Consider timing effects** — A treatment might speed up conversion without changing the overall rate

---

## Use Cases

pyexpstats is used for:

- **Conversion Rate Optimization (CRO)** — Optimize landing pages, signup flows, checkout
- **Product Experimentation** — Test new features, UI changes, pricing
- **Growth Hacking** — Validate acquisition and retention strategies
- **Marketing Analytics** — Email campaigns, ad creative testing
- **E-commerce Optimization** — Product recommendations, pricing tests
- **SaaS Metrics** — Trial conversion, churn reduction, upsell tests

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

MIT License — free for commercial and personal use.

---

## Credits

Inspired by [Evan Miller's A/B Testing Tools](https://www.evanmiller.org/ab-testing/).

---

## Keywords

A/B testing, split testing, experiment analysis, statistical significance calculator, sample size calculator, conversion rate optimization, CRO, hypothesis testing, p-value calculator, confidence interval, statistical power, experiment design, product analytics, growth hacking, chi-square test, t-test, Z-test, ANOVA, survival analysis, Kaplan-Meier, log-rank test, Poisson test, difference-in-differences, causal inference, Python statistics, web analytics, marketing analytics, experimentation platform.
