"""
Novelty Effect Detection.

Detects if an A/B test effect is fading over time (novelty effect) or
growing (primacy effect). This is crucial because:

- Novelty effect: Users initially react to changes (good or bad) but
  behavior normalizes over time. A 30% lift in week 1 might be 5% in week 4.

- Primacy effect: Users take time to discover/adapt to changes, and the
  effect grows over time.

Detecting these patterns helps you understand the true long-term impact.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal
import numpy as np
from scipy import stats as scipy_stats


@dataclass
class DailyResult:
    """Single day's results."""
    day: int
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    control_rate: float
    variant_rate: float
    lift_percent: float


@dataclass
class NoveltyEffectResult:
    """Results from novelty effect analysis."""

    # Detection results
    effect_detected: bool
    effect_type: Literal["novelty", "primacy", "stable", "insufficient_data"]

    # Trend analysis
    initial_lift: float  # Lift in first period
    current_lift: float  # Lift in most recent period
    trend_slope: float   # Slope of lift over time (negative = fading)
    trend_p_value: float

    # Projections
    projected_steady_state_lift: Optional[float]  # Projected long-term lift
    days_to_steady_state: Optional[int]

    # Confidence
    confidence: float  # Confidence in the trend detection

    # Raw data
    daily_lifts: List[float]
    smoothed_lifts: List[float]

    # Recommendations
    warning: str
    recommendation: str


