import math
from dataclasses import dataclass
from typing import Tuple, Optional
from scipy.stats import norm, t, chi2


@dataclass
class SampleSizeResult:
    n_per_group: int
    n_total: int
    alpha: float
    power: float
    effect_size: float


@dataclass  
class PowerResult:
    power: float
    alpha: float
    n_per_group: int
    effect_size: float


@dataclass
class TestStatisticResult:
    statistic: float
    p_value: float
    degrees_of_freedom: Optional[float]
    is_significant: bool


def z_alpha(confidence: int = 95, two_sided: bool = True) -> float:
    alpha = 1 - confidence / 100
    if two_sided:
        return norm.ppf(1 - alpha / 2)
    return norm.ppf(1 - alpha)


def z_beta(power: int = 80) -> float:
    beta = 1 - power / 100
    return norm.ppf(1 - beta)


def t_critical(df: float, confidence: int = 95, two_sided: bool = True) -> float:
    alpha = 1 - confidence / 100
    if two_sided:
        return t.ppf(1 - alpha / 2, df)
    return t.ppf(1 - alpha, df)


def welch_df(var1: float, var2: float, n1: int, n2: int) -> float:
    if n1 <= 1 or n2 <= 1:
        return max(1.0, float(n1 + n2 - 2))
    se1_sq = var1 / n1
    se2_sq = var2 / n2
    numerator = (se1_sq + se2_sq) ** 2
    denominator = (se1_sq ** 2) / (n1 - 1) + (se2_sq ** 2) / (n2 - 1)
    if denominator == 0:
        return float('inf')
    return numerator / denominator


