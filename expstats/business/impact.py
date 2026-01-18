"""
Revenue and Business Impact Projections.

Translates A/B test results into business value that stakeholders understand:
- Monthly/annual revenue projections
- Confidence intervals for business metrics
- Break-even analysis
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Literal
from scipy.stats import norm


@dataclass
class ImpactProjection:
    """Projected business impact from an A/B test."""

    # Revenue impact
    monthly_revenue_lift: float
    annual_revenue_lift: float
    revenue_lift_range: Tuple[float, float]  # Confidence interval

    # Conversion impact
    monthly_additional_conversions: float
    annual_additional_conversions: float

    # Per-visitor value
    value_per_visitor_control: float
    value_per_visitor_variant: float
    incremental_value_per_visitor: float

    # Risk assessment
    probability_positive_impact: float
    probability_negative_impact: float
    expected_value: float  # Expected value considering uncertainty

    # Inputs (for reference)
    lift_percent: float
    lift_ci_lower: float
    lift_ci_upper: float
    monthly_visitors: int
    revenue_per_conversion: float

    # Summary
    recommendation: str


def project_impact(
    control_rate: float,
    variant_rate: float,
    lift_percent: float,
    lift_ci_lower: float,
    lift_ci_upper: float,
    monthly_visitors: int,
    revenue_per_conversion: float,
    confidence: int = 95,
    cost_of_change: float = 0,
) -> ImpactProjection:
    """
    Project the business impact of implementing an A/B test winner.

    Args:
        control_rate: Control conversion rate (e.g., 0.05 for 5%)
        variant_rate: Variant conversion rate
        lift_percent: Observed lift percentage (e.g., 10 for 10% lift)
        lift_ci_lower: Lower bound of lift CI (percentage)
        lift_ci_upper: Upper bound of lift CI (percentage)
        monthly_visitors: Expected monthly visitors to the experience
        revenue_per_conversion: Average revenue per conversion
        confidence: Confidence level used (default 95)
        cost_of_change: One-time cost to implement the change

    Returns:
        ImpactProjection with revenue and conversion projections

    Example:
        >>> projection = project_impact(
        ...     control_rate=0.05,
        ...     variant_rate=0.055,
        ...     lift_percent=10.0,
        ...     lift_ci_lower=2.0,
        ...     lift_ci_upper=18.0,
        ...     monthly_visitors=100000,
        ...     revenue_per_conversion=50.0,
        ... )
        >>> print(f"Annual revenue lift: ${projection.annual_revenue_lift:,.0f}")
    """
    # Handle percentage inputs
    if control_rate > 1:
        control_rate = control_rate / 100
    if variant_rate > 1:
        variant_rate = variant_rate / 100

    # Calculate per-visitor values
    value_per_visitor_control = control_rate * revenue_per_conversion
    value_per_visitor_variant = variant_rate * revenue_per_conversion
    incremental_value = value_per_visitor_variant - value_per_visitor_control

    # Monthly projections
    monthly_control_conversions = monthly_visitors * control_rate
    monthly_variant_conversions = monthly_visitors * variant_rate
    monthly_additional_conversions = monthly_variant_conversions - monthly_control_conversions

    # Revenue projections
    monthly_control_revenue = monthly_control_conversions * revenue_per_conversion
    monthly_variant_revenue = monthly_variant_conversions * revenue_per_conversion
    monthly_revenue_lift = monthly_variant_revenue - monthly_control_revenue

    # Annual projections
    annual_revenue_lift = monthly_revenue_lift * 12
    annual_additional_conversions = monthly_additional_conversions * 12

    # Revenue range based on CI
    lift_lower_multiplier = 1 + (lift_ci_lower / 100)
    lift_upper_multiplier = 1 + (lift_ci_upper / 100)

    revenue_at_lower = (
        monthly_visitors * control_rate * lift_lower_multiplier * revenue_per_conversion
    ) - monthly_control_revenue
    revenue_at_upper = (
        monthly_visitors * control_rate * lift_upper_multiplier * revenue_per_conversion
    ) - monthly_control_revenue

    revenue_lift_range = (
        min(revenue_at_lower, revenue_at_upper) * 12,
        max(revenue_at_lower, revenue_at_upper) * 12,
    )

    # Probability calculations (assuming normal distribution of lift)
    # Estimate standard error from CI
    z_alpha = norm.ppf(1 - (1 - confidence / 100) / 2)
    ci_width = lift_ci_upper - lift_ci_lower
    se = ci_width / (2 * z_alpha) if z_alpha > 0 else ci_width / 4

    if se > 0:
        # Probability that true effect is positive
        z_positive = lift_percent / se
        probability_positive = norm.cdf(z_positive)
        probability_negative = 1 - probability_positive
    else:
        probability_positive = 1.0 if lift_percent > 0 else 0.0
        probability_negative = 1 - probability_positive

    # Expected value (considering uncertainty)
    # Simple model: weighted average of outcomes
    expected_value = annual_revenue_lift * probability_positive

    # Generate recommendation
    recommendation = _generate_recommendation(
        lift_percent=lift_percent,
        lift_ci_lower=lift_ci_lower,
        lift_ci_upper=lift_ci_upper,
        monthly_revenue_lift=monthly_revenue_lift,
        annual_revenue_lift=annual_revenue_lift,
        revenue_lift_range=revenue_lift_range,
        probability_positive=probability_positive,
        cost_of_change=cost_of_change,
        expected_value=expected_value,
    )

    return ImpactProjection(
        monthly_revenue_lift=monthly_revenue_lift,
        annual_revenue_lift=annual_revenue_lift,
        revenue_lift_range=revenue_lift_range,
        monthly_additional_conversions=monthly_additional_conversions,
        annual_additional_conversions=annual_additional_conversions,
        value_per_visitor_control=value_per_visitor_control,
        value_per_visitor_variant=value_per_visitor_variant,
        incremental_value_per_visitor=incremental_value,
        probability_positive_impact=probability_positive,
        probability_negative_impact=probability_negative,
        expected_value=expected_value,
        lift_percent=lift_percent,
        lift_ci_lower=lift_ci_lower,
        lift_ci_upper=lift_ci_upper,
        monthly_visitors=monthly_visitors,
        revenue_per_conversion=revenue_per_conversion,
        recommendation=recommendation,
    )


def _generate_recommendation(
    lift_percent: float,
    lift_ci_lower: float,
    lift_ci_upper: float,
    monthly_revenue_lift: float,
    annual_revenue_lift: float,
    revenue_lift_range: Tuple[float, float],
    probability_positive: float,
    cost_of_change: float,
    expected_value: float,
) -> str:
    """Generate business recommendation based on impact analysis."""
    lines = []

    lines.append("## Business Impact Analysis\n")

    # Revenue summary
    lines.append("### Revenue Impact\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Monthly Revenue Lift | ${monthly_revenue_lift:,.0f} |")
    lines.append(f"| Annual Revenue Lift | ${annual_revenue_lift:,.0f} |")
    lines.append(f"| Range (95% CI) | ${revenue_lift_range[0]:,.0f} to ${revenue_lift_range[1]:,.0f} |")
    lines.append("")

    # Probability assessment
    lines.append("### Confidence Assessment\n")
    lines.append(f"- **Probability of positive impact:** {probability_positive:.1%}")
    lines.append(f"- **Probability of negative impact:** {1 - probability_positive:.1%}")
    lines.append(f"- **Expected annual value:** ${expected_value:,.0f}")
    lines.append("")

    # Break-even analysis
    if cost_of_change > 0:
        if monthly_revenue_lift > 0:
            months_to_break_even = cost_of_change / monthly_revenue_lift
            lines.append("### Break-Even Analysis\n")
            lines.append(f"- Implementation cost: ${cost_of_change:,.0f}")
            lines.append(f"- Break-even period: {months_to_break_even:.1f} months")
            if months_to_break_even < 3:
                lines.append("- **Quick payback** - ROI realized within a quarter")
            elif months_to_break_even < 12:
                lines.append("- **Reasonable payback** - ROI realized within a year")
            else:
                lines.append("- **Long payback** - Consider if investment is worthwhile")
            lines.append("")

    # Recommendation
    lines.append("### Recommendation\n")

    if probability_positive > 0.95 and lift_ci_lower > 0:
        lines.append(
            f"**STRONG IMPLEMENT** - High confidence ({probability_positive:.0%}) that this change "
            f"will generate ${annual_revenue_lift:,.0f}/year in additional revenue."
        )
    elif probability_positive > 0.80:
        lines.append(
            f"**IMPLEMENT** - Good confidence ({probability_positive:.0%}) of positive impact. "
            f"Expected value is ${expected_value:,.0f}/year."
        )
    elif probability_positive > 0.50:
        lines.append(
            f"**CONSIDER** - Moderate confidence ({probability_positive:.0%}). The result leans "
            f"positive but isn't conclusive. Consider running longer or validating with a follow-up test."
        )
    else:
        lines.append(
            f"**DO NOT IMPLEMENT** - Low probability ({probability_positive:.0%}) of positive impact. "
            f"The change may actually hurt revenue."
        )

    return "\n".join(lines)


def summarize(result: ImpactProjection) -> str:
    """Generate markdown summary of impact projection."""
    return result.recommendation


__all__ = [
    "ImpactProjection",
    "project_impact",
    "summarize",
]
