# JOSS Submission Materials for pyexpstats

This folder contains the submission materials for the Journal of Open Source Software (JOSS).

## Contents

- `paper.tex` - LaTeX version of the paper
- `paper.md` - Markdown version (JOSS preferred format)
- `references.bib` - BibTeX references
- `figures/` - Screenshots of the application

## Required Screenshots

Please take the following screenshots and save them in the `figures/` folder:

### 1. sample-size-calculator.png
- URL: http://localhost:5173/
- Shows the Plan page with sample size calculation
- Fill in example values and show the results

### 2. analyze-results.png
- URL: http://localhost:5173/analyze
- Shows the Analyze page with all three methods tabs visible
- Include example results showing Classic, Chance to Win, and Early Stopping

### 3. diagnostics.png
- URL: http://localhost:5173/diagnostics
- Shows the Diagnostics page with health checks
- Include Overall Health, Traffic Balance, and Effect Over Time tabs

### 4. segments.png
- URL: http://localhost:5173/segments
- Shows the Segment Analysis page
- Include example segment results with the correction settings

### 5. impact.png
- URL: http://localhost:5173/impact
- Shows the Revenue Impact projection page
- Include example projection results

## How to Take Screenshots

1. Ensure the application is running:
   ```bash
   # Terminal 1: API server
   python -m pyexpstats.api

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

2. Open each URL in your browser

3. Fill in example data and calculate results

4. Take screenshots (recommended size: 1200x800 pixels)

5. Save to the `figures/` folder with the exact filenames listed above

## Building the Paper

### LaTeX Version
```bash
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

### Markdown Version (JOSS Preferred)
JOSS uses pandoc to compile the paper. Follow their submission guidelines:
https://joss.readthedocs.io/en/latest/submitting.html

## JOSS Submission Checklist

- [ ] Software is open source (MIT License)
- [ ] Repository is publicly accessible
- [ ] Documentation exists
- [ ] Installation instructions provided
- [ ] Example usage included
- [ ] Tests are included (367+ tests)
- [ ] Paper follows JOSS format
- [ ] All screenshots captured
- [ ] References are complete

## Submission URL

Submit at: https://joss.theoj.org/papers/new
