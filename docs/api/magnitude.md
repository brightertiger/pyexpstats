# magnitude

**Magnitude Effects** — *How much* it happens

The `magnitude` module provides tools for analyzing experiments where the outcome is a continuous value: revenue, time spent, order value, number of actions. Use this when you care about the *size* of the outcome, not just whether it happened.

## Overview

| Function | Purpose |
|----------|---------|
| [`sample_size()`](#sample_size) | Calculate required sample size for a test |
| [`analyze()`](#analyze) | Analyze a 2-variant A/B test |
| [`analyze_multi()`](#analyze_multi) | Analyze a multi-variant test (3+ variants) |
| [`diff_in_diff()`](#diff_in_diff) | Difference-in-Differences analysis |
| [`confidence_interval()`](#confidence_interval) | Calculate confidence interval for a mean |
| [`summarize()`](#summarize) | Generate stakeholder report for 2-variant test |
| [`summarize_multi()`](#summarize_multi) | Generate stakeholder report for multi-variant test |
| [`summarize_diff_in_diff()`](#summarize_diff_in_diff) | Generate stakeholder report for DiD |
| [`summarize_plan()`](#summarize_plan) | Generate stakeholder report for sample size plan |

---

## sample_size

Calculate the required sample size to detect a given lift in a numeric metric.

```python
def sample_size(
    current_mean: float,
    current_std: float,
    lift_percent: float = 5,
    confidence: int = 95,
    power: int = 80,
    num_variants: int = 2,
) -> SampleSizePlan
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `current_mean` | `float` | *required* | Current mean value of the metric |
| `current_std` | `float` | *required* | Standard deviation of the metric |
| `lift_percent` | `float` | `5` | Minimum relative lift to detect (e.g., 5 = 5% improvement) |
| `confidence` | `int` | `95` | Confidence level (e.g., 95 for 95% confidence) |
| `power` | `int` | `80` | Statistical power (e.g., 80 for 80% power) |
| `num_variants` | `int` | `2` | Number of variants including control |

### Returns

**`SampleSizePlan`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `visitors_per_variant` | `int` | Required visitors per variant |
| `total_visitors` | `int` | Total visitors needed across all variants |
| `current_mean` | `float` | Current mean value |
| `expected_mean` | `float` | Expected variant mean if lift is achieved |
| `standard_deviation` | `float` | Standard deviation used |
| `lift_percent` | `float` | Target lift percentage |
| `confidence` | `int` | Confidence level |
| `power` | `int` | Statistical power |
| `test_duration_days` | `int | None` | Estimated test duration (set via `with_daily_traffic()`) |

### Methods

**`with_daily_traffic(daily_visitors: int) -> SampleSizePlan`**

Set daily traffic to calculate estimated test duration.

### Example

```python
from pyexpstats import magnitude

plan = magnitude.sample_size(
    current_mean=50,      # $50 average order value
    current_std=25,       # $25 standard deviation
    lift_percent=5,       # detect 5% relative lift
    confidence=95,
    power=80,
)

print(f"Need {plan.visitors_per_variant:,} per variant")
print(f"Total: {plan.total_visitors:,}")

# Calculate duration
plan.with_daily_traffic(5000)
print(f"Duration: {plan.test_duration_days} days")
```

---

## analyze

Analyze a 2-variant A/B test for numeric metrics using Welch's t-test.

```python
def analyze(
    control_visitors: int,
    control_mean: float,
    control_std: float,
    variant_visitors: int,
    variant_mean: float,
    variant_std: float,
    confidence: int = 95,
) -> TestResults
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `control_visitors` | `int` | *required* | Sample size in control group |
| `control_mean` | `float` | *required* | Mean value in control group |
| `control_std` | `float` | *required* | Standard deviation in control group |
| `variant_visitors` | `int` | *required* | Sample size in variant group |
| `variant_mean` | `float` | *required* | Mean value in variant group |
| `variant_std` | `float` | *required* | Standard deviation in variant group |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`TestResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_mean` | `float` | Control mean |
| `variant_mean` | `float` | Variant mean |
| `lift_percent` | `float` | Relative lift (%) |
| `lift_absolute` | `float` | Absolute lift |
| `is_significant` | `bool` | Whether result is statistically significant |
| `confidence` | `int` | Confidence level used |
| `p_value` | `float` | P-value of the test |
| `confidence_interval_lower` | `float` | Lower bound of CI for lift |
| `confidence_interval_upper` | `float` | Upper bound of CI for lift |
| `control_std` | `float` | Control standard deviation |
| `variant_std` | `float` | Variant standard deviation |
| `winner` | `str` | `"control"`, `"variant"`, or `"no winner yet"` |
| `recommendation` | `str` | Plain-English recommendation |

### Example

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

print(f"Significant: {result.is_significant}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
print(result.recommendation)
```

---

## analyze_multi

Analyze a multi-variant test (3+ variants) using one-way ANOVA with optional Bonferroni correction for pairwise comparisons.

```python
def analyze_multi(
    variants: List[Dict[str, Any]],
    confidence: int = 95,
    correction: Literal["bonferroni", "none"] = "bonferroni",
) -> MultiVariantResults
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `variants` | `list[dict]` | *required* | List of variant dictionaries |
| `confidence` | `int` | `95` | Confidence level |
| `correction` | `str` | `"bonferroni"` | Multiple comparison correction method |

Each variant dictionary must have:

| Key | Type | Description |
|-----|------|-------------|
| `name` | `str` | Variant name |
| `visitors` | `int` | Sample size |
| `mean` | `float` | Mean value |
| `std` | `float` | Standard deviation |

### Returns

**`MultiVariantResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `variants` | `list[Variant]` | List of Variant objects |
| `is_significant` | `bool` | Whether overall test is significant |
| `confidence` | `int` | Confidence level |
| `p_value` | `float` | ANOVA test p-value |
| `f_statistic` | `float` | F-statistic |
| `df_between` | `int` | Degrees of freedom (between groups) |
| `df_within` | `int` | Degrees of freedom (within groups) |
| `best_variant` | `str` | Name of best performing variant |
| `worst_variant` | `str` | Name of worst performing variant |
| `pairwise_comparisons` | `list[PairwiseComparison]` | All pairwise comparisons |
| `recommendation` | `str` | Plain-English recommendation |

### Example

```python
from pyexpstats import magnitude

result = magnitude.analyze_multi(
    variants=[
        {"name": "control", "visitors": 1000, "mean": 50, "std": 25},
        {"name": "new_layout", "visitors": 1000, "mean": 52, "std": 25},
        {"name": "premium_upsell", "visitors": 1000, "mean": 55, "std": 25},
    ]
)

print(f"Best: {result.best_variant}")
print(f"F-statistic: {result.f_statistic:.2f}")
print(f"Significant: {result.is_significant}")

for p in result.pairwise_comparisons:
    if p.is_significant:
        print(f"  {p.variant_a} vs {p.variant_b}: p={p.p_value_adjusted:.4f}")
```

---

## diff_in_diff

Perform a Difference-in-Differences analysis for numeric metrics. Used for quasi-experimental designs with pre/post measurements.

```python
def diff_in_diff(
    control_pre_n: int,
    control_pre_mean: float,
    control_pre_std: float,
    control_post_n: int,
    control_post_mean: float,
    control_post_std: float,
    treatment_pre_n: int,
    treatment_pre_mean: float,
    treatment_pre_std: float,
    treatment_post_n: int,
    treatment_post_mean: float,
    treatment_post_std: float,
    confidence: int = 95,
) -> DiffInDiffResults
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `control_pre_n` | `int` | *required* | Control group sample size in pre-period |
| `control_pre_mean` | `float` | *required* | Control group mean in pre-period |
| `control_pre_std` | `float` | *required* | Control group std dev in pre-period |
| `control_post_n` | `int` | *required* | Control group sample size in post-period |
| `control_post_mean` | `float` | *required* | Control group mean in post-period |
| `control_post_std` | `float` | *required* | Control group std dev in post-period |
| `treatment_pre_n` | `int` | *required* | Treatment group sample size in pre-period |
| `treatment_pre_mean` | `float` | *required* | Treatment group mean in pre-period |
| `treatment_pre_std` | `float` | *required* | Treatment group std dev in pre-period |
| `treatment_post_n` | `int` | *required* | Treatment group sample size in post-period |
| `treatment_post_mean` | `float` | *required* | Treatment group mean in post-period |
| `treatment_post_std` | `float` | *required* | Treatment group std dev in post-period |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`DiffInDiffResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_pre_mean` | `float` | Control pre-period mean |
| `control_post_mean` | `float` | Control post-period mean |
| `treatment_pre_mean` | `float` | Treatment pre-period mean |
| `treatment_post_mean` | `float` | Treatment post-period mean |
| `control_change` | `float` | Change in control group |
| `treatment_change` | `float` | Change in treatment group |
| `diff_in_diff` | `float` | DiD estimate (treatment effect) |
| `diff_in_diff_percent` | `float` | DiD as relative percent |
| `is_significant` | `bool` | Whether DiD is significant |
| `confidence` | `int` | Confidence level |
| `p_value` | `float` | P-value |
| `t_statistic` | `float` | T-statistic |
| `degrees_of_freedom` | `float` | Degrees of freedom |
| `confidence_interval_lower` | `float` | Lower CI bound |
| `confidence_interval_upper` | `float` | Upper CI bound |
| `recommendation` | `str` | Plain-English recommendation |

### Example

```python
from pyexpstats import magnitude

result = magnitude.diff_in_diff(
    control_pre_n=1000,
    control_pre_mean=50.00,
    control_pre_std=25.00,
    control_post_n=1000,
    control_post_mean=51.00,
    control_post_std=25.00,
    treatment_pre_n=1000,
    treatment_pre_mean=50.00,
    treatment_pre_std=25.00,
    treatment_post_n=1000,
    treatment_post_mean=55.00,
    treatment_post_std=26.00,
)

print(f"DiD effect: ${result.diff_in_diff:+.2f}")
print(f"Significant: {result.is_significant}")
```

---

## confidence_interval

Calculate the confidence interval for a single mean using the t-distribution.

```python
def confidence_interval(
    visitors: int,
    mean: float,
    std: float,
    confidence: int = 95,
) -> ConfidenceInterval
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `visitors` | `int` | *required* | Sample size |
| `mean` | `float` | *required* | Sample mean |
| `std` | `float` | *required* | Sample standard deviation |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`ConfidenceInterval`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `mean` | `float` | Sample mean |
| `lower` | `float` | Lower bound of CI |
| `upper` | `float` | Upper bound of CI |
| `confidence` | `int` | Confidence level |
| `margin_of_error` | `float` | Margin of error |

### Example

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

---

## summarize

Generate a markdown report for a 2-variant test result.

```python
def summarize(
    result: TestResults,
    test_name: str = "Revenue Test",
    metric_name: str = "Average Order Value",
    currency: str = "$",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `TestResults` | *required* | Result from `analyze()` |
| `test_name` | `str` | `"Revenue Test"` | Name of the test for the report |
| `metric_name` | `str` | `"Average Order Value"` | Name of the metric |
| `currency` | `str` | `"$"` | Currency symbol to use |

### Returns

A markdown-formatted string suitable for sharing with stakeholders.

### Example

```python
from pyexpstats import magnitude

result = magnitude.analyze(...)
report = magnitude.summarize(
    result,
    test_name="Checkout Flow Test",
    metric_name="Average Order Value",
    currency="$"
)
print(report)
```

---

## summarize_multi

Generate a markdown report for a multi-variant test result.

```python
def summarize_multi(
    result: MultiVariantResults,
    test_name: str = "Multi-Variant Test",
    metric_name: str = "Average Value",
    currency: str = "$",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `MultiVariantResults` | *required* | Result from `analyze_multi()` |
| `test_name` | `str` | `"Multi-Variant Test"` | Name of the test for the report |
| `metric_name` | `str` | `"Average Value"` | Name of the metric |
| `currency` | `str` | `"$"` | Currency symbol to use |

### Returns

A markdown-formatted string with variant performance table and pairwise comparisons.

---

## summarize_diff_in_diff

Generate a markdown report for a Difference-in-Differences analysis.

```python
def summarize_diff_in_diff(
    result: DiffInDiffResults,
    test_name: str = "Difference-in-Differences Analysis",
    metric_name: str = "Average Value",
    currency: str = "$",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `DiffInDiffResults` | *required* | Result from `diff_in_diff()` |
| `test_name` | `str` | `"Difference-in-Differences Analysis"` | Name of the analysis |
| `metric_name` | `str` | `"Average Value"` | Name of the metric |
| `currency` | `str` | `"$"` | Currency symbol |

### Returns

A markdown-formatted string with pre/post comparison table, DiD estimate, and interpretation.

---

## summarize_plan

Generate a markdown report for a sample size plan.

```python
def summarize_plan(
    plan: SampleSizePlan,
    test_name: str = "Revenue Test",
    metric_name: str = "Average Order Value",
    currency: str = "$",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plan` | `SampleSizePlan` | *required* | Result from `sample_size()` |
| `test_name` | `str` | `"Revenue Test"` | Name of the test for the report |
| `metric_name` | `str` | `"Average Order Value"` | Name of the metric |
| `currency` | `str` | `"$"` | Currency symbol to use |

### Returns

A markdown-formatted string with test parameters, required sample size, and duration estimate.

---

## Data Classes

### SampleSizePlan

```python
@dataclass
class SampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_mean: float
    expected_mean: float
    standard_deviation: float
    lift_percent: float
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlan': ...
```

### TestResults

```python
@dataclass
class TestResults:
    control_mean: float
    variant_mean: float
    lift_percent: float
    lift_absolute: float
    is_significant: bool
    confidence: int
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_visitors: int
    control_std: float
    variant_visitors: int
    variant_std: float
    winner: Literal["control", "variant", "no winner yet"]
    recommendation: str
```

### ConfidenceInterval

```python
@dataclass
class ConfidenceInterval:
    mean: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float
```

### MultiVariantResults

```python
@dataclass
class MultiVariantResults:
    variants: List[Variant]
    is_significant: bool
    confidence: int
    p_value: float
    f_statistic: float
    df_between: int
    df_within: int
    best_variant: str
    worst_variant: str
    pairwise_comparisons: List[PairwiseComparison]
    recommendation: str
```

### PairwiseComparison

```python
@dataclass
class PairwiseComparison:
    variant_a: str
    variant_b: str
    mean_a: float
    mean_b: float
    lift_percent: float
    lift_absolute: float
    p_value: float
    p_value_adjusted: float
    is_significant: bool
    confidence_interval_lower: float
    confidence_interval_upper: float
```
