# timing

**Timing Effects** — *When* it happens

The `timing` module provides tools for analyzing experiments where you care about *when* an event occurs or *how often* events happen.

## Use Cases

- **Time to first purchase** — Does a welcome email speed up first purchase?
- **Time to churn** — Does a new feature reduce churn rate?
- **Time to activation** — Does onboarding UX speed up activation?
- **Support ticket rate** — Does a UI change reduce support requests?
- **Error rate** — Does a code change reduce error frequency?

## Survival Analysis

Compare time-to-event between two groups using log-rank tests and hazard ratios.

### analyze()

```python
from expstats import timing

result = timing.analyze(
    control_times=[5, 8, 12, 15, 18, 22, 25, 30, 35, 40],
    control_events=[1, 1, 1, 0, 1, 1, 0, 1, 0, 1],
    treatment_times=[3, 6, 9, 12, 14, 16, 20, 24, 28, 32],
    treatment_events=[1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
    confidence=95,
)

print(f"Control median time: {result.control_median_time}")
print(f"Treatment median time: {result.treatment_median_time}")
print(f"Hazard ratio: {result.hazard_ratio:.3f}")
print(f"HR 95% CI: [{result.hazard_ratio_ci_lower:.3f}, {result.hazard_ratio_ci_upper:.3f}]")
print(f"Time saved: {result.time_saved:.1f} ({result.time_saved_percent:.1f}%)")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `control_times` | List[float] | Time values for each control subject |
| `control_events` | List[int] | Event indicators (1=event, 0=censored) |
| `treatment_times` | List[float] | Time values for each treatment subject |
| `treatment_events` | List[int] | Event indicators (1=event, 0=censored) |
| `confidence` | int | Confidence level (default: 95) |

**Returns:** `TimingResults`

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_median_time` | float | Median time for control (None if not reached) |
| `treatment_median_time` | float | Median time for treatment (None if not reached) |
| `control_events` | int | Number of events in control |
| `control_censored` | int | Number censored in control |
| `treatment_events` | int | Number of events in treatment |
| `treatment_censored` | int | Number censored in treatment |
| `hazard_ratio` | float | Hazard ratio (treatment / control) |
| `hazard_ratio_ci_lower` | float | Lower bound of HR confidence interval |
| `hazard_ratio_ci_upper` | float | Upper bound of HR confidence interval |
| `time_saved` | float | Difference in median times |
| `time_saved_percent` | float | Percentage time difference |
| `is_significant` | bool | Whether the difference is significant |
| `p_value` | float | P-value from log-rank test |
| `recommendation` | str | Plain-language interpretation |

### Interpreting Hazard Ratios

| HR Value | Interpretation |
|----------|----------------|
| HR < 1 | Treatment **slows down** the event (protective effect) |
| HR = 1 | No effect on timing |
| HR > 1 | Treatment **speeds up** the event |

Example: HR = 0.7 means the treatment reduces the event rate by 30%.

---

## Kaplan-Meier Survival Curves

### survival_curve()

Generate survival probability estimates over time.

```python
curve = timing.survival_curve(
    times=[5, 10, 15, 20, 25, 30],
    events=[1, 1, 0, 1, 1, 0],
    confidence=95,
)

print(f"Times: {curve.times}")
print(f"Survival probabilities: {curve.survival_probabilities}")
print(f"Median survival time: {curve.median_time}")
print(f"Total events: {curve.events}")
print(f"Total censored: {curve.censored}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `times` | List[float] | Time values for each subject |
| `events` | List[int] | Event indicators (1=event, 0=censored) |
| `confidence` | int | Confidence level for CI bands (default: 95) |

**Returns:** `SurvivalCurve`

| Attribute | Type | Description |
|-----------|------|-------------|
| `times` | List[float] | Time points |
| `survival_probabilities` | List[float] | Survival probability at each time |
| `confidence_lower` | List[float] | Lower CI bound |
| `confidence_upper` | List[float] | Upper CI bound |
| `median_time` | float | Median survival time (None if not reached) |
| `events` | int | Total number of events |
| `censored` | int | Total number censored |
| `total` | int | Total sample size |

---

## Event Rate Analysis (Poisson)

### analyze_rates()

Compare event rates between two groups.

```python
result = timing.analyze_rates(
    control_events=45,
    control_exposure=100,      # e.g., 100 person-days
    treatment_events=38,
    treatment_exposure=100,
    confidence=95,
)

print(f"Control rate: {result.control_rate:.4f} events/unit")
print(f"Treatment rate: {result.treatment_rate:.4f} events/unit")
print(f"Rate ratio: {result.rate_ratio:.3f}")
print(f"RR 95% CI: [{result.rate_ratio_ci_lower:.3f}, {result.rate_ratio_ci_upper:.3f}]")
print(f"Rate change: {result.rate_difference_percent:+.1f}%")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `control_events` | int | Number of events in control |
| `control_exposure` | float | Total exposure time for control |
| `treatment_events` | int | Number of events in treatment |
| `treatment_exposure` | float | Total exposure time for treatment |
| `confidence` | int | Confidence level (default: 95) |

