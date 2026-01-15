import math
from scipy.stats import norm, chi2_contingency
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass, field

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
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self

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

@dataclass  
class ConfidenceInterval:
    rate: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float

@dataclass
class Variant:
    name: str
    visitors: int
    conversions: int
    
    @property
    def rate(self) -> float:
        return self.conversions / self.visitors if self.visitors > 0 else 0

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


def sample_size(
    current_rate: float,
    lift_percent: float = 10,
    confidence: int = 95,
    power: int = 80,
    num_variants: int = 2,
) -> SampleSizePlan:
    if current_rate > 1:
        current_rate = current_rate / 100
    
    lift_decimal = lift_percent / 100
    expected_rate = current_rate * (1 + lift_decimal)
    
    if expected_rate > 1:
        raise ValueError(f"Expected rate ({expected_rate:.1%}) exceeds 100%. Lower your lift_percent.")
    if expected_rate < 0:
        raise ValueError(f"Expected rate cannot be negative. Check your lift_percent.")
    if current_rate <= 0 or current_rate >= 1:
        raise ValueError(f"current_rate must be between 0 and 1 (or 0% and 100%)")
    if num_variants < 2:
        raise ValueError("num_variants must be at least 2")
    
    alpha = 1 - (confidence / 100)
    if num_variants > 2:
        alpha = alpha / (num_variants - 1)
    
    beta = 1 - (power / 100)
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)
    
    p1 = current_rate
    p2 = expected_rate
    p_pooled = (p1 + p2) / 2
    
    numerator = (
        z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
        z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2
    
    n = math.ceil(numerator / denominator)
    
    return SampleSizePlan(
        visitors_per_variant=n,
        total_visitors=n * num_variants,
        current_rate=current_rate,
        expected_rate=expected_rate,
        lift_percent=lift_percent,
        confidence=confidence,
        power=power,
    )


def _generate_recommendation(result: 'TestResults') -> str:
    direction = "higher" if result.variant_rate > result.control_rate else "lower"
    
    if result.is_significant:
        return (
            f"**Test variant is significantly {direction} than control** (p-value: {result.p_value:.4f}).\n\n"
            f"_What this means:_ With {result.confidence}% confidence, the difference between "
            f"variant ({result.variant_rate:.2%}) and control ({result.control_rate:.2%}) is statistically real, "
            f"not due to random chance. A p-value of {result.p_value:.4f} means there's only a "
            f"{result.p_value * 100:.2f}% probability this result occurred by chance."
        )
    else:
        return (
            f"**No significant difference detected** (p-value: {result.p_value:.4f}).\n\n"
            f"_What this means:_ The observed difference between variant ({result.variant_rate:.2%}) and "
            f"control ({result.control_rate:.2%}) could be due to random chance. A p-value of {result.p_value:.4f} "
            f"is above the {1 - result.confidence/100:.2f} threshold needed for {result.confidence}% confidence. "
            f"Consider running the test longer to collect more data."
        )


def analyze(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    confidence: int = 95,
) -> TestResults:
    if control_conversions > control_visitors:
        raise ValueError("control_conversions cannot exceed control_visitors")
    if variant_conversions > variant_visitors:
        raise ValueError("variant_conversions cannot exceed variant_visitors")
    
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    
    lift_absolute = p2 - p1
    lift_percent = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    p_pooled = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_visitors + 1/variant_visitors))
    
    if se_pooled > 0:
        z_stat = (p2 - p1) / se_pooled
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    else:
        z_stat = 0
        p_value = 1.0
    
    se_diff = math.sqrt(p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / variant_visitors)
    z_crit = norm.ppf(1 - alpha / 2)
    ci_lower = lift_absolute - z_crit * se_diff
    ci_upper = lift_absolute + z_crit * se_diff
    
    is_significant = p_value < alpha
    
    if is_significant:
        winner = "variant" if p2 > p1 else "control"
    else:
        winner = "no winner yet"
    
    result = TestResults(
        control_rate=p1,
        variant_rate=p2,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        winner=winner,
        recommendation="",
    )
    
    result.recommendation = _generate_recommendation(result)
    
    return result


