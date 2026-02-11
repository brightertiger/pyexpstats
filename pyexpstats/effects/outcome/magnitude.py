import math
from scipy.stats import norm, t, f as f_dist
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass

from pyexpstats.effects.outcome.base import FullOutcomeEffect
from pyexpstats.utils.stats import (
    sample_size_two_means,
    welch_t_test,
    mean_ci as calc_mean_ci,
    mean_difference_se,
    lift_calculations,
    bonferroni_correction,
    t_critical,
    welch_df,
)


@dataclass
class MagnitudeSampleSizePlan:
    visitors_per_variant: int
    total_visitors: int
    current_mean: float
    expected_mean: float
    standard_deviation: float
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
    
    def with_daily_traffic(self, daily_visitors: int) -> 'MagnitudeSampleSizePlan':
        self.test_duration_days = math.ceil(self.total_visitors / daily_visitors)
        return self


@dataclass
class MagnitudeTestResults:
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
    
    @property
    def point_estimate(self) -> float:
        return self.lift_absolute
    
    @property
    def effect_size(self) -> float:
        return self.lift_percent


@dataclass
class MagnitudeConfidenceInterval:
    mean: float
    lower: float
    upper: float
    confidence: int
    margin_of_error: float
    
    @property
    def point_estimate(self) -> float:
        return self.mean
    
    @property
    def lower_bound(self) -> float:
        return self.lower
    
    @property
    def upper_bound(self) -> float:
        return self.upper


@dataclass
class MagnitudeVariant:
    name: str
    visitors: int
    mean: float
    std: float


@dataclass
class MagnitudePairwiseComparison:
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
    
    @property
    def difference(self) -> float:
        return self.lift_absolute


@dataclass
class MagnitudeMultiVariantResults:
    variants: List[MagnitudeVariant]
    is_significant: bool
    confidence: int
    p_value: float
    f_statistic: float
    df_between: int
    df_within: int
    best_variant: str
    worst_variant: str
    pairwise_comparisons: List[MagnitudePairwiseComparison]
    recommendation: str


@dataclass
class MagnitudeDiffInDiffResults:
    control_pre_mean: float
    control_post_mean: float
    treatment_pre_mean: float
    treatment_post_mean: float
    control_change: float
    treatment_change: float
    diff_in_diff: float
    diff_in_diff_percent: float
    is_significant: bool
    confidence: int
    p_value: float
    t_statistic: float
    degrees_of_freedom: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    control_pre_n: int
    control_pre_std: float
    control_post_n: int
    control_post_std: float
    treatment_pre_n: int
    treatment_pre_std: float
    treatment_post_n: int
    treatment_post_std: float
    recommendation: str


