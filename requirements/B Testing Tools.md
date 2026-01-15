# Statistical Formulas for A/B Testing Tools

## 1. Sample Size Calculator
- **Formula**: $n = \frac{16\sigma^2}{\delta^2}$ (Rule of thumb for 80% power and 5% significance).
- **Variance**: $\sigma^2 = p(1-p)$ for binomial proportions.
- **More Precise**: $n = \frac{(z_{\alpha/2} + z_{\beta})^2 \cdot 2 \cdot p(1-p)}{\delta^2}$ where $z_{\alpha/2}$ is the critical value for significance and $z_{\beta}$ is the critical value for power.

## 2. Chi-Squared Test (2x2)
- **Test Statistic**: $\chi^2 = \sum \frac{(O-E)^2}{E}$
- **Confidence Interval (Wald)**: $\hat{p} \pm z_{\alpha/2} \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$
- **p-value**: Calculated from the Chi-squared distribution with 1 degree of freedom.

## 3. Two-Sample T-Test
- **Test Statistic**: $t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$ (Welch's T-test for unequal variances).
- **Degrees of Freedom**: Satterthwaite approximation.
- **Confidence Interval**: $(\bar{x}_1 - \bar{x}_2) \pm t_{\alpha/2, df} \cdot SE_{diff}$.

## 4. Survival Curves (Log-Rank Test)
- **Method**: Kaplan-Meier estimator for survival curves.
- **Log-Rank Statistic**: $Z = \frac{\sum (O_i - E_i)}{\sqrt{\sum V_i}}$ where $O_i$ is observed events and $E_i$ is expected events.
- **Confidence Bands**: Greenwood's formula.

## 5. Poisson Means Test
- **Arrival Rate**: $\lambda = \frac{\text{Events}}{\text{Time}}$.
- **Confidence Interval**: Based on the relationship between Poisson and Chi-squared distributions.
- **Test**: Comparison of two Poisson rates using the conditional binomial test.

## 6. Sequential Sampling
- **Probability of Success**: $p = \frac{p_c}{p_c + p_t}$.
- **Boundary $d^*$**: Total difference in successes needed to stop.
- **Stopping Rule**: Stop when $T-C$ reaches $d^*$ or $T+C$ reaches $N$.
- **Formula**: $R_{N,d} = \sum_{n=1}^N \frac{d}{n} \binom{n}{(n+d)/2} p^{(n-d)/2} (1-p)^{(n+d)/2}$.
