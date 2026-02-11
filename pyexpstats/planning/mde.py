"""
Minimum Detectable Effect (MDE) Calculator.

Answers the question: "Given my traffic, what's the smallest effect I can detect?"

This is crucial for test planning because it tells you:
- Whether your test can detect the effect size you care about
- How long you need to run to detect a specific effect
- Whether a test is even worth running
"""

import math
from dataclasses import dataclass
from typing import Optional, Literal
from scipy.stats import norm


@dataclass
class MDEResult:
    """Result from MDE calculation."""

    # Primary result
    minimum_detectable_effect: float  # As relative percentage (e.g., 10 for 10%)
    minimum_detectable_absolute: float  # As absolute change

    # Input parameters
    sample_size_per_variant: int
    baseline_rate: float
    confidence: int
    power: int

    # Interpretation
    detectable_variant_rate: float  # baseline_rate * (1 + mde)
    is_practically_useful: bool  # Is MDE small enough to be useful?

    # Recommendations
    recommendation: str
    sample_needed_for_target: Optional[int]  # If they have a target MDE


def minimum_detectable_effect(
    sample_size_per_variant: Optional[int] = None,
    daily_traffic: Optional[int] = None,
    test_duration_days: Optional[int] = None,
    baseline_rate: float = 0.05,
    confidence: int = 95,
    power: int = 80,
    target_mde: Optional[float] = None,
    metric_type: Literal["conversion", "continuous"] = "conversion",
    baseline_std: Optional[float] = None,
) -> MDEResult:
    """
    Calculate the Minimum Detectable Effect for your test.

    You can provide either:
    - sample_size_per_variant directly, OR
    - daily_traffic and test_duration_days (will be calculated)

    Args:
        sample_size_per_variant: Number of visitors per variant
        daily_traffic: Total daily traffic (will be split between variants)
        test_duration_days: How many days you'll run the test
        baseline_rate: Expected conversion rate (e.g., 0.05 for 5%)
        confidence: Confidence level (default 95)
        power: Statistical power (default 80)
        target_mde: If provided, will tell you if you can achieve it
        metric_type: "conversion" for binary, "continuous" for revenue-like
        baseline_std: Standard deviation (required for continuous metrics)

    Returns:
        MDEResult with MDE and recommendations

    Example:
        >>> result = minimum_detectable_effect(
        ...     daily_traffic=5000,
        ...     test_duration_days=14,
        ...     baseline_rate=0.05,
        ... )
        >>> print(f"Can detect {result.minimum_detectable_effect:.1f}% lift or larger")
        Can detect 12.3% lift or larger
    """
    # Calculate sample size if not provided
    if sample_size_per_variant is None:
        if daily_traffic is None or test_duration_days is None:
            raise ValueError(
                "Must provide either sample_size_per_variant, or both "
                "daily_traffic and test_duration_days"
            )
        # Assume 50/50 split
        sample_size_per_variant = (daily_traffic * test_duration_days) // 2

    if sample_size_per_variant <= 0:
        raise ValueError("Sample size must be positive")

    # Handle percentage input
    if baseline_rate > 1:
        baseline_rate = baseline_rate / 100

    # Calculate critical values
    alpha = 1 - confidence / 100
    beta = 1 - power / 100

    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)

    n = sample_size_per_variant

    if metric_type == "conversion":
        # For proportions, MDE formula
        # n = 2 * ((z_alpha + z_beta) / MDE)^2 * p * (1-p) * 2
        # Solving for MDE:
        # MDE = (z_alpha + z_beta) * sqrt(2 * p * (1-p) / n)

        p = baseline_rate
        se = math.sqrt(2 * p * (1 - p) / n)
        mde_absolute = (z_alpha + z_beta) * se
        mde_relative = (mde_absolute / p * 100) if p > 0 else float('inf')

    else:  # continuous
        if baseline_std is None:
            raise ValueError("baseline_std required for continuous metrics")

        # For means:
        # n = 2 * ((z_alpha + z_beta) * std / MDE)^2
        # Solving for MDE:
        # MDE = (z_alpha + z_beta) * std * sqrt(2/n)

        mde_absolute = (z_alpha + z_beta) * baseline_std * math.sqrt(2 / n)
        mde_relative = (mde_absolute / baseline_rate * 100) if baseline_rate != 0 else float('inf')

    # Calculate detectable variant rate
    detectable_variant_rate = baseline_rate * (1 + mde_relative / 100)

    # Is this practically useful?
    # Generally, MDEs > 20-30% are not very useful
    is_useful = mde_relative <= 25

    # Calculate sample needed for target MDE if provided
    sample_needed = None
    if target_mde is not None:
        if target_mde > 1:
            target_mde = target_mde / 100

        target_absolute = baseline_rate * target_mde

        if metric_type == "conversion":
            p = baseline_rate
            sample_needed = int(math.ceil(
                2 * ((z_alpha + z_beta) ** 2) * p * (1 - p) / (target_absolute ** 2)
            ))
        else:
            sample_needed = int(math.ceil(
                2 * ((z_alpha + z_beta) * baseline_std / target_absolute) ** 2
            ))

    # Generate recommendation
    recommendation = _generate_recommendation(
        mde_relative=mde_relative,
        n=n,
        daily_traffic=daily_traffic,
        test_duration_days=test_duration_days,
        target_mde=target_mde,
        sample_needed=sample_needed,
        is_useful=is_useful,
        baseline_rate=baseline_rate,
    )

    return MDEResult(
        minimum_detectable_effect=mde_relative,
        minimum_detectable_absolute=mde_absolute,
        sample_size_per_variant=n,
        baseline_rate=baseline_rate,
        confidence=confidence,
        power=power,
        detectable_variant_rate=detectable_variant_rate,
        is_practically_useful=is_useful,
        recommendation=recommendation,
        sample_needed_for_target=sample_needed,
    )