def sample_size_two_proportions(
    p1: float,
    p2: float,
    confidence: int = 95,
    power: int = 80,
    num_groups: int = 2,
) -> SampleSizeResult:
    if abs(p2 - p1) < 1e-12:
        raise ValueError("p1 and p2 must be different to calculate sample size")

    alpha = 1 - confidence / 100
    if num_groups > 2:
        num_comparisons = num_groups * (num_groups - 1) // 2
        alpha = alpha / num_comparisons

    beta = 1 - power / 100

    za = norm.ppf(1 - alpha / 2)
    zb = norm.ppf(1 - beta)

    p_pooled = (p1 + p2) / 2

    numerator = (
        za * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
        zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2

    n = math.ceil(numerator / denominator)

    effect_size = abs(p2 - p1) / math.sqrt(p_pooled * (1 - p_pooled))

    return SampleSizeResult(
        n_per_group=n,
        n_total=n * num_groups,
        alpha=alpha,
        power=power / 100,
        effect_size=effect_size,
    )


def sample_size_two_means(
    effect_size: float,
    std: float,
    confidence: int = 95,
    power: int = 80,
    num_groups: int = 2,
) -> SampleSizeResult:
    if abs(effect_size) < 1e-12:
        raise ValueError("effect_size must be non-zero to calculate sample size")

    alpha = 1 - confidence / 100
    if num_groups > 2:
        num_comparisons = num_groups * (num_groups - 1) // 2
        alpha = alpha / num_comparisons
    
    beta = 1 - power / 100
    
    za = norm.ppf(1 - alpha / 2)
    zb = norm.ppf(1 - beta)
    
    n = math.ceil(2 * ((za + zb) * std / effect_size) ** 2)
    
    cohens_d = effect_size / std
    
    return SampleSizeResult(
        n_per_group=n,
        n_total=n * num_groups,
        alpha=alpha,
        power=power / 100,
        effect_size=cohens_d,
    )


def sample_size_survival(
    hr: float,
    confidence: int = 95,
    power: int = 80,
    allocation_ratio: float = 1.0,
) -> SampleSizeResult:
    alpha = 1 - confidence / 100
    beta = 1 - power / 100
    
    za = norm.ppf(1 - alpha / 2)
    zb = norm.ppf(1 - beta)
    
    log_hr = math.log(hr)
    if abs(log_hr) < 0.001:
        raise ValueError("Hazard ratio too close to 1")
    
    k = allocation_ratio
    events_needed = ((za + zb) ** 2 * (1 + k) ** 2) / (k * log_hr ** 2)
    events_needed = int(math.ceil(events_needed))
    
    return SampleSizeResult(
        n_per_group=int(math.ceil(events_needed / 2)),
        n_total=events_needed,
        alpha=alpha,
        power=power / 100,
        effect_size=log_hr,
    )


def z_test_two_proportions(
    p1: float,
    n1: int,
    p2: float,
    n2: int,
    confidence: int = 95,
) -> TestStatisticResult:
    alpha = 1 - confidence / 100
    
    p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se_pooled > 0:
        z_stat = (p2 - p1) / se_pooled
        p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    else:
        z_stat = 0
        p_value = 1.0
    
    return TestStatisticResult(
        statistic=z_stat,
        p_value=p_value,
        degrees_of_freedom=None,
        is_significant=p_value < alpha,
    )


def welch_t_test(
    mean1: float,
    std1: float,
    n1: int,
    mean2: float,
    std2: float,
    n2: int,
    confidence: int = 95,
) -> TestStatisticResult:
    alpha = 1 - confidence / 100
    
    var1 = std1 ** 2
    var2 = std2 ** 2
    
    se = math.sqrt(var1 / n1 + var2 / n2)
    
    if se > 0:
        t_stat = (mean2 - mean1) / se
        df = welch_df(var1, var2, n1, n2)
        p_value = 2 * (1 - t.cdf(abs(t_stat), df))
    else:
        t_stat = 0
        df = n1 + n2 - 2
        p_value = 1.0
    
    return TestStatisticResult(
        statistic=t_stat,
        p_value=p_value,
        degrees_of_freedom=df,
        is_significant=p_value < alpha,
    )


def proportion_ci(
    successes: int,
    n: int,
    confidence: int = 95,
    method: str = "wilson",
) -> Tuple[float, float, float, float]:
    rate = successes / n
    alpha = 1 - confidence / 100
    z = norm.ppf(1 - alpha / 2)
    
    if method == "wilson":
        denominator = 1 + z**2 / n
        center = (rate + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt((rate * (1 - rate) + z**2 / (4 * n)) / n) / denominator
        lower = max(0, center - margin)
        upper = min(1, center + margin)
    else:
        se = math.sqrt(rate * (1 - rate) / n)
        margin = z * se
        lower = max(0, rate - margin)
        upper = min(1, rate + margin)
    
    return rate, lower, upper, margin


def mean_ci(
    mean: float,
    std: float,
    n: int,
    confidence: int = 95,
) -> Tuple[float, float, float, float]:
    alpha = 1 - confidence / 100
    se = std / math.sqrt(n)
    t_crit = t.ppf(1 - alpha / 2, n - 1)
    margin = t_crit * se
    
    return mean, mean - margin, mean + margin, margin


def difference_ci(
    diff: float,
    se: float,
    df: float,
    confidence: int = 95,
) -> Tuple[float, float, float]:
    alpha = 1 - confidence / 100
    t_crit = t.ppf(1 - alpha / 2, df) if df > 0 else norm.ppf(1 - alpha / 2)
    margin = t_crit * se
    
    return diff - margin, diff + margin, margin


def proportion_difference_se(p1: float, n1: int, p2: float, n2: int) -> float:
    return math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)


def mean_difference_se(std1: float, n1: int, std2: float, n2: int) -> float:
    return math.sqrt(std1**2 / n1 + std2**2 / n2)


def lift_calculations(baseline: float, variant: float) -> Tuple[float, float]:
    absolute = variant - baseline
    relative = (absolute / baseline * 100) if baseline != 0 else 0
    return absolute, relative


def bonferroni_correction(p_value: float, num_comparisons: int) -> float:
    return min(1.0, p_value * num_comparisons)


def log_rank_statistic(
    observed: float,
    expected: float,
    variance: float,
) -> Tuple[float, float]:
    if variance <= 0:
        return 0.0, 1.0
    
    chi2_stat = (observed - expected) ** 2 / variance
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    
    return chi2_stat, p_value


def hazard_ratio_from_events(
    ctrl_events: int,
    ctrl_time: float,
    trt_events: int,
    trt_time: float,
    confidence: int = 95,
) -> Tuple[float, float, float]:
    if ctrl_events == 0 and trt_events == 0:
        return 1.0, 0.0, float('inf')
    if ctrl_events == 0:
        return float('inf'), 0.0, float('inf')
    if trt_events == 0:
        return 0.0, 0.0, float('inf')

    ctrl_rate = ctrl_events / ctrl_time if ctrl_time > 0 else 0
    trt_rate = trt_events / trt_time if trt_time > 0 else 0

    hr = trt_rate / ctrl_rate if ctrl_rate > 0 else float('inf')
    
    se_log_hr = math.sqrt(1/ctrl_events + 1/trt_events)
    log_hr = math.log(hr) if hr > 0 else 0
    
    alpha = 1 - confidence / 100
    z = norm.ppf(1 - alpha / 2)
    ci_lower = math.exp(log_hr - z * se_log_hr)
    ci_upper = math.exp(log_hr + z * se_log_hr)
    
    return hr, ci_lower, ci_upper


def rate_ratio(
    ctrl_events: int,
    ctrl_exposure: float,
    trt_events: int,
    trt_exposure: float,
    confidence: int = 95,
) -> Tuple[float, float, float, float]:
    if ctrl_exposure <= 0 or trt_exposure <= 0:
        raise ValueError("Exposure must be positive")
    
    ctrl_rate = ctrl_events / ctrl_exposure
    trt_rate = trt_events / trt_exposure
    
    if ctrl_rate == 0:
        rr = float('inf') if trt_rate > 0 else 1.0
        return rr, 0.0, float('inf'), 1.0
    
    rr = trt_rate / ctrl_rate
    
    if ctrl_events > 0 and trt_events > 0:
        se_log_rr = math.sqrt(1/ctrl_events + 1/trt_events)
        log_rr = math.log(rr)
        z = norm.ppf(1 - (1 - confidence/100) / 2)
        rr_lower = math.exp(log_rr - z * se_log_rr)
        rr_upper = math.exp(log_rr + z * se_log_rr)
    else:
        rr_lower, rr_upper = 0.0, float('inf')
    
    expected_ctrl = (ctrl_events + trt_events) * ctrl_exposure / (ctrl_exposure + trt_exposure)
    expected_trt = (ctrl_events + trt_events) * trt_exposure / (ctrl_exposure + trt_exposure)
    
    if expected_ctrl > 0 and expected_trt > 0:
        chi2_stat = ((ctrl_events - expected_ctrl) ** 2 / expected_ctrl + 
                     (trt_events - expected_trt) ** 2 / expected_trt)
        p_value = 1 - chi2.cdf(chi2_stat, df=1)
    else:
        p_value = 1.0
    
    return rr, rr_lower, rr_upper, p_value