def _pairwise_z_test(v1: Variant, v2: Variant, confidence: int) -> PairwiseComparison:
    p1 = v1.rate
    p2 = v2.rate
    
    lift_absolute = p2 - p1
    lift_percent = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    p_pooled = (v1.conversions + v2.conversions) / (v1.visitors + v2.visitors)
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/v1.visitors + 1/v2.visitors))
    
    if se_pooled > 0:
        z_stat = (p2 - p1) / se_pooled
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    else:
        p_value = 1.0
    
    se_diff = math.sqrt(p1 * (1 - p1) / v1.visitors + p2 * (1 - p2) / v2.visitors)
    z_crit = norm.ppf(1 - alpha / 2)
    ci_lower = lift_absolute - z_crit * se_diff
    ci_upper = lift_absolute + z_crit * se_diff
    
    return PairwiseComparison(
        variant_a=v1.name,
        variant_b=v2.name,
        rate_a=p1,
        rate_b=p2,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        p_value=p_value,
        p_value_adjusted=p_value,
        is_significant=p_value < alpha,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
    )


def analyze_multi(
    variants: List[Dict[str, Any]],
    confidence: int = 95,
    correction: Literal["bonferroni", "none"] = "bonferroni",
) -> MultiVariantResults:
    if len(variants) < 2:
        raise ValueError("At least 2 variants are required")
    
    variant_objects = []
    for v in variants:
        if v["conversions"] > v["visitors"]:
            raise ValueError(f"conversions cannot exceed visitors for variant '{v['name']}'")
        variant_objects.append(Variant(
            name=v["name"],
            visitors=v["visitors"],
            conversions=v["conversions"],
        ))
    
    observed = []
    for v in variant_objects:
        observed.append([v.conversions, v.visitors - v.conversions])
    
    chi2, p_value, dof, expected = chi2_contingency(observed)
    
    alpha = 1 - (confidence / 100)
    is_significant = p_value < alpha
    
    rates = [(v.name, v.rate) for v in variant_objects]
    rates_sorted = sorted(rates, key=lambda x: x[1], reverse=True)
    best_variant = rates_sorted[0][0]
    worst_variant = rates_sorted[-1][0]
    
    pairwise = []
    num_comparisons = len(variant_objects) * (len(variant_objects) - 1) // 2
    
    for i in range(len(variant_objects)):
        for j in range(i + 1, len(variant_objects)):
            comparison = _pairwise_z_test(variant_objects[i], variant_objects[j], confidence)
            
            if correction == "bonferroni":
                comparison.p_value_adjusted = min(1.0, comparison.p_value * num_comparisons)
                comparison.is_significant = comparison.p_value_adjusted < alpha
            
            pairwise.append(comparison)
    
    recommendation = _generate_multi_recommendation(
        variant_objects, is_significant, p_value, best_variant, pairwise, confidence
    )
    
    return MultiVariantResults(
        variants=variant_objects,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        test_statistic=chi2,
        degrees_of_freedom=dof,
        best_variant=best_variant,
        worst_variant=worst_variant,
        pairwise_comparisons=pairwise,
        recommendation=recommendation,
    )


def _generate_multi_recommendation(
    variants: List[Variant],
    is_significant: bool,
    p_value: float,
    best_variant: str,
    pairwise: List[PairwiseComparison],
    confidence: int,
) -> str:
    if is_significant:
        best = next(v for v in variants if v.name == best_variant)
        sig_wins = [p for p in pairwise if p.is_significant and 
                   ((p.variant_b == best_variant and p.lift_percent > 0) or 
                    (p.variant_a == best_variant and p.lift_percent < 0))]
        
        return (
            f"**Significant differences detected across variants** (p-value: {p_value:.4f}).\n\n"
            f"_What this means:_ With {confidence}% confidence, at least one variant performs "
            f"differently from the others. **{best_variant}** has the highest conversion rate "
            f"({best.rate:.2%}). "
            f"{'It significantly outperforms ' + str(len(sig_wins)) + ' other variant(s) in pairwise comparisons.' if sig_wins else 'Check pairwise comparisons for details.'}"
        )
    else:
        return (
            f"**No significant differences detected across variants** (p-value: {p_value:.4f}).\n\n"
            f"_What this means:_ The observed differences between variants could be due to random chance. "
            f"A p-value of {p_value:.4f} is above the {1 - confidence/100:.2f} threshold needed for "
            f"{confidence}% confidence. Consider running the test longer to collect more data."
        )


