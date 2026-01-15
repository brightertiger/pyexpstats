import math
from scipy.stats import norm, t, f as f_dist
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class SampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_mean: float
    expected_mean: float
    standard_deviation: float
    lift_percent: float
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self

@dataclass
class TestResults:
    control_mean: float
    variant_mean: float
    lift_percent: float
    lift_absolute: float
    is_significant: bool
    confidence: int
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_visitors: int
    control_std: float
    variant_visitors: int
    variant_std: float
    winner: Literal["control", "variant", "no winner yet"]
    recommendation: str

@dataclass
class ConfidenceInterval:
    mean: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float

@dataclass
class Variant:
    name: str
    visitors: int
    mean: float
    std: float

@dataclass
class PairwiseComparison:
    variant_a: str
    variant_b: str
    mean_a: float
    mean_b: float
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
    f_statistic: float
    df_between: int
    df_within: int
    best_variant: str
    worst_variant: str
    pairwise_comparisons: List[PairwiseComparison]
    recommendation: str


def sample_size(
    current_mean: float,
    current_std: float,
    lift_percent: float = 5,
    confidence: int = 95,
    power: int = 80,
    num_variants: int = 2,
) -> SampleSizePlan:
    lift_decimal = lift_percent / 100
    expected_mean = current_mean * (1 + lift_decimal)
    absolute_effect = abs(expected_mean - current_mean)
    
    if absolute_effect == 0:
        raise ValueError("lift_percent cannot be zero")
    if current_std <= 0:
        raise ValueError("current_std must be positive")
    if num_variants < 2:
        raise ValueError("num_variants must be at least 2")
    
    alpha = 1 - (confidence / 100)
    if num_variants > 2:
        alpha = alpha / (num_variants - 1)
    
    beta = 1 - (power / 100)
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(1 - beta)
    
    n = math.ceil(2 * ((z_alpha + z_beta) * current_std / absolute_effect) ** 2)
    
    return SampleSizePlan(
        visitors_per_variant=n,
        total_visitors=n * num_variants,
        current_mean=current_mean,
        expected_mean=expected_mean,
        standard_deviation=current_std,
        lift_percent=lift_percent,
        confidence=confidence,
        power=power,
    )


def _generate_recommendation(result: 'TestResults', currency: str = "$") -> str:
    direction = "higher" if result.variant_mean > result.control_mean else "lower"
    
    if result.is_significant:
        return (
            f"**Test variant is significantly {direction} than control** (p-value: {result.p_value:.4f}).\n\n"
            f"_What this means:_ With {result.confidence}% confidence, the difference between "
            f"variant ({currency}{result.variant_mean:,.2f}) and control ({currency}{result.control_mean:,.2f}) is statistically real, "
            f"not due to random chance. A p-value of {result.p_value:.4f} means there's only a "
            f"{result.p_value * 100:.2f}% probability this result occurred by chance."
        )
    else:
        return (
            f"**No significant difference detected** (p-value: {result.p_value:.4f}).\n\n"
            f"_What this means:_ The observed difference between variant ({currency}{result.variant_mean:,.2f}) and "
            f"control ({currency}{result.control_mean:,.2f}) could be due to random chance. A p-value of {result.p_value:.4f} "
            f"is above the {1 - result.confidence/100:.2f} threshold needed for {result.confidence}% confidence. "
            f"Consider running the test longer to collect more data."
        )


