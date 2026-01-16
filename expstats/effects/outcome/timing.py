from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from scipy import stats

from expstats.utils.stats import (
    sample_size_survival,
    hazard_ratio_from_events,
)


@dataclass
class SurvivalCurve:
    times: List[float]
    survival_probabilities: List[float]
    confidence_lower: List[float]
    confidence_upper: List[float]
    median_time: Optional[float]
    events: int
    censored: int
    total: int


@dataclass
class TimingResults:
    control_median_time: Optional[float]
    treatment_median_time: Optional[float]
    control_events: int
    control_censored: int
    treatment_events: int
    treatment_censored: int
    hazard_ratio: float
    hazard_ratio_ci_lower: float
    hazard_ratio_ci_upper: float
    time_saved: Optional[float]
    time_saved_percent: Optional[float]
    is_significant: bool
    confidence: int
    p_value: float
    recommendation: str


@dataclass
class TimingSampleSizePlan:
    subjects_per_group: int
    total_subjects: int
    expected_events_per_group: int
    total_expected_events: int
    control_median: float
    treatment_median: float
    hazard_ratio: float
    confidence: int
    power: int
    study_duration: Optional[float]
    accrual_duration: Optional[float]


@dataclass
class RateResults:
    control_rate: float
    treatment_rate: float
    control_events: int
    control_exposure: float
    treatment_events: int
    treatment_exposure: float
    rate_ratio: float
    rate_ratio_ci_lower: float
    rate_ratio_ci_upper: float
    rate_difference: float
    rate_difference_percent: float
    is_significant: bool
    confidence: int
    p_value: float
    recommendation: str


def _kaplan_meier(times: np.ndarray, events: np.ndarray, confidence: int = 95) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    sorted_indices = np.argsort(times)
    times = times[sorted_indices]
    events = events[sorted_indices]
    
    unique_times = np.unique(times[events == 1])
    if len(unique_times) == 0:
        return np.array([0]), np.array([1.0]), np.array([1.0]), np.array([1.0])
    
    survival = []
    variance = []
    km_times = [0]
    
    n_at_risk = len(times)
    cum_survival = 1.0
    cum_variance = 0.0
    
    for t in unique_times:
        d = np.sum((times == t) & (events == 1))
        c = np.sum((times == t) & (events == 0))
        
        if n_at_risk > 0:
            hazard = d / n_at_risk
            cum_survival *= (1 - hazard)
            if n_at_risk > d and n_at_risk > 0:
                cum_variance += d / (n_at_risk * (n_at_risk - d)) if (n_at_risk - d) > 0 else 0
        
        survival.append(cum_survival)
        variance.append(cum_variance)
        km_times.append(t)
        
        n_at_risk -= (d + c)
    
    survival = np.array([1.0] + survival)
    variance = np.array([0.0] + variance)
    km_times = np.array(km_times)
    
    se = np.sqrt(variance) * survival
    alpha = 1 - confidence / 100
    z = stats.norm.ppf(1 - alpha / 2)
    ci_lower = np.maximum(0, survival - z * se)
    ci_upper = np.minimum(1, survival + z * se)
    
    return km_times, survival, ci_lower, ci_upper


def _find_median(times: np.ndarray, survival: np.ndarray) -> Optional[float]:
    below_50 = np.where(survival <= 0.5)[0]
    if len(below_50) == 0:
        return None
    return float(times[below_50[0]])


