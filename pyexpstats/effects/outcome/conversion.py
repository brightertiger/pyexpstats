import math
from scipy.stats import norm, chi2_contingency
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass

from pyexpstats.effects.outcome.base import FullOutcomeEffect
from pyexpstats.utils.stats import (
    sample_size_two_proportions,
    z_test_two_proportions,
    proportion_ci,
    proportion_difference_se,
    lift_calculations,
    bonferroni_correction,
    z_alpha as get_z_alpha,
)


@dataclass
class ConversionSampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_rate: float
    expected_rate: float
    lift_percent: float
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    @property
    def subjects_per_group(self) -> int:
        return self.visitors_per_variant
    
    @property
    def total_subjects(self) -> int:
        return self.total_visitors
    
    def with_daily_traffic(self, daily_visitors: int) -> 'ConversionSampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self


@dataclass
class ConversionTestResults:
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
    
    @property
    def point_estimate(self) -> float:
        return self.lift_absolute
    
    @property
    def effect_size(self) -> float:
        return self.lift_percent


@dataclass
class ConversionConfidenceInterval:
    rate: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float
    
    @property
    def point_estimate(self) -> float:
        return self.rate
    
    @property
    def lower_bound(self) -> float:
        return self.lower
    
    @property
    def upper_bound(self) -> float:
        return self.upper


@dataclass
class ConversionVariant:
    name: str
    visitors: int
    conversions: int
    
    @property
    def rate(self) -> float:
        return self.conversions / self.visitors if self.visitors > 0 else 0


@dataclass
class ConversionPairwiseComparison:
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
    
    @property
    def difference(self) -> float:
        return self.lift_absolute


@dataclass
class ConversionMultiVariantResults:
    variants: List[ConversionVariant]
    is_significant: bool
    confidence: int
    p_value: float
    test_statistic: float
    degrees_of_freedom: int
    best_variant: str
    worst_variant: str
    pairwise_comparisons: List[ConversionPairwiseComparison]
    recommendation: str


@dataclass
class ConversionDiffInDiffResults:
    control_pre_rate: float
    control_post_rate: float
    treatment_pre_rate: float
    treatment_post_rate: float
    control_change: float
    treatment_change: float
    diff_in_diff: float
    diff_in_diff_percent: float
    is_significant: bool
    confidence: int
    p_value: float
    z_statistic: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_pre_visitors: int
    control_pre_conversions: int
    control_post_visitors: int
    control_post_conversions: int
    treatment_pre_visitors: int
    treatment_pre_conversions: int
    treatment_post_visitors: int
    treatment_post_conversions: int
    recommendation: str


