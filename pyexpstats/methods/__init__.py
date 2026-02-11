"""
Statistical methods for A/B testing.

This module provides different statistical approaches:
- sequential: Sequential testing with early stopping
- bayesian: Bayesian A/B testing
"""

from pyexpstats.methods import sequential
from pyexpstats.methods import bayesian

__all__ = ["sequential", "bayesian"]
