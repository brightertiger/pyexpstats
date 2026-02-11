"""
Diagnostic tools for A/B testing.

This module provides tools to validate your test:
- Sample Ratio Mismatch (SRM) detection
- Test health checks
- Novelty effect detection
"""

from pyexpstats.diagnostics.srm import check_sample_ratio, SampleRatioResult
from pyexpstats.diagnostics.health import check_health, TestHealthReport
from pyexpstats.diagnostics.novelty import detect_novelty_effect, NoveltyEffectResult

__all__ = [
    "check_sample_ratio",
    "SampleRatioResult",
    "check_health",
    "TestHealthReport",
    "detect_novelty_effect",
    "NoveltyEffectResult",
]
