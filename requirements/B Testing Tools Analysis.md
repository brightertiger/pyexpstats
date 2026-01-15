# A/B Testing Tools Analysis

## 1. Sample Size Calculator
- **Purpose**: Determine subjects needed for an A/B test.
- **Inputs**: Baseline conversion rate (%), Minimum Detectable Effect (%), Effect Type (Absolute/Relative), Statistical Power (1-β), Significance Level (α).
- **Outputs**: Sample size per variation.
- **Visuals**: Horizontal bar showing the "gray area" of the minimum detectable effect.

## 2. Chi-Squared Test
- **Purpose**: Compare success rates across two groups.
- **Inputs**: Successes and Trials for Sample 1 and Sample 2, Confidence Level.
- **Outputs**: Confidence intervals for each sample, Verdict (Significant/Not Significant), p-value.
- **Visuals**: Horizontal bars representing confidence intervals with a central point for the rate.

## 3. Two-Sample T-Test
- **Purpose**: Compare average values across two groups.
- **Inputs**: Raw data (list of numbers) or Summary stats (Mean, Std Dev, Count) for Sample 1 and Sample 2, Hypothesis type (d=0, d<=0, d>=0), Confidence Level.
- **Outputs**: Verdict, p-value, Mean ± Margin of Error.
- **Visuals**: Normal distribution curves for Sample 1, Sample 2, and the Difference of Means.

## 4. Survival Curves (Log-Rank Test)
- **Purpose**: Compare hazard rates (survival times) across two groups.
- **Inputs**: Survival times (with censoring marked by *) for Sample 1 and Sample 2, Confidence Level, Toggle for confidence bands.
- **Outputs**: Verdict, z-score, p-value.
- **Visuals**: Kaplan-Meier survival curves with optional shaded confidence bands.

## 5. Poisson Means Test
- **Purpose**: Compare arrival rates (events over time).
- **Inputs**: Events and Days for Sample 1 and Sample 2, Confidence Level.
- **Outputs**: Confidence intervals for arrival rates, Verdict, p-value.
- **Visuals**: Horizontal bars for confidence intervals.

## 6. Sequential Sampling Calculator
- **Purpose**: Determine conversions needed for sequential A/B testing.
- **Inputs**: Baseline conversion rate, Minimum Detectable Effect, Effect Type, Statistical Power, Significance Level.
- **Outputs**: Total conversions for "Control wins", Conversions ahead for "Treatment wins".
- **Visuals**: Similar to Sample Size Calculator.

## 7. Mean Survival Times Test
- **Purpose**: Compare average survival times.
- **Inputs**: Count and Average Survival Time (HH:MM:SS) for Sample 1 and Sample 2, Confidence Level.
- **Outputs**: Confidence intervals, Verdict, p-value.
- **Visuals**: Horizontal bars for confidence intervals.
