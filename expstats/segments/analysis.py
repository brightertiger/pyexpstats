"""
Segment Analysis for A/B Tests.

Analyzes how A/B test results vary across user segments (e.g., mobile vs desktop,
new vs returning users, by country, etc.).

Important considerations:
- Multiple comparisons problem (Bonferroni correction)
- Simpson's Paradox detection
- Sample size requirements per segment
- Heterogeneous treatment effects
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Literal
from scipy import stats as scipy_stats
from scipy.stats import norm, chi2_contingency


@dataclass
class SegmentResult:
    """Results for a single segment."""

    segment_name: str
    segment_value: str

    # Sample sizes
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int

    # Rates
    control_rate: float
    variant_rate: float

    # Effect
    lift_percent: float
    lift_ci_lower: float
    lift_ci_upper: float

    # Statistical significance
    p_value: float
    is_significant: bool  # After correction
    is_significant_uncorrected: bool

    # Interpretation
    winner: Literal["variant", "control", "no_difference"]
    sample_size_adequate: bool
    interpretation: str


@dataclass
class SegmentAnalysisReport:
    """Complete segment analysis report."""

    # Overall results
    overall_lift: float
    overall_is_significant: bool

    # Segment results
    segments: List[SegmentResult]
    n_segments: int

    # Key findings
    best_segment: Optional[str]
    worst_segment: Optional[str]
    heterogeneity_detected: bool
    simpsons_paradox_risk: bool

    # Correction info
    correction_method: str
    adjusted_alpha: float

    # Summary
    recommendation: str


def analyze_segments(
    segments_data: List[dict],
    confidence: int = 95,
    correction_method: Literal["bonferroni", "holm", "none"] = "bonferroni",
    min_sample_per_segment: int = 100,
) -> SegmentAnalysisReport:
    """
    Analyze A/B test results across multiple segments.

    Args:
        segments_data: List of segment data, each containing:
            - segment_name: Name of segment dimension (e.g., "device")
            - segment_value: Value of segment (e.g., "mobile")
            - control_visitors: Visitors in control
            - control_conversions: Conversions in control
            - variant_visitors: Visitors in variant
            - variant_conversions: Conversions in variant
        confidence: Confidence level (default 95)
        correction_method: Method for multiple comparison correction
        min_sample_per_segment: Minimum sample per segment for valid analysis

    Returns:
        SegmentAnalysisReport with detailed segment-level analysis

    Example:
        >>> report = analyze_segments([
        ...     {
        ...         "segment_name": "device",
        ...         "segment_value": "mobile",
        ...         "control_visitors": 5000,
        ...         "control_conversions": 250,
        ...         "variant_visitors": 5000,
        ...         "variant_conversions": 300,
        ...     },
        ...     {
        ...         "segment_name": "device",
        ...         "segment_value": "desktop",
        ...         "control_visitors": 3000,
        ...         "control_conversions": 180,
        ...         "variant_visitors": 3000,
        ...         "variant_conversions": 200,
        ...     },
        ... ])
        >>> print(f"Best segment: {report.best_segment}")
    """
    n_segments = len(segments_data)
    alpha = 1 - confidence / 100

    # Calculate adjusted alpha for multiple comparisons
    if correction_method == "bonferroni":
        adjusted_alpha = alpha / n_segments if n_segments > 0 else alpha
    elif correction_method == "holm":
        # Holm-Bonferroni is applied after sorting p-values
        adjusted_alpha = alpha  # Will be applied per-test
    else:
        adjusted_alpha = alpha

    # Analyze each segment
    segment_results = []
    p_values = []

    for seg_data in segments_data:
        result = _analyze_single_segment(
            seg_data, alpha, adjusted_alpha, min_sample_per_segment
        )
        segment_results.append(result)
        p_values.append(result.p_value)

    # Apply Holm-Bonferroni correction if specified
    if correction_method == "holm":
        segment_results = _apply_holm_correction(segment_results, alpha)

    # Calculate overall results
    total_control_visitors = sum(s["control_visitors"] for s in segments_data)
    total_control_conversions = sum(s["control_conversions"] for s in segments_data)
    total_variant_visitors = sum(s["variant_visitors"] for s in segments_data)
    total_variant_conversions = sum(s["variant_conversions"] for s in segments_data)

    overall_control_rate = (
        total_control_conversions / total_control_visitors
        if total_control_visitors > 0 else 0
    )
    overall_variant_rate = (
        total_variant_conversions / total_variant_visitors
        if total_variant_visitors > 0 else 0
    )
    overall_lift = (
        ((overall_variant_rate - overall_control_rate) / overall_control_rate * 100)
        if overall_control_rate > 0 else 0
    )

    # Test overall significance
    contingency = [
        [total_control_conversions, total_control_visitors - total_control_conversions],
        [total_variant_conversions, total_variant_visitors - total_variant_conversions],
    ]
    try:
        _, overall_p_value, _, _ = chi2_contingency(contingency)
        overall_is_significant = overall_p_value < alpha
    except ValueError:
        overall_is_significant = False

    # Find best and worst segments
    significant_segments = [s for s in segment_results if s.is_significant]
    if significant_segments:
        best_segment = max(significant_segments, key=lambda s: s.lift_percent)
        worst_segment = min(significant_segments, key=lambda s: s.lift_percent)
        best_segment_name = f"{best_segment.segment_name}={best_segment.segment_value}"
        worst_segment_name = f"{worst_segment.segment_name}={worst_segment.segment_value}"
    else:
        best_segment_name = None
        worst_segment_name = None

    # Check for heterogeneity (different effects across segments)
    heterogeneity = _detect_heterogeneity(segment_results)

    # Check for Simpson's Paradox
    simpsons_paradox = _check_simpsons_paradox(segment_results, overall_lift)

    # Generate recommendation
    recommendation = _generate_recommendation(
        segment_results=segment_results,
        overall_lift=overall_lift,
        overall_is_significant=overall_is_significant,
        best_segment=best_segment_name,
        worst_segment=worst_segment_name,
        heterogeneity=heterogeneity,
        simpsons_paradox=simpsons_paradox,
        correction_method=correction_method,
    )

    return SegmentAnalysisReport(
        overall_lift=overall_lift,
        overall_is_significant=overall_is_significant,
        segments=segment_results,
        n_segments=n_segments,
        best_segment=best_segment_name,
        worst_segment=worst_segment_name,
        heterogeneity_detected=heterogeneity,
        simpsons_paradox_risk=simpsons_paradox,
        correction_method=correction_method,
        adjusted_alpha=adjusted_alpha,
        recommendation=recommendation,
    )


def _analyze_single_segment(
    seg_data: dict,
    alpha: float,
    adjusted_alpha: float,
    min_sample: int,
) -> SegmentResult:
    """Analyze a single segment."""
    segment_name = seg_data["segment_name"]
    segment_value = seg_data["segment_value"]
    c_visitors = seg_data["control_visitors"]
    c_conversions = seg_data["control_conversions"]
    v_visitors = seg_data["variant_visitors"]
    v_conversions = seg_data["variant_conversions"]

    # Calculate rates
    c_rate = c_conversions / c_visitors if c_visitors > 0 else 0
    v_rate = v_conversions / v_visitors if v_visitors > 0 else 0

    # Calculate lift
    if c_rate > 0:
        lift = ((v_rate - c_rate) / c_rate) * 100
    else:
        lift = 0 if v_rate == 0 else float('inf')

    # Statistical test
    contingency = [
        [c_conversions, c_visitors - c_conversions],
        [v_conversions, v_visitors - v_conversions],
    ]

    try:
        _, p_value, _, _ = chi2_contingency(contingency)
    except ValueError:
        p_value = 1.0

    # Confidence interval for lift
    se_c = math.sqrt(c_rate * (1 - c_rate) / c_visitors) if c_visitors > 0 and 0 < c_rate < 1 else 0
    se_v = math.sqrt(v_rate * (1 - v_rate) / v_visitors) if v_visitors > 0 and 0 < v_rate < 1 else 0
    se_diff = math.sqrt(se_c**2 + se_v**2)

    z_crit = norm.ppf(1 - alpha / 2)
    diff = v_rate - c_rate
    diff_lower = diff - z_crit * se_diff
    diff_upper = diff + z_crit * se_diff

    # Convert to relative lift CI
    if c_rate > 0:
        lift_ci_lower = (diff_lower / c_rate) * 100
        lift_ci_upper = (diff_upper / c_rate) * 100
    else:
        lift_ci_lower = 0
        lift_ci_upper = 0

    # Significance (with and without correction)
    is_significant_uncorrected = p_value < alpha
    is_significant = p_value < adjusted_alpha

    # Determine winner
    if is_significant:
        winner = "variant" if lift > 0 else "control"
    else:
        winner = "no_difference"

    # Check sample size adequacy
    min_visitors = min(c_visitors, v_visitors)
    sample_adequate = min_visitors >= min_sample

    # Generate interpretation
    interpretation = _interpret_segment(
        segment_name, segment_value, lift, is_significant,
        is_significant_uncorrected, sample_adequate, p_value
    )

    return SegmentResult(
        segment_name=segment_name,
        segment_value=segment_value,
        control_visitors=c_visitors,
        control_conversions=c_conversions,
        variant_visitors=v_visitors,
        variant_conversions=v_conversions,
        control_rate=c_rate,
        variant_rate=v_rate,
        lift_percent=lift,
        lift_ci_lower=lift_ci_lower,
        lift_ci_upper=lift_ci_upper,
        p_value=p_value,
        is_significant=is_significant,
        is_significant_uncorrected=is_significant_uncorrected,
        winner=winner,
        sample_size_adequate=sample_adequate,
        interpretation=interpretation,
    )


def _apply_holm_correction(
    results: List[SegmentResult],
    alpha: float,
) -> List[SegmentResult]:
    """Apply Holm-Bonferroni correction to segment results."""
    n = len(results)
    # Sort by p-value
    sorted_indices = sorted(range(n), key=lambda i: results[i].p_value)

    # Apply Holm correction
    for rank, idx in enumerate(sorted_indices):
        adjusted_alpha = alpha / (n - rank)
        result = results[idx]
        # Update significance based on Holm threshold
        is_significant = result.p_value < adjusted_alpha
        # Create new result with updated significance
        results[idx] = SegmentResult(
            segment_name=result.segment_name,
            segment_value=result.segment_value,
            control_visitors=result.control_visitors,
            control_conversions=result.control_conversions,
            variant_visitors=result.variant_visitors,
            variant_conversions=result.variant_conversions,
            control_rate=result.control_rate,
            variant_rate=result.variant_rate,
            lift_percent=result.lift_percent,
            lift_ci_lower=result.lift_ci_lower,
            lift_ci_upper=result.lift_ci_upper,
            p_value=result.p_value,
            is_significant=is_significant,
            is_significant_uncorrected=result.is_significant_uncorrected,
            winner=result.winner if is_significant else "no_difference",
            sample_size_adequate=result.sample_size_adequate,
            interpretation=result.interpretation,
        )
        # Holm requires rejection in order - if one fails, all subsequent fail
        if not is_significant:
            for remaining_idx in sorted_indices[rank:]:
                r = results[remaining_idx]
                results[remaining_idx] = SegmentResult(
                    segment_name=r.segment_name,
                    segment_value=r.segment_value,
                    control_visitors=r.control_visitors,
                    control_conversions=r.control_conversions,
                    variant_visitors=r.variant_visitors,
                    variant_conversions=r.variant_conversions,
                    control_rate=r.control_rate,
                    variant_rate=r.variant_rate,
                    lift_percent=r.lift_percent,
                    lift_ci_lower=r.lift_ci_lower,
                    lift_ci_upper=r.lift_ci_upper,
                    p_value=r.p_value,
                    is_significant=False,
                    is_significant_uncorrected=r.is_significant_uncorrected,
                    winner="no_difference",
                    sample_size_adequate=r.sample_size_adequate,
                    interpretation=r.interpretation,
                )
            break

    return results


def _detect_heterogeneity(results: List[SegmentResult]) -> bool:
    """Detect if there's significant heterogeneity across segments."""
    if len(results) < 2:
        return False

    lifts = [r.lift_percent for r in results if r.sample_size_adequate]
    if len(lifts) < 2:
        return False

    # Check if some segments have opposite signs
    positive = sum(1 for l in lifts if l > 5)  # >5% lift
    negative = sum(1 for l in lifts if l < -5)  # <-5% lift

    # Heterogeneity if some segments strongly positive and some strongly negative
    if positive > 0 and negative > 0:
        return True

    # Also check variance of lifts
    mean_lift = sum(lifts) / len(lifts)
    variance = sum((l - mean_lift)**2 for l in lifts) / len(lifts)
    std_lift = math.sqrt(variance)

    # High variance relative to mean suggests heterogeneity
    return std_lift > abs(mean_lift) * 0.5 if mean_lift != 0 else std_lift > 10