def _log_rank_test(
    control_times: np.ndarray,
    control_events: np.ndarray,
    treatment_times: np.ndarray,
    treatment_events: np.ndarray,
) -> Tuple[float, float]:
    all_times = np.concatenate([control_times, treatment_times])
    all_events = np.concatenate([control_events, treatment_events])
    group = np.concatenate([np.zeros(len(control_times)), np.ones(len(treatment_times))])
    
    sorted_indices = np.argsort(all_times)
    all_times = all_times[sorted_indices]
    all_events = all_events[sorted_indices]
    group = group[sorted_indices]
    
    unique_event_times = np.unique(all_times[all_events == 1])
    
    if len(unique_event_times) == 0:
        return 0.0, 1.0
    
    O1 = 0  
    E1 = 0  
    V = 0   
    
    for t in unique_event_times:
        at_risk_ctrl = np.sum((control_times >= t))
        at_risk_trt = np.sum((treatment_times >= t))
        n = at_risk_ctrl + at_risk_trt
        
        if n == 0:
            continue
        
        events_ctrl = np.sum((control_times == t) & (control_events == 1))
        events_trt = np.sum((treatment_times == t) & (treatment_events == 1))
        d = events_ctrl + events_trt
        
        O1 += events_trt
        E1 += (at_risk_trt / n) * d if n > 0 else 0
        
        if n > 1:
            V += (at_risk_ctrl * at_risk_trt * d * (n - d)) / (n * n * (n - 1))
    
    if V <= 0:
        return 0.0, 1.0
    
    chi2 = (O1 - E1) ** 2 / V
    p_value = 1 - stats.chi2.cdf(chi2, df=1)
    
    return float(chi2), float(p_value)


def _estimate_hazard_ratio(
    control_times: np.ndarray,
    control_events: np.ndarray,
    treatment_times: np.ndarray,
    treatment_events: np.ndarray,
    confidence: int = 95,
) -> Tuple[float, float, float]:
    ctrl_events_total = int(np.sum(control_events))
    trt_events_total = int(np.sum(treatment_events))
    ctrl_total_time = float(np.sum(control_times))
    trt_total_time = float(np.sum(treatment_times))
    
    return hazard_ratio_from_events(
        ctrl_events=ctrl_events_total,
        ctrl_time=ctrl_total_time,
        trt_events=trt_events_total,
        trt_time=trt_total_time,
        confidence=confidence,
    )


def _generate_timing_recommendation(
    is_significant: bool,
    p_value: float,
    hazard_ratio: float,
    time_saved: Optional[float],
    time_saved_percent: Optional[float],
    confidence: int,
) -> str:
    if is_significant:
        if hazard_ratio < 1:
            direction = "slower"
            effect = "reduced the rate of the event"
            interpretation = "Users in the treatment group take longer to experience the event."
        else:
            direction = "faster"
            effect = "accelerated the event"
            interpretation = "Users in the treatment group experience the event sooner."
        
        time_info = ""
        if time_saved is not None and time_saved_percent is not None:
            if time_saved > 0:
                time_info = f"\n- **Time acceleration:** {abs(time_saved):.1f} units faster ({abs(time_saved_percent):.1f}% reduction)"
            else:
                time_info = f"\n- **Time delay:** {abs(time_saved):.1f} units slower ({abs(time_saved_percent):.1f}% increase)"
        
        return f"""## ⏱️ Timing Effect Analysis

### ✅ Significant Result

**The treatment {effect} significantly.**

- **Hazard ratio:** {hazard_ratio:.3f}
- **Interpretation:** Events occur {direction} in the treatment group{time_info}
- **P-value:** {p_value:.4f}

### 📝 What This Means

With {confidence}% confidence, the treatment significantly affects when the event occurs.
{interpretation}

A hazard ratio of {hazard_ratio:.3f} means:
- HR < 1: Treatment slows down the event (protective effect)
- HR > 1: Treatment speeds up the event
- HR = 1: No effect on timing
"""
    else:
        return f"""## ⏱️ Timing Effect Analysis

### ⚠️ No Significant Difference Detected

**The treatment does not significantly affect event timing** (p-value: {p_value:.4f}).

- **Hazard ratio:** {hazard_ratio:.3f}
- **P-value:** {p_value:.4f} (above {1 - confidence/100:.2f} threshold)

### 📝 What This Means

The observed difference in timing could be due to random chance.
Consider:
- Running the study longer to observe more events
- Increasing sample size
- The treatment may genuinely have no effect on timing
"""