def confidence_interval(
    visitors: int,
    conversions: int,
    confidence: int = 95,
) -> ConfidenceInterval:
    if conversions > visitors:
        raise ValueError("conversions cannot exceed visitors")
    if visitors <= 0:
        raise ValueError("visitors must be positive")
    
    rate = conversions / visitors
    alpha = 1 - (confidence / 100)
    z = norm.ppf(1 - alpha / 2)
    
    denominator = 1 + z**2 / visitors
    center = (rate + z**2 / (2 * visitors)) / denominator
    margin = z * math.sqrt((rate * (1 - rate) + z**2 / (4 * visitors)) / visitors) / denominator
    
    lower = max(0, center - margin)
    upper = min(1, center + margin)
    
    return ConfidenceInterval(
        rate=rate,
        lower=lower,
        upper=upper,
        confidence=confidence,
        margin_of_error=margin,
    )


def summarize(result: TestResults, test_name: str = "A/B Test") -> str:
    lines = []
    lines.append(f"## 📊 {test_name} Results\n")
    
    direction = "higher" if result.variant_rate > result.control_rate else "lower"
    abs_direction = "increase" if result.lift_percent > 0 else "decrease"
    
    if result.is_significant:
        lines.append(f"### ✅ Significant Result\n")
        lines.append(f"**The test variant performed significantly {direction} than the control.**\n")
        lines.append(f"- **Control conversion rate:** {result.control_rate:.2%} ({result.control_conversions:,} / {result.control_visitors:,})")
        lines.append(f"- **Variant conversion rate:** {result.variant_rate:.2%} ({result.variant_conversions:,} / {result.variant_visitors:,})")
        lines.append(f"- **Relative lift:** {result.lift_percent:+.1f}% {abs_direction}")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Confidence level:** {result.confidence}%\n")
        lines.append(f"### 📝 What This Means\n")
        lines.append(f"With {result.confidence}% confidence, the difference is statistically significant. ")
        lines.append(f"The p-value of **{result.p_value:.4f}** indicates there's only a **{result.p_value * 100:.2f}%** chance ")
        lines.append(f"this result is due to random variation. ")
        if result.winner == "variant":
            lines.append(f"The variant shows a **{abs(result.lift_percent):.1f}%** improvement over control.")
        else:
            lines.append(f"The control outperforms the variant by **{abs(result.lift_percent):.1f}%**.")
    else:
        lines.append(f"### ⏳ Not Yet Significant\n")
        lines.append(f"**No statistically significant difference detected between control and variant.**\n")
        lines.append(f"- **Control conversion rate:** {result.control_rate:.2%} ({result.control_conversions:,} / {result.control_visitors:,})")
        lines.append(f"- **Variant conversion rate:** {result.variant_rate:.2%} ({result.variant_conversions:,} / {result.variant_visitors:,})")
        lines.append(f"- **Observed lift:** {result.lift_percent:+.1f}%")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Required confidence:** {result.confidence}%\n")
        lines.append(f"### 📝 What This Means\n")
        lines.append(f"The p-value of **{result.p_value:.4f}** is above the **{(1 - result.confidence/100):.2f}** threshold ")
        lines.append(f"needed for {result.confidence}% confidence. The observed {abs(result.lift_percent):.1f}% difference ")
        lines.append(f"could be due to random chance. Continue running the test to gather more data.")
    
    return "\n".join(lines)


