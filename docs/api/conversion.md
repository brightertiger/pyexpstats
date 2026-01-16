# conversion

**Conversion Effects** — *Whether* something happens

The `conversion` module provides tools for analyzing experiments where the outcome is binary: did the user convert or not? Use this for click rates, signup rates, purchase rates, and any yes/no metric.

## Overview

| Function | Purpose |
|----------|---------|
| [`sample_size()`](#sample_size) | Calculate required sample size for a test |
| [`analyze()`](#analyze) | Analyze a 2-variant A/B test |
| [`analyze_multi()`](#analyze_multi) | Analyze a multi-variant test (3+ variants) |
| [`diff_in_diff()`](#diff_in_diff) | Difference-in-Differences analysis |
| [`confidence_interval()`](#confidence_interval) | Calculate confidence interval for a rate |
| [`summarize()`](#summarize) | Generate stakeholder report for 2-variant test |
| [`summarize_multi()`](#summarize_multi) | Generate stakeholder report for multi-variant test |
| [`summarize_diff_in_diff()`](#summarize_diff_in_diff) | Generate stakeholder report for DiD |
| [`summarize_plan()`](#summarize_plan) | Generate stakeholder report for sample size plan |

---

## sample_size

Calculate the required sample size to detect a given lift in conversion rate.

```python
def sample_size(
    current_rate: float,
    lift_percent: float = 10,
    confidence: int = 95,
    power: int = 80,
    num_variants: int = 2,
) -> SampleSizePlan
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `current_rate` | `float` | *required* | Current conversion rate. Can be decimal (0.05) or percentage (5). |
| `lift_percent` | `float` | `10` | Minimum relative lift to detect (e.g., 10 = 10% improvement). |
| `confidence` | `int` | `95` | Confidence level (e.g., 95 for 95% confidence). |
| `power` | `int` | `80` | Statistical power (e.g., 80 for 80% power). |
| `num_variants` | `int` | `2` | Number of variants including control. |

### Returns

**`SampleSizePlan`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `visitors_per_variant` | `int` | Required visitors per variant |
| `total_visitors` | `int` | Total visitors needed across all variants |
| `current_rate` | `float` | Current conversion rate (decimal) |
| `expected_rate` | `float` | Expected variant rate if lift is achieved |
| `lift_percent` | `float` | Target lift percentage |
| `confidence` | `int` | Confidence level |
| `power` | `int` | Statistical power |
| `test_duration_days` | `int | None` | Estimated test duration (set via `with_daily_traffic()`) |

### Methods

**`with_daily_traffic(daily_visitors: int) -> SampleSizePlan`**

Set daily traffic to calculate estimated test duration.

### Example

```python
from expstats import conversion

plan = conversion.sample_size(
    current_rate=5,       # 5% conversion rate
    lift_percent=10,      # detect 10% relative lift
    confidence=95,
    power=80,
)

print(f"Need {plan.visitors_per_variant:,} per variant")
print(f"Total: {plan.total_visitors:,}")

# Calculate duration
plan.with_daily_traffic(10000)
print(f"Duration: {plan.test_duration_days} days")
```

---

## analyze

Analyze a 2-variant A/B test for conversion rates using a two-proportion z-test.

```python
def analyze(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    confidence: int = 95,
) -> TestResults
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `control_visitors` | `int` | *required* | Number of visitors in control group |
| `control_conversions` | `int` | *required* | Number of conversions in control group |
| `variant_visitors` | `int` | *required* | Number of visitors in variant group |
| `variant_conversions` | `int` | *required* | Number of conversions in variant group |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`TestResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_rate` | `float` | Control conversion rate |
| `variant_rate` | `float` | Variant conversion rate |
| `lift_percent` | `float` | Relative lift (%) |
| `lift_absolute` | `float` | Absolute lift |
| `is_significant` | `bool` | Whether result is statistically significant |
| `confidence` | `int` | Confidence level used |
| `p_value` | `float` | P-value of the test |
| `confidence_interval_lower` | `float` | Lower bound of CI for lift |
| `confidence_interval_upper` | `float` | Upper bound of CI for lift |
| `winner` | `str` | `"control"`, `"variant"`, or `"no winner yet"` |
| `recommendation` | `str` | Plain-English recommendation |

### Example

```python
from expstats import conversion

result = conversion.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=600,
)

print(f"Significant: {result.is_significant}")
print(f"Lift: {result.lift_percent:+.1f}%")
print(f"Winner: {result.winner}")
print(result.recommendation)
```

---

## analyze_multi

Analyze a multi-variant test (3+ variants) using Chi-square test with optional Bonferroni correction for pairwise comparisons.

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
| `visitors` | `int` | Number of visitors |
| `conversions` | `int` | Number of conversions |

### Returns

**`MultiVariantResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `variants` | `list[Variant]` | List of Variant objects |
| `is_significant` | `bool` | Whether overall test is significant |
| `confidence` | `int` | Confidence level |
| `p_value` | `float` | Chi-square test p-value |
| `test_statistic` | `float` | Chi-square statistic |
| `degrees_of_freedom` | `int` | Degrees of freedom |
| `best_variant` | `str` | Name of best performing variant |
| `worst_variant` | `str` | Name of worst performing variant |
| `pairwise_comparisons` | `list[PairwiseComparison]` | All pairwise comparisons |
| `recommendation` | `str` | Plain-English recommendation |

### Example

```python
from expstats import conversion

result = conversion.analyze_multi(
    variants=[
        {"name": "control", "visitors": 10000, "conversions": 500},
        {"name": "variant_a", "visitors": 10000, "conversions": 550},
        {"name": "variant_b", "visitors": 10000, "conversions": 600},
    ]
)

print(f"Best: {result.best_variant}")
print(f"Significant: {result.is_significant}")

for p in result.pairwise_comparisons:
    if p.is_significant:
        print(f"  {p.variant_a} vs {p.variant_b}: p={p.p_value_adjusted:.4f}")
```

---

## diff_in_diff

Perform a Difference-in-Differences analysis for conversion rates. Used for quasi-experimental designs with pre/post measurements.

```python
def diff_in_diff(
    control_pre_visitors: int,
    control_pre_conversions: int,
    control_post_visitors: int,
    control_post_conversions: int,
    treatment_pre_visitors: int,
    treatment_pre_conversions: int,
    treatment_post_visitors: int,
    treatment_post_conversions: int,
    confidence: int = 95,
) -> DiffInDiffResults
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `control_pre_visitors` | `int` | *required* | Control group visitors in pre-period |
| `control_pre_conversions` | `int` | *required* | Control group conversions in pre-period |
| `control_post_visitors` | `int` | *required* | Control group visitors in post-period |
| `control_post_conversions` | `int` | *required* | Control group conversions in post-period |
| `treatment_pre_visitors` | `int` | *required* | Treatment group visitors in pre-period |
| `treatment_pre_conversions` | `int` | *required* | Treatment group conversions in pre-period |
| `treatment_post_visitors` | `int` | *required* | Treatment group visitors in post-period |
| `treatment_post_conversions` | `int` | *required* | Treatment group conversions in post-period |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`DiffInDiffResults`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `control_pre_rate` | `float` | Control pre-period conversion rate |
| `control_post_rate` | `float` | Control post-period conversion rate |
| `treatment_pre_rate` | `float` | Treatment pre-period conversion rate |
| `treatment_post_rate` | `float` | Treatment post-period conversion rate |
| `control_change` | `float` | Change in control group |
| `treatment_change` | `float` | Change in treatment group |
| `diff_in_diff` | `float` | DiD estimate (treatment effect) |
| `diff_in_diff_percent` | `float` | DiD as relative percent |
| `is_significant` | `bool` | Whether DiD is significant |
| `confidence` | `int` | Confidence level |
| `p_value` | `float` | P-value |
| `z_statistic` | `float` | Z-statistic |
| `confidence_interval_lower` | `float` | Lower CI bound |
| `confidence_interval_upper` | `float` | Upper CI bound |
| `recommendation` | `str` | Plain-English recommendation |

### Example

```python
from expstats import conversion

result = conversion.diff_in_diff(
    control_pre_visitors=5000,
    control_pre_conversions=250,
    control_post_visitors=5000,
    control_post_conversions=275,
    treatment_pre_visitors=5000,
    treatment_pre_conversions=250,
    treatment_post_visitors=5000,
    treatment_post_conversions=350,
)

print(f"DiD effect: {result.diff_in_diff:+.2%}")
print(f"Significant: {result.is_significant}")
```

---

## confidence_interval

Calculate the confidence interval for a single conversion rate using the Wilson score interval.

```python
def confidence_interval(
    visitors: int,
    conversions: int,
    confidence: int = 95,
) -> ConfidenceInterval
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `visitors` | `int` | *required* | Number of visitors |
| `conversions` | `int` | *required* | Number of conversions |
| `confidence` | `int` | `95` | Confidence level |

### Returns

**`ConfidenceInterval`** with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `rate` | `float` | Observed conversion rate |
| `lower` | `float` | Lower bound of CI |
| `upper` | `float` | Upper bound of CI |
| `confidence` | `int` | Confidence level |
| `margin_of_error` | `float` | Margin of error |

### Example

```python
from expstats import conversion

ci = conversion.confidence_interval(
    visitors=1000,
    conversions=50,
    confidence=95,
)

print(f"Rate: {ci.rate:.2%}")
print(f"95% CI: [{ci.lower:.2%}, {ci.upper:.2%}]")
```

---

## summarize

Generate a markdown report for a 2-variant test result.

```python
def summarize(
    result: TestResults,
    test_name: str = "A/B Test",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `TestResults` | *required* | Result from `analyze()` |
| `test_name` | `str` | `"A/B Test"` | Name of the test for the report |

### Returns

A markdown-formatted string suitable for sharing with stakeholders.

### Example

```python
from expstats import conversion

result = conversion.analyze(...)
report = conversion.summarize(result, test_name="Homepage CTA Test")
print(report)
```

---

## summarize_multi

Generate a markdown report for a multi-variant test result.

```python
def summarize_multi(
    result: MultiVariantResults,
    test_name: str = "Multi-Variant Test",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `MultiVariantResults` | *required* | Result from `analyze_multi()` |
| `test_name` | `str` | `"Multi-Variant Test"` | Name of the test for the report |

### Returns

A markdown-formatted string with variant performance table and pairwise comparisons.

---

## summarize_diff_in_diff

Generate a markdown report for a Difference-in-Differences analysis.

```python
def summarize_diff_in_diff(
    result: DiffInDiffResults,
    test_name: str = "Difference-in-Differences Analysis",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `result` | `DiffInDiffResults` | *required* | Result from `diff_in_diff()` |
| `test_name` | `str` | `"Difference-in-Differences Analysis"` | Name of the analysis |

### Returns

A markdown-formatted string with pre/post comparison table, DiD estimate, and interpretation.

---

## summarize_plan

Generate a markdown report for a sample size plan.

```python
def summarize_plan(
    plan: SampleSizePlan,
    test_name: str = "A/B Test",
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plan` | `SampleSizePlan` | *required* | Result from `sample_size()` |
| `test_name` | `str` | `"A/B Test"` | Name of the test for the report |

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
    current_rate: float
    expected_rate: float
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
    control_rate: float
    variant_rate: float
    lift_percent: float
    lift_absolute: float
    is_significant: bool
    confidence: int
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    winner: Literal["control", "variant", "no winner yet"]
    recommendation: str
```

### ConfidenceInterval

```python
@dataclass
class ConfidenceInterval:
    rate: float
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
    test_statistic: float
    degrees_of_freedom: int
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
    rate_a: float
    rate_b: float
    lift_percent: float
    lift_absolute: float
    p_value: float
    p_value_adjusted: float
    is_significant: bool
    confidence_interval_lower: float
    confidence_interval_upper: float
```