def detect_novelty_effect(
    daily_results: List[dict],
    min_days: int = 7,
    trend_threshold: float = 0.1,  # 10% change per week considered significant
    smoothing_window: int = 3,
) -> NoveltyEffectResult:
    """
    Detect if the experiment effect is changing over time.

    Args:
        daily_results: List of daily results, each with:
            - day: Day number (1, 2, 3, ...)
            - control_visitors: Visitors in control
            - control_conversions: Conversions in control
            - variant_visitors: Visitors in variant
            - variant_conversions: Conversions in variant
        min_days: Minimum days of data needed for analysis
        trend_threshold: Weekly change threshold to consider significant
        smoothing_window: Days for moving average smoothing

    Returns:
        NoveltyEffectResult with trend analysis and recommendations

    Example:
        >>> result = detect_novelty_effect([
        ...     {"day": 1, "control_visitors": 1000, "control_conversions": 50,
        ...      "variant_visitors": 1000, "variant_conversions": 65},
        ...     {"day": 2, "control_visitors": 1000, "control_conversions": 48,
        ...      "variant_visitors": 1000, "variant_conversions": 60},
        ...     # ... more days
        ... ])
        >>> print(result.effect_type)
        'novelty'
    """
    if len(daily_results) < min_days:
        return NoveltyEffectResult(
            effect_detected=False,
            effect_type="insufficient_data",
            initial_lift=0,
            current_lift=0,
            trend_slope=0,
            trend_p_value=1.0,
            projected_steady_state_lift=None,
            days_to_steady_state=None,
            confidence=0,
            daily_lifts=[],
            smoothed_lifts=[],
            warning=f"Need at least {min_days} days of data. Currently have {len(daily_results)}.",
            recommendation="Continue running the test to gather more data for trend analysis.",
        )

    # Calculate daily lifts
    daily_lifts = []
    processed_results = []

    for day_data in daily_results:
        day = day_data.get("day", len(daily_lifts) + 1)
        c_visitors = day_data["control_visitors"]
        c_conv = day_data["control_conversions"]
        v_visitors = day_data["variant_visitors"]
        v_conv = day_data["variant_conversions"]

        if c_visitors > 0 and v_visitors > 0:
            c_rate = c_conv / c_visitors
            v_rate = v_conv / v_visitors
            lift = ((v_rate - c_rate) / c_rate * 100) if c_rate > 0 else 0

            daily_lifts.append(lift)
            processed_results.append(DailyResult(
                day=day,
                control_visitors=c_visitors,
                control_conversions=c_conv,
                variant_visitors=v_visitors,
                variant_conversions=v_conv,
                control_rate=c_rate,
                variant_rate=v_rate,
                lift_percent=lift,
            ))

    if len(daily_lifts) < min_days:
        return NoveltyEffectResult(
            effect_detected=False,
            effect_type="insufficient_data",
            initial_lift=daily_lifts[0] if daily_lifts else 0,
            current_lift=daily_lifts[-1] if daily_lifts else 0,
            trend_slope=0,
            trend_p_value=1.0,
            projected_steady_state_lift=None,
            days_to_steady_state=None,
            confidence=0,
            daily_lifts=daily_lifts,
            smoothed_lifts=daily_lifts,
            warning=f"Insufficient valid daily data points ({len(daily_lifts)} < {min_days}).",
            recommendation="Check for days with zero traffic and ensure data quality.",
        )

    # Calculate smoothed lifts (moving average)
    smoothed_lifts = []
    for i in range(len(daily_lifts)):
        start = max(0, i - smoothing_window + 1)
        window = daily_lifts[start:i+1]
        smoothed_lifts.append(sum(window) / len(window))

    # Calculate initial and current lift (using smoothed values)
    initial_lift = sum(daily_lifts[:min(3, len(daily_lifts))]) / min(3, len(daily_lifts))
    current_lift = sum(daily_lifts[-3:]) / min(3, len(daily_lifts))

    # Linear regression on lift over time
    days = np.arange(1, len(daily_lifts) + 1)
    lifts = np.array(daily_lifts)

    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(days, lifts)

    # Convert slope to weekly change
    weekly_change = slope * 7

    # Determine effect type
    stability_threshold = trend_threshold * abs(initial_lift) if initial_lift != 0 else 0.5
    if abs(weekly_change) < stability_threshold:
        effect_type = "stable"
        effect_detected = False
    elif weekly_change < 0:
        effect_type = "novelty"
        effect_detected = True
    else:
        effect_type = "primacy"
        effect_detected = True

    # Project steady state (if novelty effect)
    projected_steady_state = None
    days_to_steady = None

    if effect_type == "novelty" and slope < 0:
        # Project when lift will stabilize (approach asymptote)
        # Simple model: assume exponential decay to some baseline
        if initial_lift > 0 and current_lift > 0:
            decay_rate = (initial_lift - current_lift) / initial_lift
            if decay_rate > 0 and decay_rate < 1:
                # Estimate steady state as current trend extrapolated
                projected_steady_state = max(0, current_lift + slope * 14)  # 2 weeks out
                if slope != 0:
                    days_to_steady = int(abs(current_lift / slope)) if slope != 0 else None

    # Calculate confidence based on R-squared and p-value
    confidence = (1 - p_value) * r_value ** 2 * 100 if p_value < 0.05 else 0

    # Generate warning and recommendation
    warning, recommendation = _generate_warnings(
        effect_type=effect_type,
        initial_lift=initial_lift,
        current_lift=current_lift,
        weekly_change=weekly_change,
        confidence=confidence,
        projected_steady_state=projected_steady_state,
    )

    return NoveltyEffectResult(
        effect_detected=effect_detected,
        effect_type=effect_type,
        initial_lift=initial_lift,
        current_lift=current_lift,
        trend_slope=slope,
        trend_p_value=p_value,
        projected_steady_state_lift=projected_steady_state,
        days_to_steady_state=days_to_steady,
        confidence=confidence,
        daily_lifts=daily_lifts,
        smoothed_lifts=smoothed_lifts,
        warning=warning,
        recommendation=recommendation,
    )