def _check_simpsons_paradox(results: List[SegmentResult], overall_lift: float) -> bool:
    """Check for Simpson's Paradox - when segment trends oppose overall trend."""
    if len(results) < 2:
        return False

    # Get direction of overall effect
    overall_positive = overall_lift > 0

    # Check if most segments have opposite direction
    adequate_results = [r for r in results if r.sample_size_adequate]
    if len(adequate_results) < 2:
        return False

    segment_positive = sum(1 for r in adequate_results if r.lift_percent > 0)
    segment_negative = sum(1 for r in adequate_results if r.lift_percent < 0)

    # Simpson's paradox if overall is positive but majority of segments are negative (or vice versa)
    if overall_positive and segment_negative > segment_positive:
        return True
    if not overall_positive and overall_lift < 0 and segment_positive > segment_negative:
        return True

    return False


def _interpret_segment(
    segment_name: str,
    segment_value: str,
    lift: float,
    is_significant: bool,
    is_significant_uncorrected: bool,
    sample_adequate: bool,
    p_value: float,
) -> str:
    """Generate interpretation for a single segment."""
    if not sample_adequate:
        return (
            f"Insufficient sample size for {segment_name}={segment_value}. "
            f"Results are not reliable."
        )

    direction = "outperforms" if lift > 0 else "underperforms"
    if is_significant:
        return (
            f"Variant {direction} control by {abs(lift):.1f}% in {segment_name}={segment_value} "
            f"(statistically significant, p={p_value:.4f})."
        )
    elif is_significant_uncorrected:
        return (
            f"Variant {direction} control by {abs(lift):.1f}% in {segment_name}={segment_value} "
            f"(significant before correction, p={p_value:.4f}). Interpret with caution."
        )
    else:
        return (
            f"No significant difference in {segment_name}={segment_value} "
            f"(lift: {lift:+.1f}%, p={p_value:.4f})."
        )