def survival_curve(
    times: List[float],
    events: List[int],
    confidence: int = 95,
) -> SurvivalCurve:
    times_arr = np.array(times, dtype=float)
    events_arr = np.array(events, dtype=int)
    
    if len(times_arr) != len(events_arr):
        raise ValueError("times and events must have the same length")
    if len(times_arr) == 0:
        raise ValueError("times cannot be empty")
    if not np.all((events_arr == 0) | (events_arr == 1)):
        raise ValueError("events must contain only 0 (censored) or 1 (event occurred)")
    
    km_times, survival, ci_lower, ci_upper = _kaplan_meier(times_arr, events_arr, confidence)
    median = _find_median(km_times, survival)
    
    return SurvivalCurve(
        times=km_times.tolist(),
        survival_probabilities=survival.tolist(),
        confidence_lower=ci_lower.tolist(),
        confidence_upper=ci_upper.tolist(),
        median_time=median,
        events=int(np.sum(events_arr)),
        censored=int(np.sum(events_arr == 0)),
        total=len(times_arr),
    )


def analyze(
    control_times: List[float],
    control_events: List[int],
    treatment_times: List[float],
    treatment_events: List[int],
    confidence: int = 95,
) -> TimingResults:
    ctrl_times = np.array(control_times, dtype=float)
    ctrl_events = np.array(control_events, dtype=int)
    trt_times = np.array(treatment_times, dtype=float)
    trt_events = np.array(treatment_events, dtype=int)
    
    if len(ctrl_times) != len(ctrl_events):
        raise ValueError("control_times and control_events must have the same length")
    if len(trt_times) != len(trt_events):
        raise ValueError("treatment_times and treatment_events must have the same length")
    if len(ctrl_times) == 0 or len(trt_times) == 0:
        raise ValueError("Both groups must have at least one observation")
    
    ctrl_km_times, ctrl_surv, _, _ = _kaplan_meier(ctrl_times, ctrl_events, confidence)
    trt_km_times, trt_surv, _, _ = _kaplan_meier(trt_times, trt_events, confidence)
    
    ctrl_median = _find_median(ctrl_km_times, ctrl_surv)
    trt_median = _find_median(trt_km_times, trt_surv)
    
    _, p_value = _log_rank_test(ctrl_times, ctrl_events, trt_times, trt_events)
    
    hr, hr_lower, hr_upper = _estimate_hazard_ratio(ctrl_times, ctrl_events, trt_times, trt_events, confidence)
    
    alpha = 1 - confidence / 100
    is_significant = p_value < alpha
    
    time_saved = None
    time_saved_percent = None
    if ctrl_median is not None and trt_median is not None:
        time_saved = ctrl_median - trt_median
        time_saved_percent = (time_saved / ctrl_median) * 100 if ctrl_median > 0 else None
    
    recommendation = _generate_timing_recommendation(
        is_significant=is_significant,
        p_value=p_value,
        hazard_ratio=hr,
        time_saved=time_saved,
        time_saved_percent=time_saved_percent,
        confidence=confidence,
    )
    
    return TimingResults(
        control_median_time=ctrl_median,
        treatment_median_time=trt_median,
        control_events=int(np.sum(ctrl_events)),
        control_censored=int(np.sum(ctrl_events == 0)),
        treatment_events=int(np.sum(trt_events)),
        treatment_censored=int(np.sum(trt_events == 0)),
        hazard_ratio=hr,
        hazard_ratio_ci_lower=hr_lower,
        hazard_ratio_ci_upper=hr_upper,
        time_saved=time_saved,
        time_saved_percent=time_saved_percent,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        recommendation=recommendation,
    )


