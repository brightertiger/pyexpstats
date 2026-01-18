"""
Business Impact Module.

Tools to translate A/B test results into business value:
- Revenue/impact projections
- Guardrail metrics monitoring
"""

from expstats.business.impact import (
    project_impact,
    ImpactProjection,
)
from expstats.business.guardrails import (
    check_guardrails,
    GuardrailResult,
    GuardrailCheck,
)

__all__ = [
    "project_impact",
    "ImpactProjection",
    "check_guardrails",
    "GuardrailResult",
    "GuardrailCheck",
]
