"""
Test Duration Recommendations.

Helps determine how long to run an A/B test, considering:
- Statistical requirements (sample size)
- Business cycles (weekly patterns, monthly patterns)
- Novelty effects
- Practical constraints
"""

import math
from dataclasses import dataclass
from typing import Optional, List, Literal
from scipy.stats import norm


@dataclass
class DurationRecommendation:
    """Recommendation for test duration."""

    # Primary recommendation
    recommended_days: int
    minimum_days: int
    ideal_days: int

    # Breakdown
    statistical_minimum_days: int  # Based on sample size
    weekly_cycle_days: int  # To capture day-of-week effects
    monthly_consideration: bool  # Whether monthly patterns matter

    # Sample size info
    required_sample_per_variant: int
    expected_sample_per_variant: int

    # Risk assessment
    risk_if_stopped_early: str
    confidence_at_minimum: float
    confidence_at_recommended: float

    # Recommendation text
    recommendation: str


def recommend_duration(
    baseline_rate: float,
    minimum_detectable_effect: float,
    daily_traffic: int,
    confidence: int = 95,
    power: int = 80,
    include_weekly_cycle: bool = True,
    include_monthly_cycle: bool = False,
    business_type: Literal["ecommerce", "saas", "content", "other"] = "other",
) -> DurationRecommendation:
    """
    Get recommendations for how long to run your A/B test.

    Args:
        baseline_rate: Expected conversion rate (e.g., 0.05 for 5%)
        minimum_detectable_effect: MDE as relative lift (e.g., 0.10 for 10%)
        daily_traffic: Total daily visitors to the test
        confidence: Confidence level (default 95)
        power: Statistical power (default 80)
        include_weekly_cycle: Require at least 1 full week (default True)
        include_monthly_cycle: Require consideration of monthly patterns
        business_type: Type of business (affects recommendations)

    Returns:
        DurationRecommendation with detailed guidance

    Example:
        >>> result = recommend_duration(
        ...     baseline_rate=0.05,
        ...     minimum_detectable_effect=0.10,
        ...     daily_traffic=5000,
        ... )
        >>> print(f"Run for at least {result.recommended_days} days")
    """
    # Handle percentage inputs
    if baseline_rate > 1:
        baseline_rate = baseline_rate / 100
    if minimum_detectable_effect > 1:
        minimum_detectable_effect = minimum_detectable_effect / 100

    # Calculate required sample size
    alpha = 1 - confidence / 100
    beta = 1 - power / 100

    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)

    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_detectable_effect)
    p_pooled = (p1 + p2) / 2

    required_n = math.ceil(
        ((z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
          z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) /
        ((p2 - p1) ** 2)
    )

    # Calculate days needed for sample size
    visitors_per_variant_per_day = daily_traffic // 2
    statistical_days = math.ceil(required_n / visitors_per_variant_per_day)

    # Weekly cycle requirement
    weekly_days = 7 if include_weekly_cycle else 1

    # Monthly consideration
    monthly_days = 14 if include_monthly_cycle else 0

    # Business-specific adjustments
    business_adjustment = 0
    if business_type == "ecommerce":
        # E-commerce has strong weekly patterns
        business_adjustment = 7  # At least 2 weeks recommended
    elif business_type == "saas":
        # SaaS may have monthly billing cycles
        business_adjustment = 7  # Consider monthly patterns
    elif business_type == "content":
        # Content sites have strong day-of-week patterns
        business_adjustment = 7

    # Calculate recommendations
    minimum_days = max(statistical_days, weekly_days)
    recommended_days = max(
        statistical_days,
        weekly_days,
        monthly_days,
        statistical_days + business_adjustment
    )
    ideal_days = max(recommended_days, 14, statistical_days + 7)  # Buffer for novelty effects

    # Calculate expected samples
    expected_sample = visitors_per_variant_per_day * recommended_days

    # Calculate confidence at different stopping points
    def power_at_n(n):
        if n <= 0:
            return 0.0
        se = math.sqrt(2 * p_pooled * (1 - p_pooled) / n)
        if se <= 0:
            return 1.0
        z_effect = abs(p2 - p1) / se
        return norm.cdf(z_effect - z_alpha) + norm.cdf(-z_effect - z_alpha)

    confidence_at_minimum = power_at_n(visitors_per_variant_per_day * minimum_days) * 100
    confidence_at_recommended = power_at_n(visitors_per_variant_per_day * recommended_days) * 100

    # Risk assessment
    if minimum_days == statistical_days:
        risk = (
            "Low risk if stopped at minimum. Sample size is sufficient for detection."
        )
    elif minimum_days < statistical_days:
        risk = (
            "HIGH RISK if stopped at minimum! Sample size would be insufficient. "
            f"You'd only have {(minimum_days/statistical_days)*100:.0f}% of needed sample."
        )
    else:
        risk = (
            "Moderate risk. Statistical minimum met but weekly patterns may not be captured."
        )

    # Generate recommendation
    recommendation = _generate_recommendation(
        minimum_days=minimum_days,
        recommended_days=recommended_days,
        ideal_days=ideal_days,
        statistical_days=statistical_days,
        weekly_days=weekly_days,
        required_n=required_n,
        daily_traffic=daily_traffic,
        baseline_rate=baseline_rate,
        mde=minimum_detectable_effect,
        business_type=business_type,
    )

    return DurationRecommendation(
        recommended_days=recommended_days,
        minimum_days=minimum_days,
        ideal_days=ideal_days,
        statistical_minimum_days=statistical_days,
        weekly_cycle_days=weekly_days,
        monthly_consideration=include_monthly_cycle,
        required_sample_per_variant=required_n,
        expected_sample_per_variant=expected_sample,
        risk_if_stopped_early=risk,
        confidence_at_minimum=confidence_at_minimum,
        confidence_at_recommended=confidence_at_recommended,
        recommendation=recommendation,
    )


def _generate_recommendation(
    minimum_days: int,
    recommended_days: int,
    ideal_days: int,
    statistical_days: int,
    weekly_days: int,
    required_n: int,
    daily_traffic: int,
    baseline_rate: float,
    mde: float,
    business_type: str,
) -> str:
    """Generate detailed recommendation text."""

    lines = []

    lines.append("## Test Duration Recommendation\n")

    # Main recommendation
    lines.append(f"### Run for **{recommended_days} days** (minimum: {minimum_days}, ideal: {ideal_days})\n")

    # Timeline visualization
    lines.append("```")
    for day in range(1, max(ideal_days, 21) + 1):
        markers = []
        if day == minimum_days:
            markers.append("MINIMUM")
        if day == recommended_days:
            markers.append("RECOMMENDED")
        if day == ideal_days and ideal_days != recommended_days:
            markers.append("IDEAL")
        if day == 7:
            markers.append("1 week")
        if day == 14:
            markers.append("2 weeks")
        if day == 21:
            markers.append("3 weeks")

        if markers:
            marker_str = f" <- {', '.join(markers)}"
        else:
            marker_str = ""

        if day <= minimum_days:
            bar = "█"
        elif day <= recommended_days:
            bar = "▓"
        elif day <= ideal_days:
            bar = "░"
        else:
            bar = " "

        lines.append(f"Day {day:2d} |{bar}|{marker_str}")
    lines.append("```\n")

    # Breakdown
    lines.append("### Why This Duration?\n")
    lines.append(f"1. **Statistical requirement:** {statistical_days} days")
    lines.append(f"   - Need {required_n:,} visitors per variant")
    lines.append(f"   - At {daily_traffic:,}/day = {daily_traffic//2:,} per variant")
    lines.append("")

    if weekly_days > 1:
        lines.append(f"2. **Weekly patterns:** At least 7 days to capture day-of-week effects")
        lines.append("   - Tuesday traffic differs from Saturday")
        lines.append("   - Capture at least one full business cycle")
        lines.append("")

    # Business-specific advice
    lines.append("### Business-Type Considerations\n")
    if business_type == "ecommerce":
        lines.append(
            "**E-commerce:** Strongly recommend 14+ days to capture:\n"
            "- Weekend vs weekday shopping patterns\n"
            "- Payday effects (if applicable)\n"
            "- Promotional calendar overlap\n"
        )
    elif business_type == "saas":
        lines.append(
            "**SaaS:** Consider:\n"
            "- Trial period length (if testing signup flow)\n"
            "- Monthly billing cycles\n"
            "- Enterprise vs SMB behavior differences\n"
        )
    elif business_type == "content":
        lines.append(
            "**Content:** Key considerations:\n"
            "- Strong day-of-week readership patterns\n"
            "- News cycles and trending topics\n"
            "- Return visitor behavior\n"
        )
    else:
        lines.append(
            "Consider your specific business cycles and ensure you capture "
            "representative traffic patterns.\n"
        )

    # Warnings
    lines.append("### When to Stop\n")
    lines.append(
        f"- **Don't stop before day {minimum_days}** - results won't be statistically valid\n"
        f"- **Safe to analyze at day {recommended_days}** - full statistical power\n"
        f"- **Consider running to day {ideal_days}** for extra confidence and novelty detection\n"
    )

    return "\n".join(lines)


def summarize(result: DurationRecommendation) -> str:
    """Generate markdown summary."""
    return result.recommendation


__all__ = [
    "DurationRecommendation",
    "recommend_duration",
    "summarize",
]