def _generate_warnings(
    effect_type: str,
    initial_lift: float,
    current_lift: float,
    weekly_change: float,
    confidence: float,
    projected_steady_state: Optional[float],
) -> Tuple[str, str]:
    """Generate warning and recommendation based on effect type."""

    if effect_type == "novelty":
        warning = (
            f"NOVELTY EFFECT DETECTED: Lift has faded from {initial_lift:+.1f}% to {current_lift:+.1f}% "
            f"(declining ~{abs(weekly_change):.1f}% per week)."
        )
        if projected_steady_state is not None:
            recommendation = (
                f"The effect appears to be wearing off. Projected steady-state lift: ~{projected_steady_state:+.1f}%.\n\n"
                f"**What this means:**\n"
                f"- Users may have initially reacted to the novelty of the change\n"
                f"- The long-term impact is likely smaller than early results suggest\n"
                f"- Consider running longer to see where the effect stabilizes\n\n"
                f"**Recommendation:** If steady-state lift is still valuable, proceed. "
                f"Otherwise, reconsider the change."
            )
        else:
            recommendation = (
                f"The effect is declining over time. Run the test longer to see where it stabilizes."
            )

    elif effect_type == "primacy":
        warning = (
            f"PRIMACY EFFECT DETECTED: Lift has grown from {initial_lift:+.1f}% to {current_lift:+.1f}% "
            f"(increasing ~{weekly_change:+.1f}% per week)."
        )
        recommendation = (
            f"The effect is growing over time. This could mean:\n"
            f"- Users are discovering the change and adapting positively\n"
            f"- The benefit compounds with usage\n\n"
            f"**Recommendation:** This is typically a good sign. Continue running to see "
            f"if growth continues or stabilizes."
        )

    elif effect_type == "stable":
        warning = "Effect is STABLE over time - no significant trend detected."
        recommendation = (
            f"The effect ({current_lift:+.1f}%) appears consistent over time. "
            f"You can trust this as a reliable estimate of long-term impact."
        )

    else:  # insufficient_data
        warning = "Insufficient data for trend analysis."
        recommendation = "Continue running the test to enable trend detection."

    return warning, recommendation


def summarize(result: NoveltyEffectResult, test_name: str = "A/B Test") -> str:
    """Generate markdown summary of novelty effect analysis."""
    lines = [f"## Novelty Effect Analysis - {test_name}\n"]

    # Status
    if result.effect_type == "novelty":
        lines.append("### Effect is FADING Over Time\n")
    elif result.effect_type == "primacy":
        lines.append("### Effect is GROWING Over Time\n")
    elif result.effect_type == "stable":
        lines.append("### Effect is STABLE Over Time\n")
    else:
        lines.append("### Insufficient Data for Trend Analysis\n")

    # Trend visualization (simple ASCII)
    if result.daily_lifts:
        lines.append("### Lift Over Time\n")
        lines.append("```")
        max_lift = max(abs(l) for l in result.daily_lifts) if result.daily_lifts else 1
        for i, lift in enumerate(result.smoothed_lifts):
            bar_len = int(abs(lift) / max_lift * 20) if max_lift > 0 else 0
            bar = "█" * bar_len
            lines.append(f"Day {i+1:2d}: {lift:+6.1f}% |{bar}")
        lines.append("```\n")

    # Key metrics
    lines.append("### Key Metrics\n")
    lines.append(f"- **Initial lift:** {result.initial_lift:+.1f}%")
    lines.append(f"- **Current lift:** {result.current_lift:+.1f}%")
    lines.append(f"- **Weekly trend:** {result.trend_slope * 7:+.2f}% per week")
    if result.projected_steady_state_lift is not None:
        lines.append(f"- **Projected steady state:** {result.projected_steady_state_lift:+.1f}%")
    lines.append(f"- **Trend confidence:** {result.confidence:.0f}%")
    lines.append("")

    # Warning and recommendation
    lines.append("### Analysis\n")
    lines.append(f"**{result.warning}**\n")
    lines.append(result.recommendation)

    return "\n".join(lines)


__all__ = [
    "NoveltyEffectResult",
    "DailyResult",
    "detect_novelty_effect",
    "summarize",
]
