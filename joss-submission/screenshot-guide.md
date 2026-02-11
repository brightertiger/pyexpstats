# Screenshot Guide for JOSS Submission

## Overview

This guide provides the exact URLs and example data to use when capturing screenshots for the paper.

---

## Screenshot 1: Sample Size Calculator

**File:** `figures/sample-size-calculator.png`
**URL:** http://localhost:5173/

### Example Data to Enter:
- **Test Type:** Conversion Rate (default)
- **Current Conversion Rate:** 5%
- **Improvement to Detect:** 10%
- **Confidence Level:** 95%
- **Statistical Power:** 80%
- **Number of Variants:** 2

### What to Capture:
- The full page showing inputs and the calculated results
- Results should show ~31,234 visitors per variant
- Include the "What these settings mean" explanations

---

## Screenshot 2: Analyze Results

**File:** `figures/analyze-results.png`
**URL:** http://localhost:5173/analyze

### Example Data to Enter:
- **Test Type:** Conversion Rate
- **Control Visitors:** 10,000
- **Control Conversions:** 500
- **Variant Visitors:** 10,000
- **Variant Conversions:** 550

### Capture Three States:
1. **Classic tab** - Shows p-value and confidence interval
2. **Chance to Win tab** - Shows probability variant is better (~94%)
3. **Early Stopping tab** - Shows test progress and stopping boundaries

### Recommendation:
Take one screenshot showing the "Chance to Win" tab with full results visible.

---

## Screenshot 3: Diagnostics

**File:** `figures/diagnostics.png`
**URL:** http://localhost:5173/diagnostics

### Example Data for Each Tab:

#### Overall Health Tab:
- Control Visitors: 10,000
- Variant Visitors: 10,000
- Control Conversions: 500
- Variant Conversions: 550
- Test Duration (days): 14
- Expected Split: 50/50

#### Traffic Balance Tab:
- Control Visitors: 10,000
- Variant Visitors: 9,500
- Expected Split: 50/50
(This shows a potential SRM issue)

#### Effect Over Time Tab:
- Enter daily data showing decreasing effect:
  - Day 1: 1000 visitors, 15% lift
  - Day 2: 1000 visitors, 12% lift
  - Day 3: 1000 visitors, 8% lift
  - Day 4: 1000 visitors, 5% lift
  - Day 5: 1000 visitors, 4% lift

### Recommendation:
Take screenshot of "Overall Health" tab showing the health score.

---

## Screenshot 4: Segment Analysis

**File:** `figures/segments.png`
**URL:** http://localhost:5173/segments

### Example Data to Enter:

#### Overall Results:
- Control Visitors: 20,000
- Control Conversions: 1,000
- Variant Visitors: 20,000
- Variant Conversions: 1,100

#### Segments (add 3-4 segments):

**Segment 1 - Mobile Users:**
- Control Visitors: 8,000
- Control Conversions: 320
- Variant Visitors: 8,000
- Variant Conversions: 400

**Segment 2 - Desktop Users:**
- Control Visitors: 10,000
- Control Conversions: 600
- Variant Visitors: 10,000
- Variant Conversions: 650

**Segment 3 - New Users:**
- Control Visitors: 5,000
- Control Conversions: 200
- Variant Visitors: 5,000
- Variant Conversions: 280

**Segment 4 - Returning Users:**
- Control Visitors: 15,000
- Control Conversions: 800
- Variant Visitors: 15,000
- Variant Conversions: 820

### Settings:
- Correction Method: Balanced (Holm)

### What to Capture:
- Full results showing segment breakdown
- Highlight any Simpson's Paradox warnings if they appear

---

## Screenshot 5: Revenue Impact

**File:** `figures/impact.png`
**URL:** http://localhost:5173/impact

### Example Data to Enter:
- **Current Monthly Revenue:** $1,000,000
- **Observed Lift:** 5%
- **Confidence Interval Lower:** 3%
- **Confidence Interval Upper:** 7%
- **Time Horizon:** 12 months
- **Statistical Significance:** Yes

### What to Capture:
- Full projection results showing:
  - Expected annual impact (~$600,000)
  - Range of outcomes
  - Monthly breakdown if available

---

## Screenshot Tips

1. **Browser Width:** Use a consistent browser width of ~1200px
2. **Zoom Level:** Keep at 100% for consistency
3. **Dark Mode:** Use light mode for paper readability
4. **Results Visible:** Always show calculated results, not empty forms
5. **Crop:** Crop to show relevant UI, exclude browser chrome
6. **Format:** Save as PNG with good quality

## Recommended Tools

- **macOS:** Cmd+Shift+4 (select area)
- **Windows:** Snipping Tool or Win+Shift+S
- **Browser:** Chrome DevTools > More tools > Screenshot

---

## File Naming

Save screenshots with exact names:
```
figures/
├── sample-size-calculator.png
├── analyze-results.png
├── diagnostics.png
├── segments.png
└── impact.png
```
