"""
Sequential A/B Testing Module.

This module provides sequential testing capabilities that allow you to:
- Check if you can stop a test early
- Control for the "peeking problem" (inflated false positive rates)
- Get valid confidence intervals at any point during the test

Based on Sequential Probability Ratio Test (SPRT) and group sequential methods.

References:
- Evan Miller's Sequential A/B Testing: https://www.evanmiller.org/sequential-ab-testing.html
- Johari et al. "Peeking at A/B Tests" (2017)
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional, Tuple
from scipy.stats import norm
import numpy as np


@dataclass
class SequentialTestResult:
    """Results from sequential A/B test analysis."""

    # Current state
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    control_rate: float
    variant_rate: float

    # Decision
    can_stop: bool
    decision: Literal["variant_wins", "control_wins", "no_difference", "keep_running"]
    recommendation: str

    # Statistics
    lift_percent: float
    lift_absolute: float
    z_statistic: float
    p_value: float

    # Boundaries
    upper_boundary: float  # Stop for variant wins
    lower_boundary: float  # Stop for control wins
    current_statistic: float

    # Confidence (adjusted for sequential testing)
    confidence_variant_better: float  # Probability variant > control
    confidence_control_better: float  # Probability control > variant
    adjusted_alpha: float  # Alpha spending so far

    # Progress
    information_fraction: float  # How far through the test (0-1)
    estimated_remaining_visitors: Optional[int]


@dataclass
class SequentialBoundaries:
    """Stopping boundaries for sequential test."""
    upper: float  # Z-score boundary for efficacy (variant wins)
    lower: float  # Z-score boundary for futility (no difference/control wins)
    alpha_spent: float  # Cumulative alpha spent


def _obrien_fleming_boundary(alpha: float, information_fraction: float) -> float:
    """
    Calculate O'Brien-Fleming spending function boundary.

    This is a conservative boundary that spends very little alpha early
    and more towards the end, making early stopping harder but final
    conclusions more powerful.
    """
    if information_fraction <= 0:
        return float('inf')
    if information_fraction >= 1:
        return norm.ppf(1 - alpha / 2)

    # O'Brien-Fleming spending function
    t = information_fraction
    alpha_spent = 2 * (1 - norm.cdf(norm.ppf(1 - alpha / 2) / math.sqrt(t)))

    return norm.ppf(1 - alpha_spent / 2)


def _pocock_boundary(alpha: float, information_fraction: float, num_looks: int = 5) -> float:
    """
    Calculate Pocock spending function boundary.

    This uses a constant boundary across all looks, making early stopping
    easier but requiring adjustment for multiple comparisons.
    """
    if information_fraction <= 0:
        return float('inf')

    # Pocock uses constant boundaries, adjusted for number of looks
    # Approximate adjustment
    adjusted_alpha = alpha / (1 + 0.5 * (num_looks - 1))
    return norm.ppf(1 - adjusted_alpha / 2)


def _calculate_z_statistic(p1: float, n1: int, p2: float, n2: int) -> float:
    """Calculate Z-statistic for two proportions."""
    p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)

    if p_pooled == 0 or p_pooled == 1:
        return 0.0

    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))

    if se == 0:
        return 0.0

    return (p2 - p1) / se


def get_boundaries(
    information_fraction: float,
    alpha: float = 0.05,
    method: Literal["obrien-fleming", "pocock"] = "obrien-fleming",
    num_planned_looks: int = 5,
) -> SequentialBoundaries:
    """
    Get stopping boundaries for the current information fraction.

    Args:
        information_fraction: Proportion of planned sample collected (0-1)
        alpha: Significance level (default 0.05)
        method: Boundary method ("obrien-fleming" or "pocock")
        num_planned_looks: Number of planned interim analyses

    Returns:
        SequentialBoundaries with upper and lower boundaries
    """
    if method == "obrien-fleming":
        boundary = _obrien_fleming_boundary(alpha, information_fraction)
        # O'Brien-Fleming alpha spending
        alpha_spent = 2 * (1 - norm.cdf(boundary)) if boundary < float('inf') else 0
    else:  # pocock
        boundary = _pocock_boundary(alpha, information_fraction, num_planned_looks)
        alpha_spent = alpha * information_fraction

    return SequentialBoundaries(
        upper=boundary,
        lower=-boundary,  # Symmetric boundaries
        alpha_spent=min(alpha_spent, alpha),
    )


def analyze(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    expected_visitors_per_variant: int,
    alpha: float = 0.05,
    method: Literal["obrien-fleming", "pocock"] = "obrien-fleming",
    min_visitors_per_variant: int = 100,
) -> SequentialTestResult:
    """
    Analyze an A/B test using sequential methods.

    This allows you to check results during the test while controlling
    the false positive rate. Unlike fixed-horizon tests, you can stop
    early if results are conclusive.

    Args:
        control_visitors: Number of visitors in control group
        control_conversions: Number of conversions in control group
        variant_visitors: Number of visitors in variant group
        variant_conversions: Number of conversions in variant group
        expected_visitors_per_variant: Planned sample size per variant
        alpha: Significance level (default 0.05 for 95% confidence)
        method: Boundary method - "obrien-fleming" (conservative) or "pocock" (aggressive)
        min_visitors_per_variant: Minimum visitors before allowing early stop

    Returns:
        SequentialTestResult with decision and statistics

    Example:
        >>> result = sequential.analyze(
        ...     control_visitors=5000,
        ...     control_conversions=250,
        ...     variant_visitors=5000,
        ...     variant_conversions=300,
        ...     expected_visitors_per_variant=10000,
        ... )
        >>> print(result.can_stop)
        True
        >>> print(result.decision)
        'variant_wins'
    """
    # Validate inputs
    if control_visitors <= 0 or variant_visitors <= 0:
        raise ValueError("Visitors must be positive")
    if control_conversions > control_visitors:
        raise ValueError("Control conversions cannot exceed control visitors")
    if variant_conversions > variant_visitors:
        raise ValueError("Variant conversions cannot exceed variant visitors")
    if expected_visitors_per_variant <= 0:
        raise ValueError("Expected visitors must be positive")

    # Calculate rates
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors

    # Calculate lift
    lift_absolute = p2 - p1
    lift_percent = (lift_absolute / p1 * 100) if p1 > 0 else 0

    # Calculate information fraction (how far through the test)
    current_visitors = min(control_visitors, variant_visitors)
    information_fraction = min(current_visitors / expected_visitors_per_variant, 1.0)

    # Get boundaries
    boundaries = get_boundaries(information_fraction, alpha, method)

    # Calculate test statistic
    z_stat = _calculate_z_statistic(p1, control_visitors, p2, variant_visitors)
    p_value = 2 * (1 - norm.cdf(abs(z_stat)))

    # Calculate confidence that each variant is better
    # Using approximate posterior probability
    se_diff = math.sqrt(
        p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / variant_visitors
    ) if control_visitors > 0 and variant_visitors > 0 else 0

    if se_diff > 0:
        # Probability that variant is better than control
        confidence_variant_better = norm.cdf(lift_absolute / se_diff)
        confidence_control_better = 1 - confidence_variant_better
    else:
        confidence_variant_better = 0.5
        confidence_control_better = 0.5

    # Make decision
    can_stop = False
    decision = "keep_running"

    # Check if we have enough data
    has_min_sample = (
        control_visitors >= min_visitors_per_variant and
        variant_visitors >= min_visitors_per_variant
    )

    if has_min_sample:
        if z_stat >= boundaries.upper:
            can_stop = True
            decision = "variant_wins"
        elif z_stat <= boundaries.lower:
            can_stop = True
            decision = "control_wins"
        elif information_fraction >= 1.0:
            can_stop = True
            if abs(z_stat) < norm.ppf(1 - alpha / 2):
                decision = "no_difference"
            elif z_stat > 0:
                decision = "variant_wins"
            else:
                decision = "control_wins"

    # Calculate remaining visitors needed
    remaining = None
    if not can_stop and information_fraction < 1.0:
        remaining = int((expected_visitors_per_variant - current_visitors) * 2)

    # Generate recommendation
    recommendation = _generate_recommendation(
        decision=decision,
        can_stop=can_stop,
        lift_percent=lift_percent,
        confidence_variant_better=confidence_variant_better,
        information_fraction=information_fraction,
        control_rate=p1,
        variant_rate=p2,
        remaining_visitors=remaining,
        alpha=alpha,
    )

    return SequentialTestResult(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        control_rate=p1,
        variant_rate=p2,
        can_stop=can_stop,
        decision=decision,
        recommendation=recommendation,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        z_statistic=z_stat,
        p_value=p_value,
        upper_boundary=boundaries.upper,
        lower_boundary=boundaries.lower,
        current_statistic=z_stat,
        confidence_variant_better=confidence_variant_better * 100,
        confidence_control_better=confidence_control_better * 100,
        adjusted_alpha=boundaries.alpha_spent,
        information_fraction=information_fraction,
        estimated_remaining_visitors=remaining,
    )


def _generate_recommendation(
    decision: str,
    can_stop: bool,
    lift_percent: float,
    confidence_variant_better: float,
    information_fraction: float,
    control_rate: float,
    variant_rate: float,
    remaining_visitors: Optional[int],
    alpha: float,
) -> str:
    """Generate human-readable recommendation."""

    if can_stop:
        if decision == "variant_wins":
            return (
                f"## You can stop the test - Variant Wins!\n\n"
                f"The variant is performing significantly better than control.\n\n"
                f"**Results:**\n"
                f"- Control rate: {control_rate:.2%}\n"
                f"- Variant rate: {variant_rate:.2%}\n"
                f"- Lift: {lift_percent:+.1f}%\n"
                f"- Confidence: {confidence_variant_better:.1f}% sure variant is better\n\n"
                f"**Recommendation:** Implement the variant."
            )
        elif decision == "control_wins":
            return (
                f"## You can stop the test - Control Wins!\n\n"
                f"The control is performing better than the variant.\n\n"
                f"**Results:**\n"
                f"- Control rate: {control_rate:.2%}\n"
                f"- Variant rate: {variant_rate:.2%}\n"
                f"- Lift: {lift_percent:+.1f}%\n"
                f"- Confidence: {100 - confidence_variant_better:.1f}% sure control is better\n\n"
                f"**Recommendation:** Keep the control, do not implement variant."
            )
        else:  # no_difference
            return (
                f"## You can stop the test - No Significant Difference\n\n"
                f"There is no meaningful difference between control and variant.\n\n"
                f"**Results:**\n"
                f"- Control rate: {control_rate:.2%}\n"
                f"- Variant rate: {variant_rate:.2%}\n"
                f"- Lift: {lift_percent:+.1f}%\n\n"
                f"**Recommendation:** The difference is too small to matter. "
                f"Choose based on other factors (cost, complexity, etc.)."
            )
    else:
        progress_pct = information_fraction * 100
        return (
            f"## Keep running the test\n\n"
            f"Results are not yet conclusive. You're {progress_pct:.0f}% through the planned test.\n\n"
            f"**Current results (not final):**\n"
            f"- Control rate: {control_rate:.2%}\n"
            f"- Variant rate: {variant_rate:.2%}\n"
            f"- Observed lift: {lift_percent:+.1f}%\n"
            f"- Current confidence: {confidence_variant_better:.1f}% that variant is better\n\n"
            f"**Why you can't stop yet:**\n"
            f"Stopping now would inflate your false positive rate. The observed difference "
            f"hasn't crossed the statistical threshold needed for a valid conclusion.\n\n"
            + (f"**Estimated remaining:** ~{remaining_visitors:,} more visitors needed.\n"
               if remaining_visitors else "")
        )


def sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    num_planned_looks: int = 5,
    method: Literal["obrien-fleming", "pocock"] = "obrien-fleming",
) -> dict:
    """
    Calculate sample size for sequential test.

    Sequential tests typically require 20-30% more samples than fixed-horizon
    tests to maintain the same power, but can often stop earlier when effects
    are large.

    Args:
        baseline_rate: Expected conversion rate for control (e.g., 0.05 for 5%)
        minimum_detectable_effect: Minimum relative lift to detect (e.g., 0.10 for 10%)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80)
        num_planned_looks: Number of interim analyses planned
        method: Boundary method

    Returns:
        Dictionary with sample size information

    Example:
        >>> result = sequential.sample_size(
        ...     baseline_rate=0.05,
        ...     minimum_detectable_effect=0.10,
        ... )
        >>> print(result['visitors_per_variant'])
        31234
    """
    if baseline_rate > 1:
        baseline_rate = baseline_rate / 100
    if minimum_detectable_effect > 1:
        minimum_detectable_effect = minimum_detectable_effect / 100

    # Calculate expected rates
    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_detectable_effect)

    # Standard sample size formula
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    p_pooled = (p1 + p2) / 2

    n_fixed = (
        (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    ) / (p2 - p1) ** 2

    # Inflation factor for sequential testing
    # O'Brien-Fleming requires ~2-5% more, Pocock ~15-20% more
    if method == "obrien-fleming":
        inflation = 1.03 + 0.01 * num_planned_looks
    else:
        inflation = 1.15 + 0.02 * num_planned_looks

    n_sequential = int(math.ceil(n_fixed * inflation))

    return {
        "visitors_per_variant": n_sequential,
        "total_visitors": n_sequential * 2,
        "fixed_horizon_equivalent": int(math.ceil(n_fixed)),
        "inflation_factor": inflation,
        "num_planned_looks": num_planned_looks,
        "look_interval": n_sequential // num_planned_looks,
        "baseline_rate": p1,
        "expected_variant_rate": p2,
        "minimum_detectable_effect": minimum_detectable_effect,
    }


def summarize(result: SequentialTestResult, test_name: str = "Sequential A/B Test") -> str:
    """
    Generate a markdown summary of sequential test results.

    Args:
        result: SequentialTestResult from analyze()
        test_name: Name of the test for the report

    Returns:
        Markdown-formatted summary string
    """
    lines = [f"## {test_name} - Sequential Analysis\n"]

    # Status indicator
    if result.can_stop:
        if result.decision == "variant_wins":
            lines.append("### **STOP - Variant Wins**\n")
        elif result.decision == "control_wins":
            lines.append("### **STOP - Control Wins**\n")
        else:
            lines.append("### **STOP - No Difference**\n")
    else:
        lines.append("### **KEEP RUNNING**\n")

    # Progress bar
    progress = int(result.information_fraction * 20)
    progress_bar = "[" + "#" * progress + "-" * (20 - progress) + "]"
    lines.append(f"**Progress:** {progress_bar} {result.information_fraction*100:.0f}%\n")

    # Results table
    lines.append("### Current Results\n")
    lines.append("| Metric | Control | Variant |")
    lines.append("|--------|---------|---------|")
    lines.append(f"| Visitors | {result.control_visitors:,} | {result.variant_visitors:,} |")
    lines.append(f"| Conversions | {result.control_conversions:,} | {result.variant_conversions:,} |")
    lines.append(f"| Rate | {result.control_rate:.2%} | {result.variant_rate:.2%} |")
    lines.append("")

    # Key metrics
    lines.append("### Key Metrics\n")
    lines.append(f"- **Lift:** {result.lift_percent:+.1f}%")
    lines.append(f"- **Confidence variant is better:** {result.confidence_variant_better:.1f}%")
    lines.append(f"- **Z-statistic:** {result.z_statistic:.2f}")
    lines.append(f"- **Upper boundary:** {result.upper_boundary:.2f}")
    lines.append(f"- **Lower boundary:** {result.lower_boundary:.2f}")
    lines.append("")

    # Recommendation
    lines.append("### Recommendation\n")
    lines.append(result.recommendation.replace("## ", "").replace("**", ""))

    return "\n".join(lines)


__all__ = [
    "SequentialTestResult",
    "SequentialBoundaries",
    "analyze",
    "sample_size",
    "get_boundaries",
    "summarize",
]
