"""
Sample Ratio Mismatch (SRM) Detection.

SRM occurs when the actual traffic split differs significantly from the expected split.
This often indicates implementation bugs that can invalidate your entire experiment.

Common causes of SRM:
- Bugs in the randomization code
- Bot traffic affecting one variant more than another
- Browser redirects or page load issues
- Caching problems
- JavaScript errors
"""

import math
from dataclasses import dataclass
from typing import Optional, List, Tuple
from scipy.stats import chi2


@dataclass
class SampleRatioResult:
    """Result of Sample Ratio Mismatch check."""

    # Input data
    control_visitors: int
    variant_visitors: int
    expected_ratio: float  # Expected control proportion (e.g., 0.5 for 50/50)

    # Results
    observed_ratio: float
    is_valid: bool  # True if no SRM detected
    p_value: float
    chi2_statistic: float

    # Diagnosis
    severity: str  # "ok", "warning", "critical"
    deviation_percent: float  # How far off from expected
    warning: str
    recommendation: str


def check_sample_ratio(
    control_visitors: int,
    variant_visitors: int,
    expected_ratio: float = 0.5,
    alpha: float = 0.001,  # Very low threshold - SRM is serious
) -> SampleRatioResult:
    """
    Check for Sample Ratio Mismatch (SRM).

    SRM is one of the most critical issues in A/B testing. It indicates
    that something is wrong with your experiment setup, and results
    may be completely invalid.

    Args:
        control_visitors: Number of visitors in control group
        variant_visitors: Number of visitors in variant group
        expected_ratio: Expected proportion in control (default 0.5 for 50/50 split)
        alpha: Significance level for SRM detection (default 0.001, very strict)

    Returns:
        SampleRatioResult with validity check and recommendations

    Example:
        >>> result = check_sample_ratio(
        ...     control_visitors=10500,
        ...     variant_visitors=9500,
        ...     expected_ratio=0.5,
        ... )
        >>> print(result.is_valid)
        False
        >>> print(result.warning)
        "Traffic split is 52.5%/47.5%, expected 50/50..."
    """
    if control_visitors < 0 or variant_visitors < 0:
        raise ValueError("Visitor counts cannot be negative")
    if not 0 < expected_ratio < 1:
        raise ValueError("expected_ratio must be between 0 and 1")

    total_visitors = control_visitors + variant_visitors

    if total_visitors == 0:
        return SampleRatioResult(
            control_visitors=control_visitors,
            variant_visitors=variant_visitors,
            expected_ratio=expected_ratio,
            observed_ratio=0.5,
            is_valid=True,
            p_value=1.0,
            chi2_statistic=0.0,
            severity="ok",
            deviation_percent=0.0,
            warning="No visitors yet.",
            recommendation="Wait for traffic before checking SRM.",
        )

    # Calculate observed ratio
    observed_ratio = control_visitors / total_visitors
    variant_ratio = variant_visitors / total_visitors

    # Expected counts
    expected_control = total_visitors * expected_ratio
    expected_variant = total_visitors * (1 - expected_ratio)

    # Chi-square test for goodness of fit
    chi2_stat = (
        ((control_visitors - expected_control) ** 2 / expected_control) +
        ((variant_visitors - expected_variant) ** 2 / expected_variant)
    )

    p_value = 1 - chi2.cdf(chi2_stat, df=1)

    # Calculate deviation
    deviation_percent = abs(observed_ratio - expected_ratio) / expected_ratio * 100

    # Determine severity
    is_valid = p_value >= alpha

    if is_valid:
        severity = "ok"
    elif p_value >= 0.01:
        severity = "warning"
    else:
        severity = "critical"

    # Generate warning message
    if is_valid:
        warning = (
            f"Traffic split looks good: {observed_ratio*100:.1f}%/{variant_ratio*100:.1f}% "
            f"(expected {expected_ratio*100:.0f}%/{(1-expected_ratio)*100:.0f}%)."
        )
    else:
        warning = (
            f"SAMPLE RATIO MISMATCH DETECTED! "
            f"Traffic split is {observed_ratio*100:.1f}%/{variant_ratio*100:.1f}%, "
            f"expected {expected_ratio*100:.0f}%/{(1-expected_ratio)*100:.0f}%. "
            f"This {deviation_percent:.1f}% deviation is statistically significant (p={p_value:.6f}). "
            f"Your experiment results may be INVALID."
        )

    # Generate recommendation
    if is_valid:
        recommendation = "No action needed. Traffic is splitting as expected."
    else:
        recommendation = (
            "STOP AND INVESTIGATE before trusting results:\n\n"
            "1. **Check randomization code** - Is the bucketing logic correct?\n"
            "2. **Look for bot traffic** - Are bots hitting one variant more?\n"
            "3. **Check for redirects** - Are there any redirects affecting traffic?\n"
            "4. **Review JavaScript errors** - Are errors preventing tracking in one variant?\n"
            "5. **Check caching** - Is one variant being cached differently?\n"
            "6. **Review recent deployments** - Did anything change recently?\n\n"
            "DO NOT trust experiment results until SRM is resolved."
        )

    return SampleRatioResult(
        control_visitors=control_visitors,
        variant_visitors=variant_visitors,
        expected_ratio=expected_ratio,
        observed_ratio=observed_ratio,
        is_valid=is_valid,
        p_value=p_value,
        chi2_statistic=chi2_stat,
        severity=severity,
        deviation_percent=deviation_percent,
        warning=warning,
        recommendation=recommendation,
    )


