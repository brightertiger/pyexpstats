"""
Statistical methods for A/B testing.

This module provides different statistical approaches:
- sequential: Sequential testing with early stopping
- bayesian: Bayesian A/B testing
"""

from expstats.methods import sequential
from expstats.methods import bayesian

__all__ = ["sequential", "bayesian"]
