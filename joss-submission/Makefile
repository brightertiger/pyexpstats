# Makefile for JOSS paper

.PHONY: all latex pdf clean check

# Default target
all: pdf

# Build PDF from LaTeX
latex: paper.tex references.bib
	pdflatex paper.tex
	bibtex paper
	pdflatex paper.tex
	pdflatex paper.tex

# Build PDF using pandoc (JOSS style)
pdf: paper.md references.bib
	pandoc paper.md \
		--from=markdown \
		--to=pdf \
		--output=paper.pdf \
		--citeproc \
		--bibliography=references.bib \
		--pdf-engine=xelatex \
		-V geometry:margin=1in \
		-V fontsize=11pt

# Check that all required files exist
check:
	@echo "Checking required files..."
	@test -f paper.md && echo "  ✓ paper.md" || echo "  ✗ paper.md missing"
	@test -f paper.tex && echo "  ✓ paper.tex" || echo "  ✗ paper.tex missing"
	@test -f references.bib && echo "  ✓ references.bib" || echo "  ✗ references.bib missing"
	@test -f figures/sample-size-calculator.png && echo "  ✓ sample-size-calculator.png" || echo "  ✗ sample-size-calculator.png missing"
	@test -f figures/analyze-results.png && echo "  ✓ analyze-results.png" || echo "  ✗ analyze-results.png missing"
	@test -f figures/diagnostics.png && echo "  ✓ diagnostics.png" || echo "  ✗ diagnostics.png missing"
	@test -f figures/segments.png && echo "  ✓ segments.png" || echo "  ✗ segments.png missing"
	@test -f figures/impact.png && echo "  ✓ impact.png" || echo "  ✗ impact.png missing"

# Clean build artifacts
clean:
	rm -f paper.pdf paper.aux paper.bbl paper.blg paper.log paper.out

# Word count
wordcount:
	@pandoc paper.md --to=plain | wc -w