def sample_size(
    control_median: float,
    treatment_median: float,
    confidence: int = 95,
    power: int = 80,
    dropout_rate: float = 0.1,
    allocation_ratio: float = 1.0,
) -> TimingSampleSizePlan:
    if control_median <= 0:
        raise ValueError("control_median must be positive")
    if treatment_median <= 0:
        raise ValueError("treatment_median must be positive")
    if not 0 <= dropout_rate < 1:
        raise ValueError("dropout_rate must be between 0 and 1")
    
    hr = control_median / treatment_median
    
    log_hr = np.log(hr)
    if abs(log_hr) < 0.001:
        raise ValueError("Medians are too similar to detect a difference")
    
    result = sample_size_survival(
        hr=hr,
        confidence=confidence,
        power=power,
        allocation_ratio=allocation_ratio,
    )
    
    event_probability = 1 - dropout_rate
    subjects_per_group = int(np.ceil(result.n_total / (2 * event_probability)))
    
    return TimingSampleSizePlan(
        subjects_per_group=subjects_per_group,
        total_subjects=subjects_per_group * 2,
        expected_events_per_group=int(np.ceil(result.n_total / 2)),
        total_expected_events=result.n_total,
        control_median=control_median,
        treatment_median=treatment_median,
        hazard_ratio=hr,
        confidence=confidence,
        power=power,
        study_duration=None,
        accrual_duration=None,
    )


def analyze_rates(
    control_events: int,
    control_exposure: float,
    treatment_events: int,
    treatment_exposure: float,
    confidence: int = 95,
) -> RateResults:
    if control_events < 0 or treatment_events < 0:
        raise ValueError("Event counts must be non-negative")
    if control_exposure <= 0 or treatment_exposure <= 0:
        raise ValueError("Exposure must be positive")
    
    ctrl_rate = control_events / control_exposure
    trt_rate = treatment_events / treatment_exposure
    
    if ctrl_rate == 0:
        rate_ratio = float('inf') if trt_rate > 0 else 1.0
        rr_lower, rr_upper = 0.0, float('inf')
    else:
        rate_ratio = trt_rate / ctrl_rate
        
        if control_events > 0 and treatment_events > 0:
            se_log_rr = np.sqrt(1/control_events + 1/treatment_events)
            log_rr = np.log(rate_ratio)
            z = stats.norm.ppf(1 - (1 - confidence/100) / 2)
            rr_lower = np.exp(log_rr - z * se_log_rr)
            rr_upper = np.exp(log_rr + z * se_log_rr)
        else:
            rr_lower, rr_upper = 0.0, float('inf')
    
    rate_diff = trt_rate - ctrl_rate
    rate_diff_percent = (rate_diff / ctrl_rate * 100) if ctrl_rate > 0 else 0
    
    expected_ctrl = (control_events + treatment_events) * control_exposure / (control_exposure + treatment_exposure)
    expected_trt = (control_events + treatment_events) * treatment_exposure / (control_exposure + treatment_exposure)
    
    if expected_ctrl > 0 and expected_trt > 0:
        chi2 = ((control_events - expected_ctrl) ** 2 / expected_ctrl + 
                (treatment_events - expected_trt) ** 2 / expected_trt)
        p_value = 1 - stats.chi2.cdf(chi2, df=1)
    else:
        p_value = 1.0
    
    alpha = 1 - confidence / 100
    is_significant = p_value < alpha
    
    recommendation = _generate_rate_recommendation(
        is_significant=is_significant,
        p_value=p_value,
        rate_ratio=rate_ratio,
        ctrl_rate=ctrl_rate,
        trt_rate=trt_rate,
        rate_diff_percent=rate_diff_percent,
        confidence=confidence,
    )
    
    return RateResults(
        control_rate=ctrl_rate,
        treatment_rate=trt_rate,
        control_events=control_events,
        control_exposure=control_exposure,
        treatment_events=treatment_events,
        treatment_exposure=treatment_exposure,
        rate_ratio=rate_ratio,
        rate_ratio_ci_lower=rr_lower,
        rate_ratio_ci_upper=rr_upper,
        rate_difference=rate_diff,
        rate_difference_percent=rate_diff_percent,
        is_significant=is_significant,
        confidence=confidence,
        p_value=p_value,
        recommendation=recommendation,
    )