def _generate_recommendation(
    segment_results: List[SegmentResult],
    overall_lift: float,
    overall_is_significant: bool,
    best_segment: Optional[str],
    worst_segment: Optional[str],
    heterogeneity: bool,
    simpsons_paradox: bool,
    correction_method: str,
) -> str:
    """Generate overall recommendation based on segment analysis."""
    lines = []

    lines.append("## Segment Analysis Report\n")

    # Summary table
    lines.append("### Segment Results\n")
    lines.append("| Segment | Lift | Significant? | Winner |")
    lines.append("|---------|------|--------------|--------|")
    for result in segment_results:
        sig = "Yes" if result.is_significant else ("~" if result.is_significant_uncorrected else "No")
        lines.append(
            f"| {result.segment_name}={result.segment_value} | "
            f"{result.lift_percent:+.1f}% | {sig} | {result.winner} |"
        )
    lines.append("")

    # Overall result
    lines.append("### Overall Result\n")
    overall_sig = "statistically significant" if overall_is_significant else "not statistically significant"
    lines.append(f"- **Overall lift:** {overall_lift:+.1f}% ({overall_sig})")
    lines.append(f"- **Correction method:** {correction_method}")
    lines.append("")

    # Key findings
    if best_segment:
        lines.append(f"- **Best performing segment:** {best_segment}")
    if worst_segment and worst_segment != best_segment:
        lines.append(f"- **Worst performing segment:** {worst_segment}")
    lines.append("")

    # Warnings
    if simpsons_paradox:
        lines.append("### Simpson's Paradox Warning\n")
        lines.append(
            "The overall result has a different direction than most individual segments. "
            "This can happen when segment sizes are imbalanced. Be very careful about "
            "generalizing the overall result - the effect may vary significantly by segment."
        )
        lines.append("")

    if heterogeneity:
        lines.append("### Heterogeneity Detected\n")
        lines.append(
            "The variant effect varies significantly across segments. Some segments "
            "benefit while others may be harmed. Consider:\n"
            "- Targeting only segments where the variant performs well\n"
            "- Investigating why certain segments respond differently\n"
            "- Running segment-specific follow-up tests"
        )
        lines.append("")

    # Final recommendation
    lines.append("### Recommendation\n")

    if simpsons_paradox:
        lines.append(
            "**INVESTIGATE FURTHER** - Simpson's Paradox detected. The overall result "
            "may be misleading. Analyze segment-level data carefully before making decisions."
        )
    elif heterogeneity:
        lines.append(
            "**CONSIDER TARGETED ROLLOUT** - The variant effect varies by segment. "
            "Consider rolling out only to segments where it performs well, or investigate "
            "the source of heterogeneity."
        )
    elif overall_is_significant and overall_lift > 0:
        lines.append(
            "**SHIP TO ALL SEGMENTS** - The variant wins consistently across segments. "
            "Proceed with confidence."
        )
    elif overall_is_significant and overall_lift < 0:
        lines.append(
            "**DO NOT SHIP** - The variant underperforms consistently. "
            "The control is the better experience."
        )
    else:
        lines.append(
            "**NO CLEAR WINNER** - Results are not statistically significant overall or "
            "across segments. Consider running longer or focusing on specific segments."
        )

    return "\n".join(lines)


def summarize(report: SegmentAnalysisReport) -> str:
    """Generate markdown summary of segment analysis."""
    return report.recommendation


__all__ = [
    "SegmentResult",
    "SegmentAnalysisReport",
    "analyze_segments",
    "summarize",
]