class ConversionEffect(FullOutcomeEffect):
    
    def sample_size(
        self,
        current_rate: float,
        lift_percent: float = 10,
        confidence: int = 95,
        power: int = 80,
        num_variants: int = 2,
    ) -> ConversionSampleSizePlan:
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
        
        result = sample_size_two_proportions(
            p1=current_rate,
            p2=expected_rate,
            confidence=confidence,
            power=power,
            num_groups=num_variants,
        )
        
        return ConversionSampleSizePlan(
            visitors_per_variant=result.n_per_group,
            total_visitors=result.n_total,
            current_rate=current_rate,
            expected_rate=expected_rate,
            lift_percent=lift_percent,
            confidence=confidence,
            power=power,
        )
    
    def analyze(
        self,
        control_visitors: int,
        control_conversions: int,
        variant_visitors: int,
        variant_conversions: int,
        confidence: int = 95,
    ) -> ConversionTestResults:
        if control_conversions > control_visitors:
            raise ValueError("control_conversions cannot exceed control_visitors")
        if variant_conversions > variant_visitors:
            raise ValueError("variant_conversions cannot exceed variant_visitors")
        
        p1 = control_conversions / control_visitors
        p2 = variant_conversions / variant_visitors
        
        lift_absolute, lift_percent = lift_calculations(p1, p2)
        
        test_result = z_test_two_proportions(p1, control_visitors, p2, variant_visitors, confidence)
        
        se_diff = proportion_difference_se(p1, control_visitors, p2, variant_visitors)
        z_crit = get_z_alpha(confidence)
        ci_lower = lift_absolute - z_crit * se_diff
        ci_upper = lift_absolute + z_crit * se_diff
        
        if test_result.is_significant:
            winner = "variant" if p2 > p1 else "control"
        else:
            winner = "no winner yet"
        
        result = ConversionTestResults(
            control_rate=p1,
            variant_rate=p2,
            lift_percent=lift_percent,
            lift_absolute=lift_absolute,
            is_significant=test_result.is_significant,
            confidence=confidence,
            p_value=test_result.p_value,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            control_visitors=control_visitors,
            control_conversions=control_conversions,
            variant_visitors=variant_visitors,
            variant_conversions=variant_conversions,
            winner=winner,
            recommendation="",
        )
        
        result.recommendation = self._generate_recommendation(result)
        
        return result
    
    def _generate_recommendation(self, result: ConversionTestResults) -> str:
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
    
    def _pairwise_z_test(self, v1: ConversionVariant, v2: ConversionVariant, confidence: int, num_comparisons: int = 1) -> ConversionPairwiseComparison:
        p1 = v1.rate
        p2 = v2.rate

        lift_absolute, lift_percent = lift_calculations(p1, p2)

        test_result = z_test_two_proportions(p1, v1.visitors, p2, v2.visitors, confidence)

        se_diff = proportion_difference_se(p1, v1.visitors, p2, v2.visitors)
        # Adjust CI for multiple comparisons (Bonferroni)
        adjusted_confidence = 100 - (100 - confidence) / num_comparisons if num_comparisons > 1 else confidence
        z_crit = get_z_alpha(int(adjusted_confidence))
        ci_lower = lift_absolute - z_crit * se_diff
        ci_upper = lift_absolute + z_crit * se_diff

        return ConversionPairwiseComparison(
            variant_a=v1.name,
            variant_b=v2.name,
            rate_a=p1,
            rate_b=p2,
            lift_percent=lift_percent,
            lift_absolute=lift_absolute,
            p_value=test_result.p_value,
            p_value_adjusted=test_result.p_value,
            is_significant=test_result.is_significant,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
        )
    
    def analyze_multi(
        self,
        variants: List[Dict[str, Any]],
        confidence: int = 95,
        correction: Literal["bonferroni", "none"] = "bonferroni",
    ) -> ConversionMultiVariantResults:
        if len(variants) < 2:
            raise ValueError("At least 2 variants are required")
        
        names = [v["name"] for v in variants]
        if len(names) != len(set(names)):
            raise ValueError("Variant names must be unique")
        
        variant_objects = []
        for v in variants:
            if v["conversions"] > v["visitors"]:
                raise ValueError(f"conversions cannot exceed visitors for variant '{v['name']}'")
            variant_objects.append(ConversionVariant(
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
                comparison = self._pairwise_z_test(variant_objects[i], variant_objects[j], confidence, num_comparisons)
                
                if correction == "bonferroni":
                    comparison.p_value_adjusted = bonferroni_correction(comparison.p_value, num_comparisons)
                    comparison.is_significant = comparison.p_value_adjusted < alpha
                
                pairwise.append(comparison)
        
        recommendation = self._generate_multi_recommendation(
            variant_objects, is_significant, p_value, best_variant, pairwise, confidence
        )
        
        return ConversionMultiVariantResults(
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
        self,
        variants: List[ConversionVariant],
        is_significant: bool,
        p_value: float,
        best_variant: str,
        pairwise: List[ConversionPairwiseComparison],
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
        self,
        visitors: int,
        conversions: int,
        confidence: int = 95,
    ) -> ConversionConfidenceInterval:
        if conversions > visitors:
            raise ValueError("conversions cannot exceed visitors")
        if visitors <= 0:
            raise ValueError("visitors must be positive")
        
        rate, lower, upper, margin = proportion_ci(conversions, visitors, confidence, method="wilson")
        
        return ConversionConfidenceInterval(
            rate=rate,
            lower=lower,
            upper=upper,
            confidence=confidence,
            margin_of_error=margin,
        )
    
    def summarize(self, result: ConversionTestResults, test_name: str = "A/B Test") -> str:
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
    
    def summarize_multi(self, result: ConversionMultiVariantResults, test_name: str = "Multi-Variant Test") -> str:
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
    
    def summarize_plan(self, plan: ConversionSampleSizePlan, test_name: str = "A/B Test") -> str:
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
    
    def diff_in_diff(
        self,
        control_pre_visitors: int,
        control_pre_conversions: int,
        control_post_visitors: int,
        control_post_conversions: int,
        treatment_pre_visitors: int,
        treatment_pre_conversions: int,
        treatment_post_visitors: int,
        treatment_post_conversions: int,
        confidence: int = 95,
    ) -> ConversionDiffInDiffResults:
        if control_pre_conversions > control_pre_visitors:
            raise ValueError("control_pre_conversions cannot exceed control_pre_visitors")
        if control_post_conversions > control_post_visitors:
            raise ValueError("control_post_conversions cannot exceed control_post_visitors")
        if treatment_pre_conversions > treatment_pre_visitors:
            raise ValueError("treatment_pre_conversions cannot exceed treatment_pre_visitors")
        if treatment_post_conversions > treatment_post_visitors:
            raise ValueError("treatment_post_conversions cannot exceed treatment_post_visitors")
        
        p_c_pre = control_pre_conversions / control_pre_visitors
        p_c_post = control_post_conversions / control_post_visitors
        p_t_pre = treatment_pre_conversions / treatment_pre_visitors
        p_t_post = treatment_post_conversions / treatment_post_visitors
        
        control_change = p_c_post - p_c_pre
        treatment_change = p_t_post - p_t_pre
        
        did = treatment_change - control_change
        
        did_percent = (did / p_t_pre * 100) if p_t_pre > 0 else 0
        
        var_c_pre = p_c_pre * (1 - p_c_pre) / control_pre_visitors
        var_c_post = p_c_post * (1 - p_c_post) / control_post_visitors
        var_t_pre = p_t_pre * (1 - p_t_pre) / treatment_pre_visitors
        var_t_post = p_t_post * (1 - p_t_post) / treatment_post_visitors
        
        se_did = math.sqrt(var_c_pre + var_c_post + var_t_pre + var_t_post)
        
        alpha = 1 - (confidence / 100)
        z_crit = norm.ppf(1 - alpha / 2)
        
        if se_did > 0:
            z_stat = did / se_did
            p_value = 2 * (1 - norm.cdf(abs(z_stat)))
        else:
            z_stat = 0
            p_value = 1.0
        
        ci_lower = did - z_crit * se_did
        ci_upper = did + z_crit * se_did
        
        is_significant = p_value < alpha
        
        result = ConversionDiffInDiffResults(
            control_pre_rate=p_c_pre,
            control_post_rate=p_c_post,
            treatment_pre_rate=p_t_pre,
            treatment_post_rate=p_t_post,
            control_change=control_change,
            treatment_change=treatment_change,
            diff_in_diff=did,
            diff_in_diff_percent=did_percent,
            is_significant=is_significant,
            confidence=confidence,
            p_value=p_value,
            z_statistic=z_stat,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            control_pre_visitors=control_pre_visitors,
            control_pre_conversions=control_pre_conversions,
            control_post_visitors=control_post_visitors,
            control_post_conversions=control_post_conversions,
            treatment_pre_visitors=treatment_pre_visitors,
            treatment_pre_conversions=treatment_pre_conversions,
            treatment_post_visitors=treatment_post_visitors,
            treatment_post_conversions=treatment_post_conversions,
            recommendation="",
        )
        
        result.recommendation = self._generate_did_recommendation(result)
        
        return result
    
    def _generate_did_recommendation(self, result: ConversionDiffInDiffResults) -> str:
        direction = "positive" if result.diff_in_diff > 0 else "negative"
        
        if result.is_significant:
            return (
                f"**Significant treatment effect detected** (p-value: {result.p_value:.4f}).\n\n"
                f"_What this means:_ The treatment group showed a **{direction}** effect beyond what would be "
                f"expected from the control group's trend. The treatment changed conversion by "
                f"**{result.diff_in_diff:+.2%}** ({result.diff_in_diff_percent:+.1f}% relative) more than the control. "
                f"With {result.confidence}% confidence, this effect is statistically real."
            )
        else:
            return (
                f"**No significant treatment effect detected** (p-value: {result.p_value:.4f}).\n\n"
                f"_What this means:_ The observed difference-in-differences of {result.diff_in_diff:+.2%} "
                f"could be due to random chance. The treatment group's change was not significantly different "
                f"from the control group's change. Consider collecting more data or the effect may be too small to detect."
            )
    
    def summarize_diff_in_diff(self, result: ConversionDiffInDiffResults, test_name: str = "Difference-in-Differences Analysis") -> str:
        lines = []
        lines.append(f"## 📊 {test_name}\n")
        
        if result.is_significant:
            lines.append(f"### ✅ Significant Treatment Effect\n")
            direction = "increase" if result.diff_in_diff > 0 else "decrease"
            lines.append(f"**The treatment caused a significant {direction} in conversion rate.**\n")
        else:
            lines.append(f"### ⏳ No Significant Treatment Effect\n")
            lines.append(f"**The treatment effect is not statistically significant.**\n")
        
        lines.append(f"### Conversion Rates\n")
        lines.append(f"| Group | Pre-Period | Post-Period | Change |")
        lines.append(f"|-------|------------|-------------|--------|")
        lines.append(f"| Control | {result.control_pre_rate:.2%} | {result.control_post_rate:.2%} | {result.control_change:+.2%} |")
        lines.append(f"| Treatment | {result.treatment_pre_rate:.2%} | {result.treatment_post_rate:.2%} | {result.treatment_change:+.2%} |")
        lines.append("")
        
        lines.append(f"### Difference-in-Differences Estimate\n")
        lines.append(f"- **DiD Effect:** {result.diff_in_diff:+.2%} ({result.diff_in_diff_percent:+.1f}% relative)")
        lines.append(f"- **95% CI:** [{result.confidence_interval_lower:.2%}, {result.confidence_interval_upper:.2%}]")
        lines.append(f"- **Z-statistic:** {result.z_statistic:.2f}")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Confidence level:** {result.confidence}%\n")
        
        lines.append(f"### Sample Sizes\n")
        lines.append(f"| Group | Pre-Period | Post-Period |")
        lines.append(f"|-------|------------|-------------|")
        lines.append(f"| Control | {result.control_pre_visitors:,} | {result.control_post_visitors:,} |")
        lines.append(f"| Treatment | {result.treatment_pre_visitors:,} | {result.treatment_post_visitors:,} |")
        lines.append("")
        
        lines.append(f"### 📝 What This Means\n")
        if result.is_significant:
            lines.append(f"The treatment group's conversion rate changed by **{result.treatment_change:+.2%}** ")
            lines.append(f"while the control group changed by **{result.control_change:+.2%}**. ")
            lines.append(f"After accounting for the control group's trend, the treatment effect is **{result.diff_in_diff:+.2%}**. ")
            lines.append(f"This effect is statistically significant at the {result.confidence}% confidence level.")
        else:
            lines.append(f"The treatment group's conversion rate changed by **{result.treatment_change:+.2%}** ")
            lines.append(f"while the control group changed by **{result.control_change:+.2%}**. ")
            lines.append(f"The difference ({result.diff_in_diff:+.2%}) is not statistically significant. ")
            lines.append(f"This could mean the treatment had no real effect, or the sample size is insufficient to detect it.")
        
        return "\n".join(lines)


_default_instance = ConversionEffect()

sample_size = _default_instance.sample_size
analyze = _default_instance.analyze
analyze_multi = _default_instance.analyze_multi
confidence_interval = _default_instance.confidence_interval
summarize = _default_instance.summarize
summarize_multi = _default_instance.summarize_multi
summarize_plan = _default_instance.summarize_plan
diff_in_diff = _default_instance.diff_in_diff
summarize_diff_in_diff = _default_instance.summarize_diff_in_diff

SampleSizePlan = ConversionSampleSizePlan
TestResults = ConversionTestResults
ConfidenceInterval = ConversionConfidenceInterval
Variant = ConversionVariant
PairwiseComparison = ConversionPairwiseComparison
MultiVariantResults = ConversionMultiVariantResults
DiffInDiffResults = ConversionDiffInDiffResults

__all__ = [
    "ConversionEffect",
    "ConversionSampleSizePlan",
    "ConversionTestResults",
    "ConversionConfidenceInterval",
    "ConversionVariant",
    "ConversionPairwiseComparison",
    "ConversionMultiVariantResults",
    "ConversionDiffInDiffResults",
    "sample_size",
    "analyze",
    "analyze_multi",
    "confidence_interval",
    "summarize",
    "summarize_multi",
    "summarize_plan",
    "diff_in_diff",
    "summarize_diff_in_diff",
    "SampleSizePlan",
    "TestResults",
    "ConfidenceInterval",
    "Variant",
    "PairwiseComparison",
    "MultiVariantResults",
    "DiffInDiffResults",
]