def _generate_rate_recommendation(
    is_significant: bool,
    p_value: float,
    rate_ratio: float,
    ctrl_rate: float,
    trt_rate: float,
    rate_diff_percent: float,
    confidence: int,
) -> str:
    if is_significant:
        if rate_ratio > 1:
            direction = "higher"
            change = "increased"
        else:
            direction = "lower"
            change = "decreased"
        
        return f"""## 📊 Event Rate Analysis

### ✅ Significant Difference

**The treatment group has a significantly {direction} event rate.**

- **Control rate:** {ctrl_rate:.4f} events per unit time
- **Treatment rate:** {trt_rate:.4f} events per unit time
- **Rate ratio:** {rate_ratio:.3f} ({rate_diff_percent:+.1f}% change)
- **P-value:** {p_value:.4f}

### 📝 What This Means

With {confidence}% confidence, the treatment {change} the event rate by {abs(rate_diff_percent):.1f}%.

A rate ratio of {rate_ratio:.3f} means:
- RR > 1: Treatment increases event rate
- RR < 1: Treatment decreases event rate
- RR = 1: No effect
"""
    else:
        return f"""## 📊 Event Rate Analysis

### ⚠️ No Significant Difference

**The event rates are not significantly different** (p-value: {p_value:.4f}).

- **Control rate:** {ctrl_rate:.4f} events per unit time
- **Treatment rate:** {trt_rate:.4f} events per unit time
- **Rate ratio:** {rate_ratio:.3f}

### 📝 What This Means

The observed difference could be due to random chance.
Consider collecting more data or extending the observation period.
"""


def summarize(result: TimingResults, test_name: str = "Timing Effect Test") -> str:
    lines = [f"## ⏱️ {test_name} Results", ""]
    
    if result.is_significant:
        lines.append("### ✅ Significant Timing Effect Detected")
        lines.append("")
        
        if result.hazard_ratio < 1:
            lines.append("**The treatment slows down when the event occurs.**")
        else:
            lines.append("**The treatment speeds up when the event occurs.**")
    else:
        lines.append("### ⚠️ No Significant Timing Effect")
        lines.append("")
        lines.append("**The treatment does not significantly affect event timing.**")
    
    lines.append("")
    lines.append("### 📈 Key Metrics")
    lines.append("")
    
    ctrl_median_str = f"{result.control_median_time:.1f}" if result.control_median_time else "Not reached"
    trt_median_str = f"{result.treatment_median_time:.1f}" if result.treatment_median_time else "Not reached"
    
    lines.append(f"| Metric | Control | Treatment |")
    lines.append(f"|--------|---------|-----------|")
    lines.append(f"| Median time | {ctrl_median_str} | {trt_median_str} |")
    lines.append(f"| Events | {result.control_events} | {result.treatment_events} |")
    lines.append(f"| Censored | {result.control_censored} | {result.treatment_censored} |")
    lines.append("")
    
    lines.append(f"- **Hazard ratio:** {result.hazard_ratio:.3f} (95% CI: {result.hazard_ratio_ci_lower:.3f} - {result.hazard_ratio_ci_upper:.3f})")
    lines.append(f"- **P-value:** {result.p_value:.4f}")
    
    if result.time_saved is not None:
        if result.time_saved > 0:
            lines.append(f"- **Time saved:** {result.time_saved:.1f} units ({result.time_saved_percent:.1f}% faster)")
        else:
            lines.append(f"- **Time added:** {abs(result.time_saved):.1f} units ({abs(result.time_saved_percent):.1f}% slower)")
    
    lines.append("")
    lines.append("### 📝 Interpretation")
    lines.append("")
    
    if result.p_value < 0.01:
        lines.append("**Very strong evidence** of a timing effect (p < 0.01).")
    elif result.p_value < 0.05:
        lines.append("**Strong evidence** of a timing effect (p < 0.05).")
    elif result.p_value < 0.10:
        lines.append("**Weak evidence** of a timing effect (0.05 < p < 0.10).")
    else:
        lines.append("**Insufficient evidence** to conclude there is a timing effect (p > 0.10).")
    
    return "\n".join(lines)