def analyze(
    control_visitors: int,
    control_mean: float,
    control_std: float,
    variant_visitors: int,
    variant_mean: float,
    variant_std: float,
    confidence: int = 95,
) -> TestResults:
    if control_visitors <= 0 or variant_visitors <= 0:
        raise ValueError("visitors must be positive")
    if control_std < 0 or variant_std < 0:
        raise ValueError("standard deviation cannot be negative")
    
    lift_absolute = variant_mean - control_mean
    lift_percent = ((variant_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    var1 = control_std ** 2
    var2 = variant_std ** 2
    
    se = math.sqrt(var1 / control_visitors + var2 / variant_visitors)
    
    if se > 0:
        t_stat = lift_absolute / se
        
        numerator = (var1 / control_visitors + var2 / variant_visitors) ** 2
        denominator = (var1 / control_visitors) ** 2 / (control_visitors - 1) + \
                      (var2 / variant_visitors) ** 2 / (variant_visitors - 1)
        df = numerator / denominator if denominator > 0 else control_visitors + variant_visitors - 2
        
        p_value = 2 * (1 - t.cdf(abs(t_stat), df))
    else:
        t_stat = 0
        p_value = 1.0
        df = control_visitors + variant_visitors - 2
    
    t_crit = t.ppf(1 - alpha / 2, df)
    ci_lower = lift_absolute - t_crit * se
    ci_upper = lift_absolute + t_crit * se
    
    is_significant = p_value < alpha
    
    if is_significant:
        winner = "variant" if variant_mean > control_mean else "control"
    else:
        winner = "no winner yet"
    
    result = TestResults(
        control_mean=control_mean,
        variant_mean=variant_mean,
        lift_percent=lift_percent,
        lift_absolute=lift_absolute,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
        control_visitors=control_visitors,
        control_std=control_std,
        variant_visitors=variant_visitors,
        variant_std=variant_std,
        winner=winner,
        recommendation="",
    )
    
    result.recommendation = _generate_recommendation(result)
    
    return result


def _pairwise_welch_t_test(v1: Variant, v2: Variant, confidence: int) -> PairwiseComparison:
    lift_absolute = v2.mean - v1.mean
    lift_percent = ((v2.mean - v1.mean) / v1.mean * 100) if v1.mean != 0 else 0
    
    alpha = 1 - (confidence / 100)
    
    var1 = v1.std ** 2
    var2 = v2.std ** 2
    
    se = math.sqrt(var1 / v1.visitors + var2 / v2.visitors)
    
    if se > 0:
        t_stat = lift_absolute / se
        
        numerator = (var1 / v1.visitors + var2 / v2.visitors) ** 2
        denominator = (var1 / v1.visitors) ** 2 / (v1.visitors - 1) + \
                      (var2 / v2.visitors) ** 2 / (v2.visitors - 1)
        df = numerator / denominator if denominator > 0 else v1.visitors + v2.visitors - 2
        
        p_value = 2 * (1 - t.cdf(abs(t_stat), df))
    else:
        p_value = 1.0
        df = v1.visitors + v2.visitors - 2
    
    t_crit = t.ppf(1 - alpha / 2, df)
    ci_lower = lift_absolute - t_crit * se
    ci_upper = lift_absolute + t_crit * se
    
    return PairwiseComparison(
        variant_a=v1.name,
        variant_b=v2.name,
        mean_a=v1.mean,
        mean_b=v2.mean,
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
        if v["visitors"] <= 0:
            raise ValueError(f"visitors must be positive for variant '{v['name']}'")
        if v.get("std", 0) < 0:
            raise ValueError(f"std cannot be negative for variant '{v['name']}'")
        variant_objects.append(Variant(
            name=v["name"],
            visitors=v["visitors"],
            mean=v["mean"],
            std=v.get("std", 0),
        ))
    
    k = len(variant_objects)
    N = sum(v.visitors for v in variant_objects)
    
    grand_mean = sum(v.mean * v.visitors for v in variant_objects) / N
    
    ss_between = sum(v.visitors * (v.mean - grand_mean) ** 2 for v in variant_objects)
    
    ss_within = sum((v.visitors - 1) * v.std ** 2 for v in variant_objects)
    
    df_between = k - 1
    df_within = N - k
    
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 1
    
    f_stat = ms_between / ms_within if ms_within > 0 else 0
    
    p_value = 1 - f_dist.cdf(f_stat, df_between, df_within) if f_stat > 0 else 1.0
    
    alpha = 1 - (confidence / 100)
    is_significant = p_value < alpha
    
    means = [(v.name, v.mean) for v in variant_objects]
    means_sorted = sorted(means, key=lambda x: x[1], reverse=True)
    best_variant = means_sorted[0][0]
    worst_variant = means_sorted[-1][0]
    
    pairwise = []
    num_comparisons = k * (k - 1) // 2
    
    for i in range(len(variant_objects)):
        for j in range(i + 1, len(variant_objects)):
            comparison = _pairwise_welch_t_test(variant_objects[i], variant_objects[j], confidence)
            
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
        f_statistic=f_stat,
        df_between=df_between,
        df_within=df_within,
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
            f"differently from the others. **{best_variant}** has the highest mean value "
            f"({best.mean:,.2f}). "
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
    mean: float,
    std: float,
    confidence: int = 95,
) -> ConfidenceInterval:
    if visitors <= 1:
        raise ValueError("visitors must be greater than 1")
    if std < 0:
        raise ValueError("standard deviation cannot be negative")
    
    alpha = 1 - (confidence / 100)
    se = std / math.sqrt(visitors)
    t_crit = t.ppf(1 - alpha / 2, visitors - 1)
    margin = t_crit * se
    
    return ConfidenceInterval(
        mean=mean,
        lower=mean - margin,
        upper=mean + margin,
        confidence=confidence,
        margin_of_error=margin,
    )


def summarize(result: TestResults, test_name: str = "Revenue Test", metric_name: str = "Average Order Value", currency: str = "$") -> str:
    lines = []
    lines.append(f"## 📊 {test_name} Results\n")
    
    direction = "higher" if result.variant_mean > result.control_mean else "lower"
    abs_direction = "increase" if result.lift_percent > 0 else "decrease"
    
    if result.is_significant:
        lines.append(f"### ✅ Significant Result\n")
        lines.append(f"**The test variant's {metric_name.lower()} is significantly {direction} than control.**\n")
        lines.append(f"- **Control {metric_name.lower()}:** {currency}{result.control_mean:,.2f} (n={result.control_visitors:,}, std={currency}{result.control_std:,.2f})")
        lines.append(f"- **Variant {metric_name.lower()}:** {currency}{result.variant_mean:,.2f} (n={result.variant_visitors:,}, std={currency}{result.variant_std:,.2f})")
        lines.append(f"- **Relative lift:** {result.lift_percent:+.1f}% {abs_direction}")
        lines.append(f"- **Absolute difference:** {currency}{result.lift_absolute:+,.2f}")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Confidence level:** {result.confidence}%\n")
        lines.append(f"### 📝 What This Means\n")
        lines.append(f"With {result.confidence}% confidence, the difference is statistically significant. ")
        lines.append(f"The p-value of **{result.p_value:.4f}** indicates there's only a **{result.p_value * 100:.2f}%** chance ")
        lines.append(f"this result is due to random variation. ")
        if result.winner == "variant":
            lines.append(f"The variant shows a **{currency}{abs(result.lift_absolute):,.2f}** ({abs(result.lift_percent):.1f}%) improvement over control.")
        else:
            lines.append(f"The control outperforms the variant by **{currency}{abs(result.lift_absolute):,.2f}** ({abs(result.lift_percent):.1f}%).")
    else:
        lines.append(f"### ⏳ Not Yet Significant\n")
        lines.append(f"**No statistically significant difference detected between control and variant.**\n")
        lines.append(f"- **Control {metric_name.lower()}:** {currency}{result.control_mean:,.2f} (n={result.control_visitors:,}, std={currency}{result.control_std:,.2f})")
        lines.append(f"- **Variant {metric_name.lower()}:** {currency}{result.variant_mean:,.2f} (n={result.variant_visitors:,}, std={currency}{result.variant_std:,.2f})")
        lines.append(f"- **Observed lift:** {result.lift_percent:+.1f}% ({currency}{result.lift_absolute:+,.2f})")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Required confidence:** {result.confidence}%\n")
        lines.append(f"### 📝 What This Means\n")
        lines.append(f"The p-value of **{result.p_value:.4f}** is above the **{(1 - result.confidence/100):.2f}** threshold ")
        lines.append(f"needed for {result.confidence}% confidence. The observed {currency}{abs(result.lift_absolute):,.2f} difference ")
        lines.append(f"could be due to random chance. Continue running the test to gather more data.")
    
    return "\n".join(lines)


def summarize_multi(result: MultiVariantResults, test_name: str = "Multi-Variant Test", metric_name: str = "Average Value", currency: str = "$") -> str:
    lines = []
    lines.append(f"## 📊 {test_name} Results\n")
    
    if result.is_significant:
        lines.append(f"### ✅ Significant Differences Detected\n")
        lines.append(f"**At least one variant performs differently from the others.**\n")
    else:
        lines.append(f"### ⏳ No Significant Differences\n")
        lines.append(f"**The observed differences could be due to random chance.**\n")
    
    lines.append(f"### Variant Performance ({metric_name})\n")
    lines.append(f"| Variant | Sample Size | Mean | Std Dev |")
    lines.append(f"|---------|-------------|------|---------|")
    
    sorted_variants = sorted(result.variants, key=lambda v: v.mean, reverse=True)
    for v in sorted_variants:
        marker = " 🏆" if v.name == result.best_variant else ""
        lines.append(f"| {v.name}{marker} | {v.visitors:,} | {currency}{v.mean:,.2f} | {currency}{v.std:,.2f} |")
    
    lines.append(f"\n### Overall Test (ANOVA)\n")
    lines.append(f"- **F-statistic:** {result.f_statistic:.2f}")
    lines.append(f"- **Degrees of freedom:** ({result.df_between}, {result.df_within})")
    lines.append(f"- **P-value:** {result.p_value:.4f}")
    lines.append(f"- **Confidence level:** {result.confidence}%\n")
    
    sig_comparisons = [p for p in result.pairwise_comparisons if p.is_significant]
    if sig_comparisons:
        lines.append(f"### Significant Pairwise Differences\n")
        for p in sig_comparisons:
            winner = p.variant_b if p.lift_percent > 0 else p.variant_a
            loser = p.variant_a if p.lift_percent > 0 else p.variant_b
            diff = abs(p.lift_absolute)
            lines.append(f"- **{winner}** beats **{loser}** by {currency}{diff:,.2f} ({abs(p.lift_percent):.1f}%, p={p.p_value_adjusted:.4f})")
        lines.append("")
    
    lines.append(f"### 📝 What This Means\n")
    if result.is_significant:
        lines.append(f"With {result.confidence}% confidence, there are real differences between your variants. ")
        lines.append(f"**{result.best_variant}** has the highest {metric_name.lower()}. ")
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


def summarize_plan(plan: SampleSizePlan, test_name: str = "Revenue Test", metric_name: str = "Average Order Value", currency: str = "$") -> str:
    lines = []
    lines.append(f"## 📋 {test_name} Sample Size Plan\n")
    
    lines.append(f"### Test Parameters ({metric_name})\n")
    lines.append(f"- **Current mean:** {currency}{plan.current_mean:,.2f}")
    lines.append(f"- **Standard deviation:** {currency}{plan.standard_deviation:,.2f}")
    lines.append(f"- **Minimum detectable lift:** {plan.lift_percent:+.0f}%")
    lines.append(f"- **Expected variant mean:** {currency}{plan.expected_mean:,.2f}")
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
    lines.append(f"If the variant truly improves {metric_name.lower()} by {plan.lift_percent}% or more, ")
    lines.append(f"this test has a **{plan.power}%** chance of detecting it. ")
    lines.append(f"There's a **{100 - plan.confidence}%** false positive risk ")
    lines.append(f"(declaring a winner when there's no real difference).")
    
    return "\n".join(lines)
