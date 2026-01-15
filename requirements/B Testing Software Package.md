# Developer Specification: A/B Testing Software Package

## Executive Summary
This report outlines the requirements for building a comprehensive A/B testing software package, mimicking the functionalities of Evan Miller's A/B tools. The package will include calculators for sample size, statistical significance, and survival analysis, featuring interactive visualizations built with **React** and **JavaScript**.

---

## 1. Core Functionalities & Statistical Requirements

The software must support the following primary statistical tests. Each tool requires specific inputs and generates precise outputs based on established statistical formulas.

### 1.1 Sample Size Planning
- **Tools**: Fixed-sample size calculator and Sequential sampling calculator.
- **Key Formulas**: 
    - Fixed: $n = \frac{16\sigma^2}{\delta^2}$ for 80% power/5% significance.
    - Sequential: Boundary $d^*$ based on the random walk theory of successes.
- **Requirement**: Support both **Absolute** and **Relative** Minimum Detectable Effects (MDE).

### 1.2 Significance Testing
| Test Type | Use Case | Key Metric |
| --- | --- | --- |
| **Chi-Squared** | Binary outcomes (conversions, clicks) | Success Rate (%) |
| **Two-Sample T-Test** | Continuous outcomes (revenue, time) | Mean Value |
| **Poisson Means** | Event rates over time (arrivals, errors) | Events per Day |
| **Log-Rank Test** | Time-to-event data (churn, subscription) | Hazard Rate |

---

## 2. Interactive Visualization Specifications

Visualizations must be built using React and a modern charting library (e.g., **D3.js**, **Recharts**, or **Victory**).

### 2.1 Confidence Interval Bars
- **Visual**: Horizontal bars showing the point estimate and the confidence interval (CI) range.
- **Interaction**: Hovering over the bar should display the exact CI (e.g., "8.5% – 22.1%").
- **Logic**: If two CI bars do not overlap significantly, the UI should highlight the "Significant" verdict.

### 2.2 Distribution Curves (T-Test)
- **Visual**: Overlapping bell curves representing the probability density functions of the two samples.
- **Interaction**: Dynamic shifting of curves as the user modifies Mean or Standard Deviation inputs.
- **Highlighting**: Shade the area representing the p-value (rejection region).

### 2.3 Kaplan-Meier Survival Curves
- **Visual**: Step-function plots showing survival probability over time.
- **Features**:
    - Toggleable **Confidence Bands** (shaded areas around the lines).
    - Markers for **Censored Data** (e.g., a small '+' or tick mark).

---

## 3. Validation & Test Cases

To ensure the correctness of the generated results, the following test cases must be implemented in the test suite.

### 3.1 Sample Size Validation
- **Input**: Baseline 20%, MDE 5% (Relative), Power 80%, Alpha 5%.
- **Expected Result**: 1,030 subjects per variation.

### 3.2 Chi-Squared Validation
- **Input**: Sample A (14/100), Sample B (20/100).
- **Expected Result**: p-value = 0.26, Verdict: "No significant difference".

### 3.3 T-Test Validation
- **Input**: Sample A (Mean 58.175, SD 28.017, N 8), Sample B (Mean 33.71, SD 11.841, N 10).
- **Expected Result**: p-value = 0.0462, Verdict: "Sample 1 mean is greater".

---

## 4. Implementation Recommendations

- **State Management**: Use React's `useMemo` for statistical calculations to prevent unnecessary re-computations on every render.
- **Math Library**: Utilize `simple-statistics` or `jstat` for robust statistical functions in JavaScript.
- **Styling**: Use **Tailwind CSS** for a clean, professional interface similar to the reference site.
- **Accessibility**: Ensure all charts have appropriate ARIA labels and tabular fallbacks for screen readers.