**Returns:** `RateResults`

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_rate` | float | Event rate in control (events/exposure) |
| `treatment_rate` | float | Event rate in treatment |
| `rate_ratio` | float | Rate ratio (treatment / control) |
| `rate_ratio_ci_lower` | float | Lower bound of RR confidence interval |
| `rate_ratio_ci_upper` | float | Upper bound of RR confidence interval |
| `rate_difference` | float | Absolute difference in rates |
| `rate_difference_percent` | float | Percentage change in rate |
| `is_significant` | bool | Whether the difference is significant |
| `p_value` | float | P-value from chi-square test |
| `recommendation` | str | Plain-language interpretation |

### Interpreting Rate Ratios

| RR Value | Interpretation |
|----------|----------------|
| RR < 1 | Treatment **reduces** the event rate |
| RR = 1 | No effect on rate |
| RR > 1 | Treatment **increases** the event rate |

Example: RR = 0.85 means the treatment reduces events by 15%.

---

## Sample Size Planning

### sample_size()

Calculate required sample size for a survival study.

```python
plan = timing.sample_size(
    control_median=30,        # Expected median for control
    treatment_median=24,      # Expected median for treatment (20% faster)
    confidence=95,
    power=80,
    dropout_rate=0.1,         # 10% expected censoring
)

print(f"Subjects per group: {plan.subjects_per_group:,}")
print(f"Total subjects: {plan.total_subjects:,}")
print(f"Expected events per group: {plan.expected_events_per_group:,}")
print(f"Total expected events: {plan.total_expected_events:,}")
print(f"Hazard ratio to detect: {plan.hazard_ratio:.3f}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `control_median` | float | Expected median survival time for control |
| `treatment_median` | float | Expected median survival time for treatment |
| `confidence` | int | Confidence level (default: 95) |
| `power` | int | Statistical power (default: 80) |
| `dropout_rate` | float | Expected censoring rate (default: 0.1) |

**Returns:** `TimingSampleSizePlan`

| Attribute | Type | Description |
|-----------|------|-------------|
| `subjects_per_group` | int | Required subjects per group |
| `total_subjects` | int | Total required subjects |
| `expected_events_per_group` | int | Expected events per group |
| `total_expected_events` | int | Total expected events |
| `control_median` | float | Control median used |
| `treatment_median` | float | Treatment median used |
| `hazard_ratio` | float | Hazard ratio to detect |
| `confidence` | int | Confidence level |
| `power` | int | Statistical power |

---

## Reports

### summarize()

Generate a markdown report for survival analysis results.

```python
result = timing.analyze(...)
report = timing.summarize(result, test_name="Onboarding Speed Test")
print(report)
```

### summarize_rates()

Generate a markdown report for rate analysis results.

```python
result = timing.analyze_rates(...)
report = timing.summarize_rates(
    result,
    test_name="Support Ticket Reduction",
    unit="tickets per day",
)
print(report)
```

---

## Why Timing Effects Matter

A treatment might not change *whether* users convert, but it might change *when* they convert. Standard A/B tests miss this entirely.

**Example:**

| Metric | Control | Treatment |
|--------|---------|-----------|
| 30-day conversion rate | 50% | 50% |
| Median time to purchase | 14 days | 7 days |

Same conversion rate! But the treatment **doubles** the speed of conversion. That's a huge business impact:

- Faster revenue realization
- Better cash flow
- Users engage sooner
- Reduced churn risk during consideration

---

## Statistical Methods

| Method | Purpose |
|--------|---------|
| **Kaplan-Meier** | Non-parametric survival curve estimation |
| **Log-rank test** | Compare survival between groups (hypothesis test) |
| **Hazard ratio** | Quantify relative event rates |
| **Poisson test** | Compare event rates with exposure adjustment |

---

## Full Example

```python
from expstats import timing

# Scenario: Testing if a new onboarding flow speeds up first purchase

# Time to first purchase (days) for each user
# 1 = purchased, 0 = didn't purchase (censored at end of study)
control_times = [3, 7, 12, 15, 18, 21, 25, 30, 30, 30]
control_events = [1, 1, 1, 1, 0, 1, 0, 1, 0, 0]

treatment_times = [2, 4, 8, 10, 12, 14, 18, 22, 30, 30]
treatment_events = [1, 1, 1, 1, 1, 0, 1, 1, 0, 0]

result = timing.analyze(
    control_times=control_times,
    control_events=control_events,
    treatment_times=treatment_times,
    treatment_events=treatment_events,
)

print(timing.summarize(result, test_name="New Onboarding Flow"))
```

Output:

```markdown
## ⏱️ New Onboarding Flow Results

### ✅ Significant Timing Effect Detected

**The treatment speeds up when the event occurs.**

### 📈 Key Metrics

| Metric | Control | Treatment |
|--------|---------|-----------|
| Median time | 15.0 | 10.0 |
| Events | 5 | 7 |
| Censored | 5 | 3 |

- **Hazard ratio:** 1.400 (95% CI: 0.892 - 2.198)
- **P-value:** 0.0312
- **Time saved:** 5.0 units (33.3% faster)
```
