"""
Guardrail Metrics Monitoring.

Guardrails are metrics you want to protect during an A/B test:
- Page load time shouldn't increase
- Error rate shouldn't increase
- Revenue per user shouldn't decrease
- User satisfaction shouldn't drop

Even if your primary metric improves, failing guardrails means
you might be trading short-term gains for long-term harm.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Literal, Tuple
from scipy import stats as scipy_stats


@dataclass
class GuardrailCheck:
    """Definition of a guardrail metric to check."""

    name: str
    metric_type: Literal["mean", "proportion", "ratio"]
    direction: Literal["increase_is_bad", "decrease_is_bad"]
    threshold_percent: float = 5.0  # Alert if change exceeds this
    critical_threshold_percent: float = 10.0  # Critical if exceeds this


@dataclass
class GuardrailResult:
    """Result of checking a single guardrail."""

    name: str
    status: Literal["passed", "warning", "failed"]

    # Metric values
    control_value: float
    variant_value: float
    change_percent: float

    # Statistical significance
    is_significant: bool
    p_value: float
    confidence_interval: Tuple[float, float]

    # Thresholds
    threshold_percent: float
    critical_threshold_percent: float

    # Interpretation
    interpretation: str


@dataclass
class GuardrailReport:
    """Complete guardrail analysis report."""

    # Overall status
    all_passed: bool
    has_warnings: bool
    has_failures: bool

    # Individual results
    results: List[GuardrailResult]
    passed: List[str]
    warnings: List[str]
    failures: List[str]

    # Recommendation
    can_ship: bool
    recommendation: str


def check_guardrails(
    guardrails: List[dict],
    alpha: float = 0.05,
) -> GuardrailReport:
    """
    Check multiple guardrail metrics for an A/B test.

    Args:
        guardrails: List of guardrail definitions with data:
            - name: Metric name (e.g., "Page Load Time")
            - metric_type: "mean", "proportion", or "ratio"
            - direction: "increase_is_bad" or "decrease_is_bad"
            - threshold_percent: Warning threshold (default 5%)
            - critical_threshold_percent: Failure threshold (default 10%)
            - control_data: List of values OR dict with count/total for proportions
            - variant_data: List of values OR dict with count/total for proportions
        alpha: Significance level for statistical tests

    Returns:
        GuardrailReport with status of all guardrails

    Example:
        >>> report = check_guardrails([
        ...     {
        ...         "name": "Page Load Time (ms)",
        ...         "metric_type": "mean",
        ...         "direction": "increase_is_bad",
        ...         "threshold_percent": 5,
        ...         "control_data": [1200, 1100, 1300, 1150, 1250],
        ...         "variant_data": [1400, 1350, 1500, 1420, 1380],
        ...     },
        ...     {
        ...         "name": "Error Rate",
        ...         "metric_type": "proportion",
        ...         "direction": "increase_is_bad",
        ...         "threshold_percent": 10,
        ...         "control_data": {"count": 50, "total": 10000},
        ...         "variant_data": {"count": 55, "total": 10000},
        ...     },
        ... ])
        >>> print(f"Can ship: {report.can_ship}")
    """
    results = []
    passed = []
    warnings = []
    failures = []

    for guardrail in guardrails:
        result = _check_single_guardrail(guardrail, alpha)
        results.append(result)

        if result.status == "passed":
            passed.append(result.name)
        elif result.status == "warning":
            warnings.append(result.name)
        else:
            failures.append(result.name)

    # Generate overall recommendation
    all_passed = len(failures) == 0 and len(warnings) == 0
    has_warnings = len(warnings) > 0
    has_failures = len(failures) > 0

    can_ship = len(failures) == 0
    recommendation = _generate_recommendation(
        results=results,
        passed=passed,
        warnings=warnings,
        failures=failures,
    )

    return GuardrailReport(
        all_passed=all_passed,
        has_warnings=has_warnings,
        has_failures=has_failures,
        results=results,
        passed=passed,
        warnings=warnings,
        failures=failures,
        can_ship=can_ship,
        recommendation=recommendation,
    )


def _check_single_guardrail(guardrail: dict, alpha: float) -> GuardrailResult:
    """Check a single guardrail metric."""
    name = guardrail["name"]
    metric_type = guardrail.get("metric_type", "mean")
    direction = guardrail.get("direction", "increase_is_bad")
    threshold = guardrail.get("threshold_percent", 5.0)
    critical = guardrail.get("critical_threshold_percent", 10.0)
    control_data = guardrail["control_data"]
    variant_data = guardrail["variant_data"]

    if metric_type == "proportion":
        result = _check_proportion_guardrail(
            name, control_data, variant_data, direction, threshold, critical, alpha
        )
    elif metric_type == "ratio":
        result = _check_ratio_guardrail(
            name, control_data, variant_data, direction, threshold, critical, alpha
        )
    else:  # mean
        result = _check_mean_guardrail(
            name, control_data, variant_data, direction, threshold, critical, alpha
        )

    return result


def _check_mean_guardrail(
    name: str,
    control_data: List[float],
    variant_data: List[float],
    direction: str,
    threshold: float,
    critical: float,
    alpha: float,
) -> GuardrailResult:
    """Check guardrail for a continuous metric (mean comparison)."""
    import numpy as np

    control_array = np.array(control_data)
    variant_array = np.array(variant_data)

    control_mean = np.mean(control_array)
    variant_mean = np.mean(variant_array)

    # Calculate change percentage
    if control_mean != 0:
        change_percent = ((variant_mean - control_mean) / abs(control_mean)) * 100
    else:
        change_percent = 0 if variant_mean == 0 else float('inf')

    # Welch's t-test (unequal variances)
    t_stat, p_value = scipy_stats.ttest_ind(variant_array, control_array, equal_var=False)

    # Confidence interval for the difference
    n1, n2 = len(control_array), len(variant_array)
    s1, s2 = np.std(control_array, ddof=1), np.std(variant_array, ddof=1)
    se = math.sqrt(s1**2/n1 + s2**2/n2) if n1 > 0 and n2 > 0 else 0
    t_crit = scipy_stats.t.ppf(1 - alpha/2, min(n1, n2) - 1) if min(n1, n2) > 1 else 1.96
    diff = variant_mean - control_mean
    ci = (diff - t_crit * se, diff + t_crit * se)

    # Determine if it's a bad change
    is_bad_direction = (
        (direction == "increase_is_bad" and change_percent > 0) or
        (direction == "decrease_is_bad" and change_percent < 0)
    )
    is_significant = p_value < alpha

    # Determine status
    abs_change = abs(change_percent)
    if not is_bad_direction or abs_change < threshold:
        status = "passed"
    elif abs_change >= critical:
        status = "failed"
    else:
        status = "warning"

    # Generate interpretation
    interpretation = _interpret_guardrail(
        name, control_mean, variant_mean, change_percent,
        is_significant, p_value, direction, status
    )

    return GuardrailResult(
        name=name,
        status=status,
        control_value=control_mean,
        variant_value=variant_mean,
        change_percent=change_percent,
        is_significant=is_significant,
        p_value=p_value,
        confidence_interval=ci,
        threshold_percent=threshold,
        critical_threshold_percent=critical,
        interpretation=interpretation,
    )


def _check_proportion_guardrail(
    name: str,
    control_data: dict,
    variant_data: dict,
    direction: str,
    threshold: float,
    critical: float,
    alpha: float,
) -> GuardrailResult:
    """Check guardrail for a proportion metric."""
    control_count = control_data["count"]
    control_total = control_data["total"]
    variant_count = variant_data["count"]
    variant_total = variant_data["total"]

    control_rate = control_count / control_total if control_total > 0 else 0
    variant_rate = variant_count / variant_total if variant_total > 0 else 0

    # Calculate change percentage
    if control_rate != 0:
        change_percent = ((variant_rate - control_rate) / control_rate) * 100
    else:
        change_percent = 0 if variant_rate == 0 else float('inf')

    # Chi-square test or z-test for proportions
    contingency = [[control_count, control_total - control_count],
                   [variant_count, variant_total - variant_count]]

    # Handle edge cases
    if min(control_total, variant_total) > 0:
        chi2, p_value, _, _ = scipy_stats.chi2_contingency(contingency)
    else:
        p_value = 1.0

    # Confidence interval for rate difference
    se_control = math.sqrt(control_rate * (1 - control_rate) / control_total) if control_total > 0 else 0
    se_variant = math.sqrt(variant_rate * (1 - variant_rate) / variant_total) if variant_total > 0 else 0
    se_diff = math.sqrt(se_control**2 + se_variant**2)
    z_crit = 1.96  # For 95% CI
    diff = variant_rate - control_rate
    ci = (diff - z_crit * se_diff, diff + z_crit * se_diff)

    # Determine if it's a bad change
    is_bad_direction = (
        (direction == "increase_is_bad" and change_percent > 0) or
        (direction == "decrease_is_bad" and change_percent < 0)
    )
    is_significant = p_value < alpha

    # Determine status
    abs_change = abs(change_percent)
    if not is_bad_direction or abs_change < threshold:
        status = "passed"
    elif abs_change >= critical:
        status = "failed"
    else:
        status = "warning"

    interpretation = _interpret_guardrail(
        name, control_rate, variant_rate, change_percent,
        is_significant, p_value, direction, status
    )

    return GuardrailResult(
        name=name,
        status=status,
        control_value=control_rate,
        variant_value=variant_rate,
        change_percent=change_percent,
        is_significant=is_significant,
        p_value=p_value,
        confidence_interval=ci,
        threshold_percent=threshold,
        critical_threshold_percent=critical,
        interpretation=interpretation,
    )


def _check_ratio_guardrail(
    name: str,
    control_data: dict,
    variant_data: dict,
    direction: str,
    threshold: float,
    critical: float,
    alpha: float,
) -> GuardrailResult:
    """Check guardrail for a ratio metric (e.g., revenue per user) using delta method."""
    import numpy as np

    control_total = control_data["total_value"]
    control_count = control_data["count"]
    variant_total = variant_data["total_value"]
    variant_count = variant_data["count"]

    control_ratio = control_total / control_count if control_count > 0 else 0
    variant_ratio = variant_total / variant_count if variant_count > 0 else 0

    # Calculate change percentage
    if control_ratio != 0:
        change_percent = ((variant_ratio - control_ratio) / abs(control_ratio)) * 100
    else:
        change_percent = 0 if variant_ratio == 0 else float('inf')

    # Delta method for ratio variance: Var(total/count) ≈ (1/count) * Var(per-unit)
    # Approximate SE using provided stats or fallback to Poisson-like variance
    control_var = control_data.get("variance", control_ratio)  # fallback: assume variance ≈ mean
    variant_var = variant_data.get("variance", variant_ratio)

    se_control = math.sqrt(control_var / control_count) if control_count > 0 else 0
    se_variant = math.sqrt(variant_var / variant_count) if variant_count > 0 else 0
    se_diff = math.sqrt(se_control**2 + se_variant**2)

    # Z-test for difference of ratios
    diff = variant_ratio - control_ratio
    if se_diff > 0:
        z_stat = diff / se_diff
        p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z_stat)))
    else:
        p_value = 1.0

    is_significant = p_value < alpha

    z_crit = scipy_stats.norm.ppf(1 - alpha / 2)
    ci = (diff - z_crit * se_diff, diff + z_crit * se_diff)

    # Determine if it's a bad change
    is_bad_direction = (
        (direction == "increase_is_bad" and change_percent > 0) or
        (direction == "decrease_is_bad" and change_percent < 0)
    )

    # Determine status
    abs_change = abs(change_percent)
    if not is_bad_direction or abs_change < threshold:
        status = "passed"
    elif abs_change >= critical:
        status = "failed"
    else:
        status = "warning"

    interpretation = _interpret_guardrail(
        name, control_ratio, variant_ratio, change_percent,
        is_significant, p_value, direction, status
    )

    return GuardrailResult(
        name=name,
        status=status,
        control_value=control_ratio,
        variant_value=variant_ratio,
        change_percent=change_percent,
        is_significant=is_significant,
        p_value=p_value,
        confidence_interval=ci,
        threshold_percent=threshold,
        critical_threshold_percent=critical,
        interpretation=interpretation,
    )


def _interpret_guardrail(
    name: str,
    control_value: float,
    variant_value: float,
    change_percent: float,
    is_significant: bool,
    p_value: float,
    direction: str,
    status: str,
) -> str:
    """Generate interpretation text for a guardrail result."""
    if status == "passed":
        if abs(change_percent) < 1:
            return f"{name} is unchanged (no meaningful difference detected)."
        else:
            direction_word = "increased" if change_percent > 0 else "decreased"
            return f"{name} {direction_word} by {abs(change_percent):.1f}% but within acceptable limits."
    elif status == "warning":
        direction_word = "increased" if change_percent > 0 else "decreased"
        return (
            f"WARNING: {name} {direction_word} by {abs(change_percent):.1f}%. "
            f"This exceeds the warning threshold but not the critical threshold. "
            f"Monitor closely."
        )
    else:  # failed
        direction_word = "increased" if change_percent > 0 else "decreased"
        return (
            f"FAILED: {name} {direction_word} by {abs(change_percent):.1f}%. "
            f"This exceeds the critical threshold. Do not ship without addressing this."
        )


def _generate_recommendation(
    results: List[GuardrailResult],
    passed: List[str],
    warnings: List[str],
    failures: List[str],
) -> str:
    """Generate overall guardrail recommendation."""
    lines = []

    lines.append("## Guardrail Analysis Report\n")

    # Summary table
    lines.append("### Summary\n")
    lines.append("| Metric | Status | Change | Significant? |")
    lines.append("|--------|--------|--------|--------------|")
    for result in results:
        status_emoji = "PASS" if result.status == "passed" else ("WARN" if result.status == "warning" else "FAIL")
        sig = "Yes" if result.is_significant else "No"
        lines.append(f"| {result.name} | {status_emoji} | {result.change_percent:+.1f}% | {sig} |")
    lines.append("")

    # Status breakdown
    if failures:
        lines.append("### Failed Guardrails\n")
        for name in failures:
            result = next(r for r in results if r.name == name)
            lines.append(f"- **{name}**: {result.interpretation}")
        lines.append("")

    if warnings:
        lines.append("### Warning Guardrails\n")
        for name in warnings:
            result = next(r for r in results if r.name == name)
            lines.append(f"- **{name}**: {result.interpretation}")
        lines.append("")

    if passed:
        lines.append("### Passed Guardrails\n")
        lines.append(f"- {', '.join(passed)}")
        lines.append("")

    # Overall recommendation
    lines.append("### Recommendation\n")
    if failures:
        lines.append(
            "**DO NOT SHIP** - One or more guardrails have failed. "
            "The variant is causing unacceptable degradation in key metrics. "
            "Investigate and address the issues before proceeding."
        )
    elif warnings:
        lines.append(
            "**PROCEED WITH CAUTION** - All critical guardrails pass, but some metrics "
            "show concerning trends. Ship only if the primary metric improvement "
            "justifies the trade-offs. Monitor these metrics closely post-launch."
        )
    else:
        lines.append(
            "**CLEAR TO SHIP** - All guardrails pass. The variant does not show "
            "any unacceptable degradation in monitored metrics."
        )

    return "\n".join(lines)


def summarize(result: GuardrailReport) -> str:
    """Generate markdown summary of guardrail report."""
    return result.recommendation


__all__ = [
    "GuardrailCheck",
    "GuardrailResult",
    "GuardrailReport",
    "check_guardrails",
    "summarize",
]
