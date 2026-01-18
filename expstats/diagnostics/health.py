"""
Test Health Dashboard.

Provides a comprehensive health check for A/B tests, including:
- Sample ratio validation
- Minimum sample size check
- Test duration recommendations
- Statistical power assessment
- Peeking warnings
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from scipy.stats import norm

from expstats.diagnostics.srm import check_sample_ratio


@dataclass
class HealthCheckItem:
    """Individual health check result."""
    name: str
    status: Literal["pass", "warning", "fail"]
    message: str
    details: Optional[str] = None


@dataclass
class TestHealthReport:
    """Comprehensive test health report."""

    # Overall status
    overall_status: Literal["healthy", "warning", "unhealthy"]
    score: int  # 0-100

    # Individual checks
    checks: List[HealthCheckItem]

    # Summary metrics
    control_visitors: int
    variant_visitors: int
    total_visitors: int
    test_duration_days: Optional[int]

    # Recommendations
    can_trust_results: bool
    primary_issues: List[str]
    recommendation: str

    # Detailed report
    summary: str


def check_health(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    expected_visitors_per_variant: Optional[int] = None,
    test_start_date: Optional[str] = None,
    daily_traffic: Optional[int] = None,
    expected_ratio: float = 0.5,
    minimum_sample_per_variant: int = 100,
    minimum_days: int = 7,
    num_peeks: int = 1,
    baseline_rate: Optional[float] = None,
    minimum_detectable_effect: float = 0.10,
) -> TestHealthReport:
    """
    Perform comprehensive health check on an A/B test.

    Args:
        control_visitors: Number of visitors in control
        control_conversions: Number of conversions in control
        variant_visitors: Number of visitors in variant
        variant_conversions: Number of conversions in variant
        expected_visitors_per_variant: Planned sample size per variant
        test_start_date: Start date as string (YYYY-MM-DD)
        daily_traffic: Expected daily traffic (total)
        expected_ratio: Expected traffic split ratio
        minimum_sample_per_variant: Minimum visitors needed per variant
        minimum_days: Minimum days to run (for weekly patterns)
        num_peeks: Number of times results have been checked
        baseline_rate: Expected baseline conversion rate (for power calc)
        minimum_detectable_effect: MDE as proportion (e.g., 0.10 for 10%)

    Returns:
        TestHealthReport with comprehensive health assessment

    Example:
        >>> health = check_health(
        ...     control_visitors=5000,
        ...     control_conversions=250,
        ...     variant_visitors=5000,
        ...     variant_conversions=280,
        ...     test_start_date="2024-01-01",
        ...     daily_traffic=1000,
        ... )
        >>> print(health.overall_status)
        'warning'
        >>> print(health.recommendation)
        "Run 2 more days to capture full week..."
    """
    checks = []
    issues = []

    total_visitors = control_visitors + variant_visitors

    # Calculate test duration if start date provided
    test_duration_days = None
    if test_start_date:
        try:
            start = datetime.strptime(test_start_date, "%Y-%m-%d")
            test_duration_days = (datetime.now() - start).days
        except ValueError:
            pass

    # Check 1: Sample Ratio Mismatch
    srm_result = check_sample_ratio(control_visitors, variant_visitors, expected_ratio)

    if srm_result.is_valid:
        checks.append(HealthCheckItem(
            name="Sample Ratio",
            status="pass",
            message=f"Traffic split is valid ({srm_result.observed_ratio*100:.1f}%/{(1-srm_result.observed_ratio)*100:.1f}%)",
        ))
    else:
        checks.append(HealthCheckItem(
            name="Sample Ratio",
            status="fail",
            message=f"SRM DETECTED: {srm_result.deviation_percent:.1f}% deviation (p={srm_result.p_value:.6f})",
            details="Traffic is not splitting as expected. Results may be invalid.",
        ))
        issues.append("Sample Ratio Mismatch detected - results may be invalid")

    # Check 2: Minimum Sample Size
    min_sample = min(control_visitors, variant_visitors)
    if min_sample >= minimum_sample_per_variant:
        checks.append(HealthCheckItem(
            name="Minimum Sample",
            status="pass",
            message=f"Sufficient sample size ({min_sample:,} >= {minimum_sample_per_variant:,} minimum)",
        ))
    else:
        checks.append(HealthCheckItem(
            name="Minimum Sample",
            status="fail" if min_sample < minimum_sample_per_variant / 2 else "warning",
            message=f"Sample too small ({min_sample:,} < {minimum_sample_per_variant:,} minimum)",
            details=f"Need {minimum_sample_per_variant - min_sample:,} more visitors in smaller group.",
        ))
        issues.append("Sample size below minimum")

    # Check 3: Test Duration (weekly patterns)
    if test_duration_days is not None:
        if test_duration_days >= minimum_days:
            checks.append(HealthCheckItem(
                name="Test Duration",
                status="pass",
                message=f"Running for {test_duration_days} days (>= {minimum_days} day minimum)",
            ))
        else:
            days_remaining = minimum_days - test_duration_days
            checks.append(HealthCheckItem(
                name="Test Duration",
                status="warning",
                message=f"Only {test_duration_days} days - recommend {minimum_days}+ for weekly patterns",
                details=f"Run {days_remaining} more days to capture full weekly cycle.",
            ))
            issues.append(f"Test duration too short ({test_duration_days} < {minimum_days} days)")
    else:
        checks.append(HealthCheckItem(
            name="Test Duration",
            status="warning",
            message="Unknown test duration - provide test_start_date to check",
        ))

    # Check 4: Statistical Power
    if baseline_rate is None:
        baseline_rate = control_conversions / control_visitors if control_visitors > 0 else 0.05

    if baseline_rate > 0 and min_sample > 0:
        # Calculate approximate power
        expected_variant_rate = baseline_rate * (1 + minimum_detectable_effect)
        effect_size = abs(expected_variant_rate - baseline_rate)

        pooled_p = (baseline_rate + expected_variant_rate) / 2
        se = math.sqrt(2 * pooled_p * (1 - pooled_p) / min_sample)

        if se > 0:
            z_effect = effect_size / se
            power = norm.cdf(z_effect - 1.96) + norm.cdf(-z_effect - 1.96)
            power = max(0, min(1, 1 - power))  # Adjust for two-sided
            # More accurate power calculation
            power = norm.cdf(z_effect - norm.ppf(0.975))
        else:
            power = 0

        power_pct = power * 100

        if power_pct >= 80:
            checks.append(HealthCheckItem(
                name="Statistical Power",
                status="pass",
                message=f"Power is {power_pct:.0f}% (>= 80% target)",
            ))
        elif power_pct >= 50:
            checks.append(HealthCheckItem(
                name="Statistical Power",
                status="warning",
                message=f"Power is only {power_pct:.0f}% (< 80% target)",
                details=f"You may not detect a {minimum_detectable_effect*100:.0f}% effect reliably.",
            ))
            issues.append(f"Low statistical power ({power_pct:.0f}%)")
        else:
            checks.append(HealthCheckItem(
                name="Statistical Power",
                status="fail",
                message=f"Power is very low ({power_pct:.0f}%)",
                details="Test is unlikely to detect the minimum effect size.",
            ))
            issues.append("Statistical power too low")
    else:
        checks.append(HealthCheckItem(
            name="Statistical Power",
            status="warning",
            message="Cannot calculate power - insufficient data",
        ))

    # Check 5: Peeking Risk
    if num_peeks > 1:
        # Approximate false positive inflation from peeking
        # This is a rough estimate - actual inflation depends on when peeks occurred
        inflated_alpha = min(0.05 * (1 + 0.1 * (num_peeks - 1)), 0.20)
        inflation_pct = (inflated_alpha / 0.05 - 1) * 100

        if num_peeks <= 3:
            checks.append(HealthCheckItem(
                name="Peeking Risk",
                status="warning",
                message=f"You've checked {num_peeks} times - slight false positive inflation",
                details=f"Estimated false positive rate: ~{inflated_alpha*100:.1f}% (vs 5% target)",
            ))
        else:
            checks.append(HealthCheckItem(
                name="Peeking Risk",
                status="fail",
                message=f"Checked {num_peeks} times - significant false positive inflation!",
                details=f"Consider using sequential testing to control for multiple looks.",
            ))
            issues.append(f"Excessive peeking ({num_peeks} times) inflates false positives")
    else:
        checks.append(HealthCheckItem(
            name="Peeking Risk",
            status="pass",
            message="First analysis - no peeking penalty",
        ))

    # Check 6: Sample Size Progress (if expected provided)
    if expected_visitors_per_variant:
        progress = min_sample / expected_visitors_per_variant
        progress_pct = progress * 100

        if progress >= 1.0:
            checks.append(HealthCheckItem(
                name="Sample Progress",
                status="pass",
                message=f"Reached planned sample size ({progress_pct:.0f}%)",
            ))
        elif progress >= 0.5:
            checks.append(HealthCheckItem(
                name="Sample Progress",
                status="warning",
                message=f"At {progress_pct:.0f}% of planned sample size",
                details=f"Need {expected_visitors_per_variant - min_sample:,} more visitors per variant.",
            ))
        else:
            checks.append(HealthCheckItem(
                name="Sample Progress",
                status="warning",
                message=f"Only {progress_pct:.0f}% of planned sample collected",
            ))

    # Calculate overall status and score
    fail_count = sum(1 for c in checks if c.status == "fail")
    warning_count = sum(1 for c in checks if c.status == "warning")
    pass_count = sum(1 for c in checks if c.status == "pass")

    if fail_count > 0:
        overall_status = "unhealthy"
    elif warning_count > 0:
        overall_status = "warning"
    else:
        overall_status = "healthy"

    # Score: each pass = 100/n, warning = 50/n, fail = 0
    n_checks = len(checks)
    score = int((pass_count * 100 + warning_count * 50) / n_checks) if n_checks > 0 else 0

    # Can we trust results?
    can_trust = (
        srm_result.is_valid and
        min_sample >= minimum_sample_per_variant and
        (test_duration_days is None or test_duration_days >= minimum_days)
    )

    # Generate recommendation
    if overall_status == "healthy":
        recommendation = (
            "Test looks healthy. You can analyze results with confidence."
        )
    elif overall_status == "warning":
        recommendation = (
            "Test has minor issues. Results may be directionally correct but "
            "consider addressing warnings before making final decisions.\n\n"
            f"Issues: {'; '.join(issues)}"
        )
    else:
        recommendation = (
            "TEST HAS CRITICAL ISSUES. Do not trust results until resolved.\n\n"
            f"Critical issues: {'; '.join(issues)}"
        )

    # Generate summary
    summary = _generate_summary(
        checks=checks,
        overall_status=overall_status,
        score=score,
        total_visitors=total_visitors,
        test_duration_days=test_duration_days,
        can_trust=can_trust,
        recommendation=recommendation,
    )

    return TestHealthReport(
        overall_status=overall_status,
        score=score,
        checks=checks,
        control_visitors=control_visitors,
        variant_visitors=variant_visitors,
        total_visitors=total_visitors,
        test_duration_days=test_duration_days,
        can_trust_results=can_trust,
        primary_issues=issues,
        recommendation=recommendation,
        summary=summary,
    )


def _generate_summary(
    checks: List[HealthCheckItem],
    overall_status: str,
    score: int,
    total_visitors: int,
    test_duration_days: Optional[int],
    can_trust: bool,
    recommendation: str,
) -> str:
    """Generate markdown summary of health report."""
    lines = ["## Test Health Report\n"]

    # Overall status with emoji
    status_emoji = {"healthy": "", "warning": "", "unhealthy": ""}
    lines.append(f"### {status_emoji.get(overall_status, '')} Overall: {overall_status.upper()} (Score: {score}/100)\n")

    # Quick stats
    duration_str = f"{test_duration_days} days" if test_duration_days else "Unknown"
    lines.append(f"- **Total visitors:** {total_visitors:,}")
    lines.append(f"- **Test duration:** {duration_str}")
    lines.append(f"- **Can trust results:** {'Yes' if can_trust else 'No'}")
    lines.append("")

    # Individual checks
    lines.append("### Health Checks\n")

    for check in checks:
        if check.status == "pass":
            icon = ""
        elif check.status == "warning":
            icon = ""
        else:
            icon = ""

        lines.append(f"{icon} **{check.name}:** {check.message}")
        if check.details:
            lines.append(f"   _{check.details}_")

    lines.append("")

    # Recommendation
    lines.append("### Recommendation\n")
    lines.append(recommendation)

    return "\n".join(lines)


__all__ = [
    "TestHealthReport",
    "HealthCheckItem",
    "check_health",
]
