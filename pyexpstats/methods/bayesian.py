"""
Bayesian A/B Testing Module.

This module provides Bayesian analysis for A/B tests, which gives more
intuitive results than frequentist methods:
- "94% probability that B is better than A" instead of "p < 0.05"
- No fixed sample size requirement
- Can peek at results anytime without penalty
- Expected loss calculations to quantify risk

Uses Beta-Binomial model for conversion rates.

References:
- VWO's Bayesian SmartStats
- Evan Miller's Bayesian A/B Testing
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional, Tuple, List
import numpy as np
from scipy import stats as scipy_stats


@dataclass
class BayesianTestResult:
    """Results from Bayesian A/B test analysis."""

    # Input data
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    control_rate: float
    variant_rate: float

    # Bayesian metrics
    probability_variant_better: float  # P(variant > control)
    probability_control_better: float  # P(control > variant)
    probability_variant_best: float    # Same as above for 2-variant case

    # Expected loss (risk quantification)
    expected_loss_choosing_variant: float  # If you pick variant but control is better
    expected_loss_choosing_control: float  # If you pick control but variant is better

    # Credible intervals (Bayesian equivalent of confidence intervals)
    control_credible_interval: Tuple[float, float]
    variant_credible_interval: Tuple[float, float]
    lift_credible_interval: Tuple[float, float]

    # Point estimates
    lift_percent: float
    lift_absolute: float

    # Decision
    has_winner: bool
    winner: Literal["control", "variant", "none"]
    confidence_threshold: float  # Threshold used for decision

    # Recommendation
    recommendation: str


@dataclass
class BayesianMultiVariantResult:
    """Results from Bayesian multi-variant analysis."""
    variants: List[dict]
    probabilities_best: dict  # {variant_name: probability}
    expected_losses: dict     # {variant_name: expected_loss}
    best_variant: str
    recommendation: str


def _beta_posterior(successes: int, trials: int, prior_alpha: float = 1, prior_beta: float = 1):
    """
    Calculate Beta posterior distribution parameters.

    Uses conjugate Beta-Binomial model:
    Prior: Beta(alpha, beta)
    Likelihood: Binomial(n, p)
    Posterior: Beta(alpha + successes, beta + failures)

    Default prior is Beta(1,1) = Uniform distribution (non-informative)
    """
    posterior_alpha = prior_alpha + successes
    posterior_beta = prior_beta + (trials - successes)
    return posterior_alpha, posterior_beta


def _probability_b_beats_a(
    alpha_a: float, beta_a: float,
    alpha_b: float, beta_b: float,
    num_samples: int = 100000
) -> float:
    """
    Calculate P(B > A) using Monte Carlo simulation.

    More accurate than closed-form approximations for the Beta distribution.
    """
    # Sample from both posteriors
    samples_a = np.random.beta(alpha_a, beta_a, num_samples)
    samples_b = np.random.beta(alpha_b, beta_b, num_samples)

    # Count how often B > A
    return float(np.mean(samples_b > samples_a))


def _expected_loss(
    alpha_a: float, beta_a: float,
    alpha_b: float, beta_b: float,
    num_samples: int = 100000
) -> Tuple[float, float]:
    """
    Calculate expected loss for choosing each variant.

    Expected loss of choosing A = E[max(0, B - A)]
    This is the expected conversion rate you lose if A is actually worse.
    """
    samples_a = np.random.beta(alpha_a, beta_a, num_samples)
    samples_b = np.random.beta(alpha_b, beta_b, num_samples)

    # Loss if we choose A but B is better
    loss_choosing_a = float(np.mean(np.maximum(0, samples_b - samples_a)))

    # Loss if we choose B but A is better
    loss_choosing_b = float(np.mean(np.maximum(0, samples_a - samples_b)))

    return loss_choosing_a, loss_choosing_b


def _credible_interval(alpha: float, beta: float, credibility: float = 0.95) -> Tuple[float, float]:
    """Calculate credible interval for Beta distribution."""
    lower = (1 - credibility) / 2
    upper = 1 - lower
    return (
        scipy_stats.beta.ppf(lower, alpha, beta),
        scipy_stats.beta.ppf(upper, alpha, beta)
    )


def _lift_credible_interval(
    alpha_a: float, beta_a: float,
    alpha_b: float, beta_b: float,
    credibility: float = 0.95,
    num_samples: int = 100000
) -> Tuple[float, float]:
    """Calculate credible interval for lift (B - A) / A."""
    samples_a = np.random.beta(alpha_a, beta_a, num_samples)
    samples_b = np.random.beta(alpha_b, beta_b, num_samples)

    # Calculate relative lift for each sample
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        lift_samples = np.where(
            samples_a > 0,
            (samples_b - samples_a) / samples_a * 100,
            0
        )

    lower = (1 - credibility) / 2
    upper = 1 - lower

    return (
        float(np.percentile(lift_samples, lower * 100)),
        float(np.percentile(lift_samples, upper * 100))
    )


def analyze(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    prior_alpha: float = 1,
    prior_beta: float = 1,
    confidence_threshold: float = 0.95,
    credibility: float = 0.95,
) -> BayesianTestResult:
    """
    Analyze an A/B test using Bayesian methods.

    This gives you intuitive probability statements like
    "94% probability the variant is better" instead of p-values.

    Args:
        control_visitors: Number of visitors in control group
        control_conversions: Number of conversions in control group
        variant_visitors: Number of visitors in variant group
        variant_conversions: Number of conversions in variant group
        prior_alpha: Alpha parameter for Beta prior (default 1 for uniform)
        prior_beta: Beta parameter for Beta prior (default 1 for uniform)
        confidence_threshold: Probability threshold to declare a winner (default 0.95)
        credibility: Credibility level for intervals (default 0.95)

    Returns:
        BayesianTestResult with probabilities and recommendations

    Example:
        >>> result = bayesian.analyze(
        ...     control_visitors=10000,
        ...     control_conversions=500,
        ...     variant_visitors=10000,
        ...     variant_conversions=550,
        ... )
        >>> print(f"{result.probability_variant_better:.1%} chance variant is better")
        94.2% chance variant is better
    """
    # Validate inputs
    if control_visitors <= 0 or variant_visitors <= 0:
        raise ValueError("Visitors must be positive")
    if control_conversions > control_visitors:
        raise ValueError("Control conversions cannot exceed control visitors")
    if variant_conversions > variant_visitors:
        raise ValueError("Variant conversions cannot exceed variant visitors")

    # Calculate observed rates
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors

    # Calculate posteriors
    alpha_c, beta_c = _beta_posterior(control_conversions, control_visitors, prior_alpha, prior_beta)
    alpha_v, beta_v = _beta_posterior(variant_conversions, variant_visitors, prior_alpha, prior_beta)

    # Calculate probability variant is better
    prob_variant_better = _probability_b_beats_a(alpha_c, beta_c, alpha_v, beta_v)
    prob_control_better = 1 - prob_variant_better

    # Calculate expected losses
    loss_control, loss_variant = _expected_loss(alpha_c, beta_c, alpha_v, beta_v)

    # Calculate credible intervals
    ci_control = _credible_interval(alpha_c, beta_c, credibility)
    ci_variant = _credible_interval(alpha_v, beta_v, credibility)
    ci_lift = _lift_credible_interval(alpha_c, beta_c, alpha_v, beta_v, credibility)

    # Calculate lift
    lift_absolute = variant_rate - control_rate
    lift_percent = (lift_absolute / control_rate * 100) if control_rate > 0 else 0

    # Determine winner
    has_winner = False
    winner = "none"

    if prob_variant_better >= confidence_threshold:
        has_winner = True
        winner = "variant"
    elif prob_control_better >= confidence_threshold:
        has_winner = True
        winner = "control"

    # Generate recommendation
    recommendation = _generate_recommendation(
        prob_variant_better=prob_variant_better,
        prob_control_better=prob_control_better,
        loss_variant=loss_variant,
        loss_control=loss_control,
        control_rate=control_rate,
        variant_rate=variant_rate,
        lift_percent=lift_percent,
        ci_lift=ci_lift,
        has_winner=has_winner,
        winner=winner,
        confidence_threshold=confidence_threshold,
    )

    return BayesianTestResult(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        control_rate=control_rate,
        variant_rate=variant_rate,
        probability_variant_better=prob_variant_better * 100,
        probability_control_better=prob_control_better * 100,
        probability_variant_best=prob_variant_better * 100,
        expected_loss_choosing_variant=loss_variant * 100,  # As percentage points
        expected_loss_choosing_control=loss_control * 100,
        control_credible_interval=ci_control,
        variant_credible_interval=ci_variant,
        lift_credible_interval=ci_lift,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        has_winner=has_winner,
        winner=winner,
        confidence_threshold=confidence_threshold * 100,
        recommendation=recommendation,
    )


def _generate_recommendation(
    prob_variant_better: float,
    prob_control_better: float,
    loss_variant: float,
    loss_control: float,
    control_rate: float,
    variant_rate: float,
    lift_percent: float,
    ci_lift: Tuple[float, float],
    has_winner: bool,
    winner: str,
    confidence_threshold: float,
) -> str:
    """Generate human-readable recommendation."""

    if has_winner and winner == "variant":
        return (
            f"## Variant Wins!\n\n"
            f"**{prob_variant_better*100:.1f}%** probability that the variant is better than control.\n\n"
            f"### Results\n"
            f"- Control: {control_rate:.2%} conversion rate\n"
            f"- Variant: {variant_rate:.2%} conversion rate\n"
            f"- Lift: {lift_percent:+.1f}% ({ci_lift[0]:+.1f}% to {ci_lift[1]:+.1f}%)\n\n"
            f"### Risk Analysis\n"
            f"- If you implement the variant and you're wrong, expected loss: {loss_variant*100:.3f}%\n"
            f"- If you keep control and you're wrong, expected loss: {loss_control*100:.3f}%\n\n"
            f"**Recommendation:** Implement the variant. The probability of improvement is "
            f"above your {confidence_threshold*100:.0f}% threshold."
        )
    elif has_winner and winner == "control":
        return (
            f"## Control Wins!\n\n"
            f"**{prob_control_better*100:.1f}%** probability that control is better than the variant.\n\n"
            f"### Results\n"
            f"- Control: {control_rate:.2%} conversion rate\n"
            f"- Variant: {variant_rate:.2%} conversion rate\n"
            f"- Lift: {lift_percent:+.1f}%\n\n"
            f"### Risk Analysis\n"
            f"- If you implement the variant, expected loss: {loss_variant*100:.3f}%\n"
            f"- If you keep control, expected loss: {loss_control*100:.3f}%\n\n"
            f"**Recommendation:** Keep the control. The variant performs worse."
        )
    else:
        leading = "Variant" if prob_variant_better > 0.5 else "Control"
        leading_prob = max(prob_variant_better, prob_control_better) * 100

        return (
            f"## No Clear Winner Yet\n\n"
            f"**{leading}** is currently leading with {leading_prob:.1f}% probability of being better, "
            f"but this is below your {confidence_threshold*100:.0f}% threshold.\n\n"
            f"### Current Results\n"
            f"- Control: {control_rate:.2%} conversion rate\n"
            f"- Variant: {variant_rate:.2%} conversion rate\n"
            f"- Observed lift: {lift_percent:+.1f}%\n"
            f"- Lift range: {ci_lift[0]:+.1f}% to {ci_lift[1]:+.1f}%\n\n"
            f"### Risk Analysis\n"
            f"- Expected loss if choosing variant: {loss_variant*100:.3f}%\n"
            f"- Expected loss if choosing control: {loss_control*100:.3f}%\n\n"
            f"**Recommendation:** Continue running the test to gather more data, "
            f"or lower your confidence threshold if you're comfortable with more risk."
        )


def analyze_multi(
    variants: List[dict],
    prior_alpha: float = 1,
    prior_beta: float = 1,
    num_samples: int = 100000,
) -> BayesianMultiVariantResult:
    """
    Analyze multiple variants using Bayesian methods.

    Args:
        variants: List of dicts with 'name', 'visitors', 'conversions'
        prior_alpha: Alpha parameter for Beta prior
        prior_beta: Beta parameter for Beta prior
        num_samples: Number of Monte Carlo samples

    Returns:
        BayesianMultiVariantResult with probabilities for each variant

    Example:
        >>> result = bayesian.analyze_multi([
        ...     {"name": "control", "visitors": 10000, "conversions": 500},
        ...     {"name": "variant_a", "visitors": 10000, "conversions": 550},
        ...     {"name": "variant_b", "visitors": 10000, "conversions": 480},
        ... ])
        >>> print(result.probabilities_best)
        {'control': 12.3, 'variant_a': 85.2, 'variant_b': 2.5}
    """
    if len(variants) < 2:
        raise ValueError("At least 2 variants required")

    # Calculate posteriors
    posteriors = {}
    for v in variants:
        alpha, beta = _beta_posterior(
            v["conversions"], v["visitors"],
            prior_alpha, prior_beta
        )
        posteriors[v["name"]] = (alpha, beta)

    # Sample from all posteriors
    samples = {}
    for name, (alpha, beta) in posteriors.items():
        samples[name] = np.random.beta(alpha, beta, num_samples)

    # Stack samples for comparison
    sample_matrix = np.vstack([samples[v["name"]] for v in variants])
    names = [v["name"] for v in variants]

    # Find which variant is best in each sample
    best_indices = np.argmax(sample_matrix, axis=0)

    # Calculate probability each variant is best
    probabilities_best = {}
    for i, name in enumerate(names):
        probabilities_best[name] = float(np.mean(best_indices == i)) * 100

    # Calculate expected losses
    expected_losses = {}
    for i, name in enumerate(names):
        # Loss = E[max(0, best_other - this)]
        other_max = np.max(np.delete(sample_matrix, i, axis=0), axis=0)
        loss = float(np.mean(np.maximum(0, other_max - sample_matrix[i])))
        expected_losses[name] = loss * 100

    # Find best variant
    best_variant = max(probabilities_best, key=probabilities_best.get)

    # Build variant info
    variant_info = []
    for v in variants:
        rate = v["conversions"] / v["visitors"]
        variant_info.append({
            "name": v["name"],
            "visitors": v["visitors"],
            "conversions": v["conversions"],
            "rate": rate,
            "probability_best": probabilities_best[v["name"]],
            "expected_loss": expected_losses[v["name"]],
        })

    # Generate recommendation
    sorted_variants = sorted(variant_info, key=lambda x: x["probability_best"], reverse=True)
    top = sorted_variants[0]

    if top["probability_best"] >= 95:
        recommendation = (
            f"**{top['name']}** is the clear winner with {top['probability_best']:.1f}% "
            f"probability of being best. Implement it."
        )
    elif top["probability_best"] >= 80:
        recommendation = (
            f"**{top['name']}** is likely the best with {top['probability_best']:.1f}% probability. "
            f"Consider implementing, or run longer for more confidence."
        )
    else:
        recommendation = (
            f"No clear winner yet. **{top['name']}** leads with only {top['probability_best']:.1f}% "
            f"probability. Continue running the test."
        )

    return BayesianMultiVariantResult(
        variants=variant_info,
        probabilities_best=probabilities_best,
        expected_losses=expected_losses,
        best_variant=best_variant,
        recommendation=recommendation,
    )


def summarize(result: BayesianTestResult, test_name: str = "Bayesian A/B Test") -> str:
    """
    Generate a markdown summary of Bayesian test results.

    Args:
        result: BayesianTestResult from analyze()
        test_name: Name of the test for the report

    Returns:
        Markdown-formatted summary string
    """
    lines = [f"## {test_name}\n"]

    # Winner status
    if result.has_winner:
        if result.winner == "variant":
            lines.append(f"### **Winner: Variant** ({result.probability_variant_better:.1f}% confidence)\n")
        else:
            lines.append(f"### **Winner: Control** ({result.probability_control_better:.1f}% confidence)\n")
    else:
        lines.append("### **No Winner Yet**\n")

    # Probability visualization
    v_pct = int(result.probability_variant_better / 5)
    c_pct = int(result.probability_control_better / 5)
    lines.append(f"**Probability Variant Wins:** {'█' * v_pct}{'░' * (20-v_pct)} {result.probability_variant_better:.1f}%")
    lines.append(f"**Probability Control Wins:** {'█' * c_pct}{'░' * (20-c_pct)} {result.probability_control_better:.1f}%\n")

    # Results table
    lines.append("### Results\n")
    lines.append("| Metric | Control | Variant |")
    lines.append("|--------|---------|---------|")
    lines.append(f"| Visitors | {result.control_visitors:,} | {result.variant_visitors:,} |")
    lines.append(f"| Conversions | {result.control_conversions:,} | {result.variant_conversions:,} |")
    lines.append(f"| Rate | {result.control_rate:.2%} | {result.variant_rate:.2%} |")
    lines.append(f"| 95% CI | [{result.control_credible_interval[0]:.2%}, {result.control_credible_interval[1]:.2%}] | [{result.variant_credible_interval[0]:.2%}, {result.variant_credible_interval[1]:.2%}] |")
    lines.append("")

    # Lift
    lines.append("### Lift Analysis\n")
    lines.append(f"- **Observed lift:** {result.lift_percent:+.1f}%")
    lines.append(f"- **95% credible interval:** {result.lift_credible_interval[0]:+.1f}% to {result.lift_credible_interval[1]:+.1f}%")
    lines.append("")

    # Risk analysis
    lines.append("### Risk Analysis\n")
    lines.append(f"- Expected loss if choosing variant: {result.expected_loss_choosing_variant:.3f} percentage points")
    lines.append(f"- Expected loss if choosing control: {result.expected_loss_choosing_control:.3f} percentage points")
    lines.append("")

    # Interpretation
    lines.append("### Interpretation\n")
    if result.has_winner:
        lines.append(f"With **{max(result.probability_variant_better, result.probability_control_better):.1f}%** confidence, ")
        lines.append(f"the **{result.winner}** performs better. This exceeds the {result.confidence_threshold:.0f}% threshold.")
    else:
        lines.append(f"Neither variant has reached the {result.confidence_threshold:.0f}% confidence threshold. ")
        lines.append("Continue running the test for more conclusive results.")

    return "\n".join(lines)


__all__ = [
    "BayesianTestResult",
    "BayesianMultiVariantResult",
    "analyze",
    "analyze_multi",
    "summarize",
]