def summarize_multi(result: MultiVariantResults, test_name: str = "Multi-Variant Test") -> str:
    lines = []
    lines.append(f"## 📊 {test_name} Results\n")
    
    if result.is_significant:
        lines.append(f"### ✅ Significant Differences Detected\n")
        lines.append(f"**At least one variant performs differently from the others.**\n")
    else:
        lines.append(f"### ⏳ No Significant Differences\n")
        lines.append(f"**The observed differences could be due to random chance.**\n")
    
    lines.append(f"### Variant Performance\n")
    lines.append(f"| Variant | Visitors | Conversions | Rate |")
    lines.append(f"|---------|----------|-------------|------|")
    
    sorted_variants = sorted(result.variants, key=lambda v: v.rate, reverse=True)
    for i, v in enumerate(sorted_variants):
        marker = " 🏆" if v.name == result.best_variant else ""
        lines.append(f"| {v.name}{marker} | {v.visitors:,} | {v.conversions:,} | {v.rate:.2%} |")
    
    lines.append(f"\n### Overall Test (Chi-Square)\n")
    lines.append(f"- **Test statistic:** {result.test_statistic:.2f}")
    lines.append(f"- **Degrees of freedom:** {result.degrees_of_freedom}")
    lines.append(f"- **P-value:** {result.p_value:.4f}")
    lines.append(f"- **Confidence level:** {result.confidence}%\n")
    
    sig_comparisons = [p for p in result.pairwise_comparisons if p.is_significant]
    if sig_comparisons:
        lines.append(f"### Significant Pairwise Differences\n")
        for p in sig_comparisons:
            winner = p.variant_b if p.lift_percent > 0 else p.variant_a
            loser = p.variant_a if p.lift_percent > 0 else p.variant_b
            lift = abs(p.lift_percent)
            lines.append(f"- **{winner}** beats **{loser}** by {lift:.1f}% (p={p.p_value_adjusted:.4f})")
        lines.append("")
    
    lines.append(f"### 📝 What This Means\n")
    if result.is_significant:
        lines.append(f"With {result.confidence}% confidence, there are real differences between your variants. ")
        lines.append(f"**{result.best_variant}** has the highest conversion rate. ")
        if sig_comparisons:
            lines.append(f"The pairwise comparisons above show which specific differences are statistically significant ")
            lines.append(f"(adjusted for multiple comparisons using Bonferroni correction).")
        else:
            lines.append(f"However, no individual pairwise comparison reached significance after adjusting for multiple comparisons.")
    else:
        lines.append(f"The p-value of **{result.p_value:.4f}** is above the **{(1 - result.confidence/100):.2f}** threshold. ")
        lines.append(f"The differences you see could be due to random variation. ")
        lines.append(f"Continue running the test to gather more data.")
    
    return "\n".join(lines)


def summarize_plan(plan: SampleSizePlan, test_name: str = "A/B Test") -> str:
    lines = []
    lines.append(f"## 📋 {test_name} Sample Size Plan\n")
    
    lines.append(f"### Test Parameters\n")
    lines.append(f"- **Current conversion rate:** {plan.current_rate:.2%}")
    lines.append(f"- **Minimum detectable lift:** {plan.lift_percent:+.0f}%")
    lines.append(f"- **Expected variant rate:** {plan.expected_rate:.2%}")
    lines.append(f"- **Confidence level:** {plan.confidence}%")
    lines.append(f"- **Statistical power:** {plan.power}%\n")
    
    lines.append(f"### Required Sample Size\n")
    lines.append(f"- **Per variant:** {plan.visitors_per_variant:,} visitors")
    lines.append(f"- **Total:** {plan.total_visitors:,} visitors\n")
    
    if plan.test_duration_days:
        lines.append(f"### Estimated Duration\n")
        if plan.test_duration_days < 7:
            lines.append(f"Approximately **{plan.test_duration_days} days** to complete.\n")
        elif plan.test_duration_days < 30:
            weeks = plan.test_duration_days / 7
            lines.append(f"Approximately **{weeks:.1f} weeks** ({plan.test_duration_days} days) to complete.\n")
        else:
            months = plan.test_duration_days / 30
            lines.append(f"Approximately **{months:.1f} months** ({plan.test_duration_days} days) to complete.\n")
    
    lines.append(f"### 📝 What This Means\n")
    lines.append(f"If the variant truly improves conversion by {plan.lift_percent}% or more, ")
    lines.append(f"this test has a **{plan.power}%** chance of detecting it. ")
    lines.append(f"There's a **{100 - plan.confidence}%** false positive risk ")
    lines.append(f"(declaring a winner when there's no real difference).")
    
    return "\n".join(lines)