def check_sample_ratio_multi(
    variant_visitors: List[int],
    expected_ratios: Optional[List[float]] = None,
    alpha: float = 0.001,
) -> SampleRatioResult:
    """
    Check for SRM with multiple variants.

    Args:
        variant_visitors: List of visitor counts for each variant
        expected_ratios: Expected proportions (default: equal split)
        alpha: Significance level

    Returns:
        SampleRatioResult for the overall check
    """
    n_variants = len(variant_visitors)

    if n_variants < 2:
        raise ValueError("Need at least 2 variants")

    if expected_ratios is None:
        expected_ratios = [1.0 / n_variants] * n_variants

    if len(expected_ratios) != n_variants:
        raise ValueError("Length of expected_ratios must match variant_visitors")

    if abs(sum(expected_ratios) - 1.0) > 0.001:
        raise ValueError("expected_ratios must sum to 1")

    total = sum(variant_visitors)

    if total == 0:
        return SampleRatioResult(
            control_visitors=variant_visitors[0] if variant_visitors else 0,
            variant_visitors=sum(variant_visitors[1:]) if len(variant_visitors) > 1 else 0,
            expected_ratio=expected_ratios[0] if expected_ratios else 0.5,
            observed_ratio=0.5,
            is_valid=True,
            p_value=1.0,
            chi2_statistic=0.0,
            severity="ok",
            deviation_percent=0.0,
            warning="No visitors yet.",
            recommendation="Wait for traffic.",
        )

    # Calculate chi-square statistic
    chi2_stat = 0
    for observed, expected_prop in zip(variant_visitors, expected_ratios):
        expected = total * expected_prop
        if expected > 0:
            chi2_stat += (observed - expected) ** 2 / expected

    df = n_variants - 1
    p_value = 1 - chi2.cdf(chi2_stat, df)

    is_valid = p_value >= alpha

    # Build result
    observed_ratios = [v / total for v in variant_visitors]
    max_deviation = max(
        abs(obs - exp) / exp * 100
        for obs, exp in zip(observed_ratios, expected_ratios)
    )

    if is_valid:
        severity = "ok"
        warning = "Traffic split looks good across all variants."
    else:
        severity = "critical" if p_value < 0.01 else "warning"
        warning = (
            f"SAMPLE RATIO MISMATCH DETECTED across {n_variants} variants! "
            f"Maximum deviation: {max_deviation:.1f}% (p={p_value:.6f})."
        )

    return SampleRatioResult(
        control_visitors=variant_visitors[0],
        variant_visitors=sum(variant_visitors[1:]),
        expected_ratio=expected_ratios[0],
        observed_ratio=observed_ratios[0],
        is_valid=is_valid,
        p_value=p_value,
        chi2_statistic=chi2_stat,
        severity=severity,
        deviation_percent=max_deviation,
        warning=warning,
        recommendation="Investigate SRM before trusting results." if not is_valid else "No action needed.",
    )


def summarize(result: SampleRatioResult) -> str:
    """Generate markdown summary of SRM check."""
    lines = ["## Sample Ratio Mismatch Check\n"]

    if result.is_valid:
        lines.append("### Traffic Split is Valid\n")
    else:
        lines.append("### WARNING: Sample Ratio Mismatch Detected!\n")

    # Visual representation
    total = result.control_visitors + result.variant_visitors
    if total > 0:
        ctrl_pct = result.control_visitors / total * 100
        var_pct = result.variant_visitors / total * 100
        ctrl_bar = int(ctrl_pct / 5)
        var_bar = int(var_pct / 5)

        lines.append("**Observed Split:**")
        lines.append(f"- Control: {'█' * ctrl_bar}{'░' * (20-ctrl_bar)} {ctrl_pct:.1f}% ({result.control_visitors:,})")
        lines.append(f"- Variant: {'█' * var_bar}{'░' * (20-var_bar)} {var_pct:.1f}% ({result.variant_visitors:,})")
        lines.append("")

    # Expected vs observed
    lines.append("### Statistics\n")
    lines.append(f"- **Expected ratio:** {result.expected_ratio*100:.0f}%/{(1-result.expected_ratio)*100:.0f}%")
    lines.append(f"- **Observed ratio:** {result.observed_ratio*100:.1f}%/{(1-result.observed_ratio)*100:.1f}%")
    lines.append(f"- **Deviation:** {result.deviation_percent:.2f}%")
    lines.append(f"- **Chi-square statistic:** {result.chi2_statistic:.2f}")
    lines.append(f"- **P-value:** {result.p_value:.6f}")
    lines.append("")

    # Recommendation
    lines.append("### Recommendation\n")
    lines.append(result.recommendation)

    return "\n".join(lines)


__all__ = [
    "SampleRatioResult",
    "check_sample_ratio",
    "check_sample_ratio_multi",
    "summarize",
]
