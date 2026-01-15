# Test Cases for A/B Testing Software Validation

## 1. Sample Size Calculator
| Input Parameter | Value | Expected Output |
| --- | --- | --- |
| Baseline Rate | 20% | |
| MDE (Relative) | 5% | |
| Power | 80% | |
| Significance | 5% | **Sample Size: 1,030 per variation** |

## 2. Chi-Squared Test
| Sample | Successes | Trials | Expected Output |
| --- | --- | --- | --- |
| Sample 1 | 14 | 100 | CI: 8.5% – 22.1% |
| Sample 2 | 20 | 100 | CI: 13.3% – 28.9% |
| **Verdict** | | | **No significant difference (p = 0.26)** |

## 3. Two-Sample T-Test (Summary Stats)
| Sample | Mean | Std Dev | Count | Expected Output |
| --- | --- | --- | --- | --- |
| Sample 1 | 58.175 | 28.017 | 8 | |
| Sample 2 | 33.71 | 11.841 | 10 | |
| **Verdict** | | | | **Sample 1 mean is greater (p = 0.0462)** |

## 4. Poisson Means Test
| Sample | Events | Days | Expected Output |
| --- | --- | --- | --- |
| Sample 1 | 20 | 1 | CI: 12.2 – 30.9 |
| Sample 2 | 25 | 1 | CI: 16.2 – 36.9 |
| **Verdict** | | | **No significant difference (p = 0.55)** |

## 5. Sequential Sampling
| Input Parameter | Value | Expected Output |
| --- | --- | --- |
| Baseline Rate | 1% | |
| MDE (Absolute) | 20% | |
| Power | 80% | |
| Significance | 5% | **Control wins if: 808 total conversions** |
| | | **Treatment wins: 56 conversions ahead** |

## 6. Mean Survival Times
| Sample | Count | Avg Time | Expected Output |
| --- | --- | --- | --- |
| Sample 1 | 100 | 00:00:55 | CI: 45.6 – 1:07.6 |
| Sample 2 | 120 | 00:00:45 | CI: 37.9 – 54.3 |
| **Verdict** | | | **No significant difference (p = 0.14)** |
