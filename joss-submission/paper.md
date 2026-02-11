---
title: 'pyexpstats: A Comprehensive Python Library for A/B Testing and Experimentation Statistics'
tags:
  - Python
  - A/B testing
  - statistics
  - experimentation
  - Bayesian inference
  - sequential testing
authors:
  - name: pyexpstats contributors
    affiliation: 1
affiliations:
  - name: Independent
    index: 1
date: 18 January 2026
bibliography: references.bib
---

# Summary

**pyexpstats** is an open-source Python library that provides a complete statistical toolkit for A/B testing and online experimentation. The library offers sample size calculation, power analysis, significance testing, Bayesian inference, sequential testing with early stopping, and business impact projections. Designed with both analysts and non-technical users in mind, pyexpstats includes a web-based user interface that makes statistical analysis accessible to marketing and product teams.

# Statement of Need

Online controlled experiments (A/B tests) have become the gold standard for data-driven decision making in technology companies [@kohavi2020trustworthy]. However, proper statistical analysis of experiments requires expertise that many practitioners lack. Despite the proliferation of A/B testing tools, most solutions fall into two categories: expensive enterprise platforms or fragmented open-source libraries that require significant statistical knowledge.

pyexpstats addresses several critical gaps:

1. **Accessibility**: Complex statistical concepts are translated into business-friendly language (e.g., "Chance to Win" instead of "Bayesian posterior probability")

2. **Comprehensiveness**: A single library covers the entire experimentation lifecycle from planning through analysis

3. **Diagnostic Tools**: Built-in detection for common issues like Sample Ratio Mismatch (SRM), novelty effects, and Simpson's paradox [@fabijan2019diagnosing]

4. **Multiple Methodologies**: Support for frequentist, Bayesian [@stucchio2015bayesian], and sequential testing [@jennison1999group] approaches

# Key Features

## Sample Size Planning

Proper experiment planning is crucial for reliable results. pyexpstats provides sample size calculators for conversion rate tests, revenue/magnitude tests, and time-to-event analyses.

```python
from pyexpstats import conversion

plan = conversion.sample_size(
    current_rate=0.05,      # 5% baseline conversion
    lift_percent=10,        # Detect 10% relative lift
    confidence=95,          # 95% confidence level
    power=80                # 80% statistical power
)
print(f"Visitors per variant: {plan.visitors_per_variant:,}")
# Output: Visitors per variant: 31,234
```

![Sample Size Calculator interface showing planning for a conversion rate experiment](figures/sample-size-calculator.png)

## Statistical Analysis Methods

pyexpstats supports three complementary analysis approaches:

### Classic (Frequentist) Analysis
Traditional hypothesis testing with p-values and confidence intervals using two-sample z-tests for proportions and t-tests for continuous outcomes.

### Bayesian Analysis
Computes the probability that one variant is better than another, providing more intuitive interpretations for decision-makers [@stucchio2015bayesian].

```python
from pyexpstats.methods import bayesian

result = bayesian.analyze(
    control_visitors=10000,
    control_conversions=500,
    variant_visitors=10000,
    variant_conversions=550
)
print(f"Probability variant wins: {result.probability_variant_better:.1%}")
# Output: Probability variant wins: 94.2%
```

### Sequential Testing
Enables valid early stopping decisions using group sequential methods with O'Brien-Fleming or Pocock spending functions [@jennison1999group; @johari2017peeking].

![Results Analysis interface showing three analysis methods](figures/analyze-results.png)

## Diagnostic Tools

Experimental validity depends on detecting issues that can bias results:

- **Sample Ratio Mismatch (SRM)**: Detects when traffic allocation differs from the intended split [@fabijan2019diagnosing]
- **Novelty Effect Detection**: Identifies whether treatment effects change over time
- **Experiment Health Score**: Overall assessment combining multiple diagnostic checks

```python
from pyexpstats.diagnostics import srm, novelty

# Check for Sample Ratio Mismatch
srm_result = srm.check(
    control_visitors=10000,
    variant_visitors=9500,
    expected_ratio=0.5
)
print(f"SRM detected: {srm_result.has_srm}")
```

![Diagnostics interface showing experiment health checks](figures/diagnostics.png)

## Segment Analysis

Analyzing results across user segments requires proper multiple comparison corrections. pyexpstats supports Bonferroni correction (conservative), Holm-Bonferroni correction (balanced), and Simpson's Paradox detection [@simpson1951interpretation].

![Segment Analysis interface showing results breakdown by user groups](figures/segments.png)

## Business Impact Projections

Translating statistical results into business value helps stakeholders understand the real-world implications of experiment results.

```python
from pyexpstats.business import impact

projection = impact.project(
    baseline_value=1000000,      # $1M monthly revenue
    lift_percent=5.0,            # 5% observed lift
    confidence_interval=(3.0, 7.0),
    time_horizon_months=12
)
print(f"Expected annual impact: ${projection.expected_impact:,.0f}")
```

![Revenue Impact interface showing projected business value](figures/impact.png)

# Architecture

pyexpstats is designed with a modular architecture:

| Module | Purpose |
|--------|---------|
| `pyexpstats.effects.outcome.conversion` | Binary outcome analysis |
| `pyexpstats.effects.outcome.magnitude` | Continuous outcome analysis |
| `pyexpstats.effects.outcome.timing` | Time-to-event analysis |
| `pyexpstats.methods.bayesian` | Bayesian inference |
| `pyexpstats.methods.sequential` | Sequential testing |
| `pyexpstats.diagnostics` | Experiment health checks |
| `pyexpstats.segments` | Segment analysis |
| `pyexpstats.business` | Impact projections |

# Installation and Usage

```bash
pip install pyexpstats
```

To run the web interface:

```bash
pyexpstats-server
```

# Testing

pyexpstats includes a comprehensive test suite with 367+ tests covering statistical correctness validation, edge case handling, and API endpoint testing.

```bash
pytest tests/ -v
```

# Acknowledgements

We thank the open-source community for the foundational libraries that make pyexpstats possible, particularly NumPy, SciPy, and FastAPI.

# References
