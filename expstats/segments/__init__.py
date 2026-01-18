"""
Segment Analysis Module.

Tools to analyze A/B test results across user segments:
- Segment-level lift analysis
- Simpson's Paradox detection
- Winner identification by segment
- Statistical corrections for multiple comparisons
"""

from expstats.segments.analysis import (
    analyze_segments,
    SegmentResult,
    SegmentAnalysisReport,
)

__all__ = [
    "analyze_segments",
    "SegmentResult",
    "SegmentAnalysisReport",
]