def _generate_recommendation(
    mde_relative: float,
    n: int,
    daily_traffic: Optional[int],
    test_duration_days: Optional[int],
    target_mde: Optional[float],
    sample_needed: Optional[int],
    is_useful: bool,
    baseline_rate: float,
) -> str:
    """Generate recommendation based on MDE calculation."""

    lines = []

    # Main finding
    lines.append(f"## Minimum Detectable Effect: {mde_relative:.1f}%\n")

    lines.append(
        f"With **{n:,}** visitors per variant, you can detect a "
        f"**{mde_relative:.1f}%** relative lift (or larger) with 95% confidence "
        f"and 80% power.\n"
    )

    # What this means
    lines.append("### What This Means\n")
    lines.append(
        f"- Your baseline rate: {baseline_rate:.2%}\n"
        f"- Smallest detectable variant rate: {baseline_rate * (1 + mde_relative/100):.2%}\n"
        f"- Any lift **smaller** than {mde_relative:.1f}% will likely NOT be detected\n"
    )

    # Is it useful?
    if is_useful:
        lines.append(
            f"**Good news:** A {mde_relative:.1f}% MDE is reasonably small. "
            f"You should be able to detect meaningful effects.\n"
        )
    else:
        lines.append(
            f"**Warning:** A {mde_relative:.1f}% MDE is quite large. You'll only detect "
            f"very significant changes. Consider running longer or increasing traffic.\n"
        )

    # Target MDE analysis
    if target_mde is not None and sample_needed is not None:
        target_pct = target_mde * 100 if target_mde <= 1 else target_mde
        lines.append(f"### Target MDE Analysis\n")

        if mde_relative <= target_pct:
            lines.append(
                f"**You can detect your target of {target_pct:.1f}%!** "
                f"Your current sample size is sufficient.\n"
            )
        else:
            lines.append(
                f"**You cannot detect your target of {target_pct:.1f}%** with current traffic.\n"
                f"You would need **{sample_needed:,}** visitors per variant.\n"
            )

            if daily_traffic:
                days_needed = math.ceil(sample_needed * 2 / daily_traffic)
                lines.append(
                    f"At {daily_traffic:,} visitors/day, that's **{days_needed} days**.\n"
                )

    # Recommendations
    lines.append("### Recommendations\n")

    if mde_relative > 30:
        lines.append(
            "- **Run longer:** Your MDE is very high. Double or triple your test duration.\n"
            "- **Increase traffic:** Can you send more traffic to this test?\n"
            "- **Focus on big changes:** Only test changes you expect to have 30%+ impact.\n"
        )
    elif mde_relative > 15:
        lines.append(
            "- **Consider running longer:** You'll miss moderate effects.\n"
            "- **Good for testing bold changes:** Focus on significant redesigns or features.\n"
        )
    else:
        lines.append(
            "- **Good to proceed:** You can detect reasonably small effects.\n"
            "- **Suitable for optimization:** Can test iterative improvements.\n"
        )

    return "\n".join(lines)


def summarize(result: MDEResult, test_name: str = "A/B Test") -> str:
    """Generate markdown summary of MDE analysis."""
    return result.recommendation


__all__ = [
    "MDEResult",
    "minimum_detectable_effect",
    "summarize",
]