def summarize_rates(result: RateResults, test_name: str = "Event Rate Test", unit: str = "events per day") -> str:
    lines = [f"## 📊 {test_name} Results", ""]
    
    if result.is_significant:
        lines.append("### ✅ Significant Rate Difference Detected")
        lines.append("")
        
        if result.rate_ratio > 1:
            lines.append("**The treatment increases the event rate.**")
        else:
            lines.append("**The treatment decreases the event rate.**")
    else:
        lines.append("### ⚠️ No Significant Rate Difference")
        lines.append("")
        lines.append("**The event rates are not significantly different.**")
    
    lines.append("")
    lines.append("### 📈 Key Metrics")
    lines.append("")
    lines.append(f"| Group | Events | Exposure | Rate ({unit}) |")
    lines.append(f"|-------|--------|----------|------|")
    lines.append(f"| Control | {result.control_events} | {result.control_exposure:.1f} | {result.control_rate:.4f} |")
    lines.append(f"| Treatment | {result.treatment_events} | {result.treatment_exposure:.1f} | {result.treatment_rate:.4f} |")
    lines.append("")
    
    lines.append(f"- **Rate ratio:** {result.rate_ratio:.3f} (95% CI: {result.rate_ratio_ci_lower:.3f} - {result.rate_ratio_ci_upper:.3f})")
    lines.append(f"- **Rate change:** {result.rate_difference_percent:+.1f}%")
    lines.append(f"- **P-value:** {result.p_value:.4f}")
    
    return "\n".join(lines)


class TimingEffect:
    
    def analyze(
        self,
        control_times: List[float],
        control_events: List[int],
        treatment_times: List[float],
        treatment_events: List[int],
        confidence: int = 95,
    ) -> TimingResults:
        return analyze(control_times, control_events, treatment_times, treatment_events, confidence)
    
    def sample_size(
        self,
        control_median: float,
        treatment_median: float,
        confidence: int = 95,
        power: int = 80,
        dropout_rate: float = 0.1,
        allocation_ratio: float = 1.0,
    ) -> TimingSampleSizePlan:
        return sample_size(control_median, treatment_median, confidence, power, dropout_rate, allocation_ratio)
    
    def survival_curve(
        self,
        times: List[float],
        events: List[int],
        confidence: int = 95,
    ) -> SurvivalCurve:
        return survival_curve(times, events, confidence)
    
    def analyze_rates(
        self,
        control_events: int,
        control_exposure: float,
        treatment_events: int,
        treatment_exposure: float,
        confidence: int = 95,
    ) -> RateResults:
        return analyze_rates(control_events, control_exposure, treatment_events, treatment_exposure, confidence)
    
    def summarize(self, result: TimingResults, test_name: str = "Timing Effect Test") -> str:
        return summarize(result, test_name)
    
    def summarize_rates(self, result: RateResults, test_name: str = "Event Rate Test", unit: str = "events per day") -> str:
        return summarize_rates(result, test_name, unit)


__all__ = [
    "TimingEffect",
    "TimingResults",
    "TimingSampleSizePlan",
    "SurvivalCurve",
    "RateResults",
    "analyze",
    "sample_size",
    "survival_curve",
    "analyze_rates",
    "summarize",
    "summarize_rates",
]