class MagnitudeEffect(FullOutcomeEffect):
    
    def sample_size(
        self,
        current_mean: float,
        current_std: float,
        lift_percent: float = 5,
        confidence: int = 95,
        power: int = 80,
        num_variants: int = 2,
    ) -> MagnitudeSampleSizePlan:
        lift_decimal = lift_percent / 100
        expected_mean = current_mean * (1 + lift_decimal)
        absolute_effect = abs(expected_mean - current_mean)
        
        if absolute_effect == 0:
            raise ValueError("lift_percent cannot be zero")
        if current_std <= 0:
            raise ValueError("current_std must be positive")
        if num_variants < 2:
            raise ValueError("num_variants must be at least 2")
        
        result = sample_size_two_means(
            effect_size=absolute_effect,
            std=current_std,
            confidence=confidence,
            power=power,
            num_groups=num_variants,
        )
        
        return MagnitudeSampleSizePlan(
            visitors_per_variant=result.n_per_group,
            total_visitors=result.n_total,
            current_mean=current_mean,
            expected_mean=expected_mean,
            standard_deviation=current_std,
            lift_percent=lift_percent,
            confidence=confidence,
            power=power,
        )
    
    def analyze(
        self,
        control_visitors: int,
        control_mean: float,
        control_std: float,
        variant_visitors: int,
        variant_mean: float,
        variant_std: float,
        confidence: int = 95,
    ) -> MagnitudeTestResults:
        if control_visitors <= 0 or variant_visitors <= 0:
            raise ValueError("visitors must be positive")
        if control_std < 0 or variant_std < 0:
            raise ValueError("standard deviation cannot be negative")
        
        lift_absolute, lift_percent = lift_calculations(control_mean, variant_mean)
        
        test_result = welch_t_test(
            control_mean, control_std, control_visitors,
            variant_mean, variant_std, variant_visitors,
            confidence,
        )
        
        se = mean_difference_se(control_std, control_visitors, variant_std, variant_visitors)
        df = welch_df(control_std**2, variant_std**2, control_visitors, variant_visitors)
        t_crit = t_critical(df, confidence)
        ci_lower = lift_absolute - t_crit * se
        ci_upper = lift_absolute + t_crit * se
        
        if test_result.is_significant:
            winner = "variant" if variant_mean > control_mean else "control"
        else:
            winner = "no winner yet"
        
        result = MagnitudeTestResults(
            control_mean=control_mean,
            variant_mean=variant_mean,
            lift_percent=lift_percent,
            lift_absolute=lift_absolute,
            is_significant=test_result.is_significant,
            confidence=confidence,
            p_value=test_result.p_value,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            control_visitors=control_visitors,
            control_std=control_std,
            variant_visitors=variant_visitors,
            variant_std=variant_std,
            winner=winner,
            recommendation="",
        )
        
        result.recommendation = self._generate_recommendation(result)
        
        return result
    
    def _generate_recommendation(self, result: MagnitudeTestResults, currency: str = "$") -> str:
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
    
    def _pairwise_welch_t_test(self, v1: MagnitudeVariant, v2: MagnitudeVariant, confidence: int, num_comparisons: int = 1) -> MagnitudePairwiseComparison:
        lift_absolute, lift_percent = lift_calculations(v1.mean, v2.mean)

        test_result = welch_t_test(
            v1.mean, v1.std, v1.visitors,
            v2.mean, v2.std, v2.visitors,
            confidence,
        )

        se = mean_difference_se(v1.std, v1.visitors, v2.std, v2.visitors)
        df = welch_df(v1.std**2, v2.std**2, v1.visitors, v2.visitors)
        # Adjust CI for multiple comparisons (Bonferroni)
        adjusted_confidence = 100 - (100 - confidence) / num_comparisons if num_comparisons > 1 else confidence
        t_crit = t_critical(df, round(adjusted_confidence))
        ci_lower = lift_absolute - t_crit * se
        ci_upper = lift_absolute + t_crit * se

        return MagnitudePairwiseComparison(
            variant_a=v1.name,
            variant_b=v2.name,
            mean_a=v1.mean,
            mean_b=v2.mean,
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
    ) -> MagnitudeMultiVariantResults:
        if len(variants) < 2:
            raise ValueError("At least 2 variants are required")
        
        names = [v["name"] for v in variants]
        if len(names) != len(set(names)):
            raise ValueError("Variant names must be unique")
        
        variant_objects = []
        for v in variants:
            if v["visitors"] <= 0:
                raise ValueError(f"visitors must be positive for variant '{v['name']}'")
            if v.get("std", 0) < 0:
                raise ValueError(f"std cannot be negative for variant '{v['name']}'")
            variant_objects.append(MagnitudeVariant(
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
        ms_within = ss_within / df_within if df_within > 0 else 0

        if ms_within > 0:
            f_stat = ms_between / ms_within
            p_value = 1 - f_dist.cdf(f_stat, df_between, df_within) if f_stat > 0 else 1.0
        elif ms_between > 0:
            # Perfect separation: all within-group variance is zero but groups differ
            f_stat = float('inf')
            p_value = 0.0
        else:
            f_stat = 0.0
            p_value = 1.0
        
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
                comparison = self._pairwise_welch_t_test(variant_objects[i], variant_objects[j], confidence, num_comparisons)
                
                if correction == "bonferroni":
                    comparison.p_value_adjusted = bonferroni_correction(comparison.p_value, num_comparisons)
                    comparison.is_significant = comparison.p_value_adjusted < alpha
                
                pairwise.append(comparison)
        
        recommendation = self._generate_multi_recommendation(
            variant_objects, is_significant, p_value, best_variant, pairwise, confidence
        )
        
        return MagnitudeMultiVariantResults(
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
        self,
        variants: List[MagnitudeVariant],
        is_significant: bool,
        p_value: float,
        best_variant: str,
        pairwise: List[MagnitudePairwiseComparison],
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
        self,
        visitors: int,
        mean: float,
        std: float,
        confidence: int = 95,
    ) -> MagnitudeConfidenceInterval:
        if visitors <= 1:
            raise ValueError("visitors must be greater than 1")
        if std < 0:
            raise ValueError("standard deviation cannot be negative")
        
        _, lower, upper, margin = calc_mean_ci(mean, std, visitors, confidence)
        
        return MagnitudeConfidenceInterval(
            mean=mean,
            lower=lower,
            upper=upper,
            confidence=confidence,
            margin_of_error=margin,
        )
    
    def summarize(
        self,
        result: MagnitudeTestResults,
        test_name: str = "Revenue Test",
        metric_name: str = "Average Order Value",
        currency: str = "$",
    ) -> str:
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
    
    def summarize_multi(
        self,
        result: MagnitudeMultiVariantResults,
        test_name: str = "Multi-Variant Test",
        metric_name: str = "Average Value",
        currency: str = "$",
    ) -> str:
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
    
    def summarize_plan(
        self,
        plan: MagnitudeSampleSizePlan,
        test_name: str = "Revenue Test",
        metric_name: str = "Average Order Value",
        currency: str = "$",
    ) -> str:
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
    
    def diff_in_diff(
        self,
        control_pre_n: int,
        control_pre_mean: float,
        control_pre_std: float,
        control_post_n: int,
        control_post_mean: float,
        control_post_std: float,
        treatment_pre_n: int,
        treatment_pre_mean: float,
        treatment_pre_std: float,
        treatment_post_n: int,
        treatment_post_mean: float,
        treatment_post_std: float,
        confidence: int = 95,
    ) -> MagnitudeDiffInDiffResults:
        if any(n <= 0 for n in [control_pre_n, control_post_n, treatment_pre_n, treatment_post_n]):
            raise ValueError("All sample sizes must be positive")
        if any(s < 0 for s in [control_pre_std, control_post_std, treatment_pre_std, treatment_post_std]):
            raise ValueError("Standard deviations cannot be negative")
        
        control_change = control_post_mean - control_pre_mean
        treatment_change = treatment_post_mean - treatment_pre_mean
        
        did = treatment_change - control_change
        
        did_percent = (did / treatment_pre_mean * 100) if treatment_pre_mean != 0 else 0
        
        var_c_pre = control_pre_std ** 2 / control_pre_n
        var_c_post = control_post_std ** 2 / control_post_n
        var_t_pre = treatment_pre_std ** 2 / treatment_pre_n
        var_t_post = treatment_post_std ** 2 / treatment_post_n
        
        se_did = math.sqrt(var_c_pre + var_c_post + var_t_pre + var_t_post)
        
        alpha = 1 - (confidence / 100)
        
        total_n = control_pre_n + control_post_n + treatment_pre_n + treatment_post_n
        df = max(1, total_n - 4)
        
        if se_did > 0 and df > 0:
            t_stat = did / se_did
            p_value = 2 * (1 - t.cdf(abs(t_stat), df))
        else:
            t_stat = 0
            p_value = 1.0
        
        t_crit = t.ppf(1 - alpha / 2, df) if df > 0 else norm.ppf(1 - alpha / 2)
        ci_lower = did - t_crit * se_did
        ci_upper = did + t_crit * se_did
        
        is_significant = p_value < alpha
        
        result = MagnitudeDiffInDiffResults(
            control_pre_mean=control_pre_mean,
            control_post_mean=control_post_mean,
            treatment_pre_mean=treatment_pre_mean,
            treatment_post_mean=treatment_post_mean,
            control_change=control_change,
            treatment_change=treatment_change,
            diff_in_diff=did,
            diff_in_diff_percent=did_percent,
            is_significant=is_significant,
            confidence=confidence,
            p_value=p_value,
            t_statistic=t_stat,
            degrees_of_freedom=df,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            control_pre_n=control_pre_n,
            control_pre_std=control_pre_std,
            control_post_n=control_post_n,
            control_post_std=control_post_std,
            treatment_pre_n=treatment_pre_n,
            treatment_pre_std=treatment_pre_std,
            treatment_post_n=treatment_post_n,
            treatment_post_std=treatment_post_std,
            recommendation="",
        )
        
        result.recommendation = self._generate_did_recommendation(result)
        
        return result
    
    def _generate_did_recommendation(self, result: MagnitudeDiffInDiffResults, currency: str = "$") -> str:
        direction = "positive" if result.diff_in_diff > 0 else "negative"
        
        if result.is_significant:
            return (
                f"**Significant treatment effect detected** (p-value: {result.p_value:.4f}).\n\n"
                f"_What this means:_ The treatment group showed a **{direction}** effect beyond what would be "
                f"expected from the control group's trend. The treatment changed the metric by "
                f"**{currency}{result.diff_in_diff:+,.2f}** ({result.diff_in_diff_percent:+.1f}% relative) more than the control. "
                f"With {result.confidence}% confidence, this effect is statistically real."
            )
        else:
            return (
                f"**No significant treatment effect detected** (p-value: {result.p_value:.4f}).\n\n"
                f"_What this means:_ The observed difference-in-differences of {currency}{result.diff_in_diff:+,.2f} "
                f"could be due to random chance. The treatment group's change was not significantly different "
                f"from the control group's change. Consider collecting more data or the effect may be too small to detect."
            )
    
    def summarize_diff_in_diff(
        self,
        result: MagnitudeDiffInDiffResults,
        test_name: str = "Difference-in-Differences Analysis",
        metric_name: str = "Average Value",
        currency: str = "$",
    ) -> str:
        lines = []
        lines.append(f"## 📊 {test_name}\n")
        
        if result.is_significant:
            lines.append(f"### ✅ Significant Treatment Effect\n")
            direction = "increase" if result.diff_in_diff > 0 else "decrease"
            lines.append(f"**The treatment caused a significant {direction} in {metric_name.lower()}.**\n")
        else:
            lines.append(f"### ⏳ No Significant Treatment Effect\n")
            lines.append(f"**The treatment effect is not statistically significant.**\n")
        
        lines.append(f"### {metric_name}\n")
        lines.append(f"| Group | Pre-Period | Post-Period | Change |")
        lines.append(f"|-------|------------|-------------|--------|")
        lines.append(f"| Control | {currency}{result.control_pre_mean:,.2f} | {currency}{result.control_post_mean:,.2f} | {currency}{result.control_change:+,.2f} |")
        lines.append(f"| Treatment | {currency}{result.treatment_pre_mean:,.2f} | {currency}{result.treatment_post_mean:,.2f} | {currency}{result.treatment_change:+,.2f} |")
        lines.append("")
        
        lines.append(f"### Difference-in-Differences Estimate\n")
        lines.append(f"- **DiD Effect:** {currency}{result.diff_in_diff:+,.2f} ({result.diff_in_diff_percent:+.1f}% relative)")
        lines.append(f"- **95% CI:** [{currency}{result.confidence_interval_lower:,.2f}, {currency}{result.confidence_interval_upper:,.2f}]")
        lines.append(f"- **T-statistic:** {result.t_statistic:.2f}")
        lines.append(f"- **Degrees of freedom:** {result.degrees_of_freedom:.0f}")
        lines.append(f"- **P-value:** {result.p_value:.4f}")
        lines.append(f"- **Confidence level:** {result.confidence}%\n")
        
        lines.append(f"### Sample Sizes\n")
        lines.append(f"| Group | Pre-Period | Post-Period |")
        lines.append(f"|-------|------------|-------------|")
        lines.append(f"| Control | {result.control_pre_n:,} | {result.control_post_n:,} |")
        lines.append(f"| Treatment | {result.treatment_pre_n:,} | {result.treatment_post_n:,} |")
        lines.append("")
        
        lines.append(f"### 📝 What This Means\n")
        if result.is_significant:
            lines.append(f"The treatment group's {metric_name.lower()} changed by **{currency}{result.treatment_change:+,.2f}** ")
            lines.append(f"while the control group changed by **{currency}{result.control_change:+,.2f}**. ")
            lines.append(f"After accounting for the control group's trend, the treatment effect is **{currency}{result.diff_in_diff:+,.2f}**. ")
            lines.append(f"This effect is statistically significant at the {result.confidence}% confidence level.")
        else:
            lines.append(f"The treatment group's {metric_name.lower()} changed by **{currency}{result.treatment_change:+,.2f}** ")
            lines.append(f"while the control group changed by **{currency}{result.control_change:+,.2f}**. ")
            lines.append(f"The difference ({currency}{result.diff_in_diff:+,.2f}) is not statistically significant. ")
            lines.append(f"This could mean the treatment had no real effect, or the sample size is insufficient to detect it.")
        
        return "\n".join(lines)


_default_instance = MagnitudeEffect()

sample_size = _default_instance.sample_size
analyze = _default_instance.analyze
analyze_multi = _default_instance.analyze_multi
confidence_interval = _default_instance.confidence_interval
summarize = _default_instance.summarize
summarize_multi = _default_instance.summarize_multi
summarize_plan = _default_instance.summarize_plan
diff_in_diff = _default_instance.diff_in_diff
summarize_diff_in_diff = _default_instance.summarize_diff_in_diff

SampleSizePlan = MagnitudeSampleSizePlan
TestResults = MagnitudeTestResults
ConfidenceInterval = MagnitudeConfidenceInterval
Variant = MagnitudeVariant
PairwiseComparison = MagnitudePairwiseComparison
MultiVariantResults = MagnitudeMultiVariantResults
DiffInDiffResults = MagnitudeDiffInDiffResults

__all__ = [
    "MagnitudeEffect",
    "MagnitudeSampleSizePlan",
    "MagnitudeTestResults",
    "MagnitudeConfidenceInterval",
    "MagnitudeVariant",
    "MagnitudePairwiseComparison",
    "MagnitudeMultiVariantResults",
    "MagnitudeDiffInDiffResults",
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
