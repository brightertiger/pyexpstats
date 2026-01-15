# Interactive Visualization Specifications (React + JS)

## General UI/UX Principles
- **Real-time Updates**: All charts should update immediately as user inputs change.
- **Responsiveness**: Use SVG-based libraries (like D3.js or Recharts) for crisp rendering on all screen sizes.
- **Interactivity**: Hover effects to show exact values, sliders for continuous variables (Power, Significance).

## 1. Sample Size & Sequential "Gray Area" Bar
- **Component**: `EffectSizeBar`
- **Visual**: A horizontal bar representing the conversion rate spectrum.
- **Features**:
    - Central marker for the **Baseline Rate**.
    - Shaded "Gray Area" extending from `Baseline - MDE` to `Baseline + MDE`.
    - Tooltip showing the exact range boundaries.
- **React Implementation**: Use a simple SVG with `<rect>` for the bar and `<line>` for markers.

## 2. Confidence Interval Comparison
- **Component**: `CIComparisonChart`
- **Visual**: Stacked horizontal bars for Sample 1 and Sample 2.
- **Features**:
    - A thin line representing the full confidence interval.
    - A thicker colored segment or a dot representing the point estimate (mean/rate).
    - Vertical reference line at the baseline or Sample 1's mean for easy comparison.
- **React Implementation**: Recharts `ComposedChart` or custom D3.

## 3. Distribution Curves (T-Test)
- **Component**: `DistributionOverlay`
- **Visual**: Overlapping Bell Curves (Normal/T-distribution).
- **Features**:
    - Three curves: Sample 1, Sample 2, and the Difference distribution.
    - Shaded areas for the "rejection regions" (tails).
    - Vertical dashed line at the mean of each distribution.
- **React Implementation**: D3.js is best for generating smooth paths based on statistical functions.

## 4. Kaplan-Meier Survival Plot
- **Component**: `SurvivalPlot`
- **Visual**: Step-function lines for survival probability over time.
- **Features**:
    - Two distinct colors for Sample 1 and Sample 2.
    - Shaded "Confidence Bands" (optional toggle).
    - Tick marks on the lines to indicate censored data points.
- **React Implementation**: Recharts `LineChart` with `layout="step"` or custom D3.

## 5. Sequential Random Walk (Optional but Recommended)
- **Component**: `SequentialWalk`
- **Visual**: A 2D plot showing the difference in successes ($T-C$) vs. total successes ($T+C$).
- **Features**:
    - Horizontal boundaries at $+d^*$ and $-d^*$.
    - A vertical boundary at $N$.
    - A "path" that grows as data is added (for the "Wizard" or live-tracking version).
- **React Implementation**: D3.js with a dynamic path generator.
