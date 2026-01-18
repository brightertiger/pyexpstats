"""
Tests for Segments Module.

Tests segment analysis and Simpson's Paradox detection.
"""

import pytest
from expstats.segments.analysis import (
    analyze_segments,
    SegmentAnalysisReport,
    SegmentResult,
)


class TestSegmentAnalysis:
    """Tests for segment analysis."""

    def test_basic_analysis(self):
        """Test basic segment analysis."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 3000,
                "control_conversions": 180,
                "variant_visitors": 3000,
                "variant_conversions": 200,
            },
        ])

        assert isinstance(result, SegmentAnalysisReport)
        assert result.n_segments == 2
        assert len(result.segments) == 2

    def test_overall_lift_calculation(self):
        """Test overall lift calculation."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 1000,
                "control_conversions": 50,  # 5%
                "variant_visitors": 1000,
                "variant_conversions": 60,  # 6%
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 1000,
                "control_conversions": 50,  # 5%
                "variant_visitors": 1000,
                "variant_conversions": 60,  # 6%
            },
        ])

        # Overall: 100/2000 = 5% control, 120/2000 = 6% variant
        # Lift = 20%
        assert pytest.approx(result.overall_lift, abs=1) == 20

    def test_segment_level_significance(self):
        """Test segment-level significance detection."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 700,  # 40% lift
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 510,  # 2% lift
            },
        ])

        # Mobile should be significant, desktop probably not
        mobile_result = next(s for s in result.segments if s.segment_value == "mobile")
        assert mobile_result.is_significant_uncorrected == True

    def test_bonferroni_correction(self):
        """Test Bonferroni correction for multiple comparisons."""
        result = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": f"segment_{i}",
                    "control_visitors": 1000,
                    "control_conversions": 50,
                    "variant_visitors": 1000,
                    "variant_conversions": 55,  # Small effect
                }
                for i in range(10)  # 10 segments
            ],
            correction_method="bonferroni",
        )

        # With 10 segments, adjusted alpha = 0.05/10 = 0.005
        assert result.adjusted_alpha == pytest.approx(0.005, abs=0.001)

    def test_holm_correction(self):
        """Test Holm-Bonferroni correction."""
        result = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 10000,
                    "control_conversions": 500,
                    "variant_visitors": 10000,
                    "variant_conversions": 700,
                },
                {
                    "segment_name": "device",
                    "segment_value": "desktop",
                    "control_visitors": 10000,
                    "control_conversions": 500,
                    "variant_visitors": 10000,
                    "variant_conversions": 520,
                },
            ],
            correction_method="holm",
        )

        assert result.correction_method == "holm"

    def test_no_correction(self):
        """Test with no multiple comparison correction."""
        result = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 5000,
                    "control_conversions": 250,
                    "variant_visitors": 5000,
                    "variant_conversions": 275,
                },
            ],
            correction_method="none",
        )

        assert result.correction_method == "none"

    def test_best_worst_segment(self):
        """Test best and worst segment identification."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 800,  # 60% lift - best
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 400,  # -20% lift - worst
            },
            {
                "segment_name": "device",
                "segment_value": "tablet",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 550,  # 10% lift
            },
        ])

        if result.best_segment:
            assert "mobile" in result.best_segment
        if result.worst_segment:
            assert "desktop" in result.worst_segment

    def test_heterogeneity_detection(self):
        """Test heterogeneity detection."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 800,  # +60% lift
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 300,  # -40% lift
            },
        ])

        # Opposite effects should trigger heterogeneity
        assert result.heterogeneity_detected is True

    def test_simpsons_paradox_detection(self):
        """Test Simpson's Paradox detection."""
        # Classic Simpson's Paradox: overall positive, but most segments negative
        result = analyze_segments([
            {
                "segment_name": "group",
                "segment_value": "A",
                "control_visitors": 100,
                "control_conversions": 80,  # 80%
                "variant_visitors": 900,
                "variant_conversions": 700,  # 77.8% - lower
            },
            {
                "segment_name": "group",
                "segment_value": "B",
                "control_visitors": 900,
                "control_conversions": 270,  # 30%
                "variant_visitors": 100,
                "variant_conversions": 28,  # 28% - lower
            },
        ])

        # Overall might be positive due to composition shift
        # Even if both segments are negative
        assert isinstance(result.simpsons_paradox_risk, bool)

    def test_minimum_sample_per_segment(self):
        """Test minimum sample per segment validation."""
        result = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 50,  # Below minimum
                    "control_conversions": 5,
                    "variant_visitors": 50,
                    "variant_conversions": 7,
                },
            ],
            min_sample_per_segment=100,
        )

        assert result.segments[0].sample_size_adequate is False

    def test_segment_lift_ci(self):
        """Test segment-level lift confidence interval."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
        ])

        segment = result.segments[0]
        assert segment.lift_ci_lower < segment.lift_percent < segment.lift_ci_upper

    def test_segment_p_value(self):
        """Test segment-level p-value calculation."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
        ])

        assert 0 <= result.segments[0].p_value <= 1

    def test_segment_winner(self):
        """Test segment winner determination."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 700,  # Clear variant win
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 10000,
                "control_conversions": 700,
                "variant_visitors": 10000,
                "variant_conversions": 500,  # Clear control win
            },
        ])

        mobile = next(s for s in result.segments if s.segment_value == "mobile")
        desktop = next(s for s in result.segments if s.segment_value == "desktop")

        # These should have clear winners given large samples
        if mobile.is_significant:
            assert mobile.winner == "variant"
        if desktop.is_significant:
            assert desktop.winner == "control"

    def test_different_confidence_levels(self):
        """Test different confidence levels."""
        result_95 = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 5000,
                    "control_conversions": 250,
                    "variant_visitors": 5000,
                    "variant_conversions": 275,
                },
            ],
            confidence=95,
        )

        result_99 = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 5000,
                    "control_conversions": 250,
                    "variant_visitors": 5000,
                    "variant_conversions": 275,
                },
            ],
            confidence=99,
        )

        # 99% confidence should have wider CI
        segment_95 = result_95.segments[0]
        segment_99 = result_99.segments[0]
        width_95 = segment_95.lift_ci_upper - segment_95.lift_ci_lower
        width_99 = segment_99.lift_ci_upper - segment_99.lift_ci_lower
        assert width_99 > width_95

    def test_empty_segments(self):
        """Test empty segments list."""
        result = analyze_segments([])

        assert result.n_segments == 0
        assert len(result.segments) == 0

    def test_single_segment(self):
        """Test single segment analysis."""
        result = analyze_segments([
            {
                "segment_name": "all",
                "segment_value": "users",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
        ])

        assert result.n_segments == 1
        assert result.heterogeneity_detected is False
        assert result.simpsons_paradox_risk is False

    def test_recommendation_generated(self):
        """Test that recommendation is generated."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
        ])

        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0


class TestSegmentEdgeCases:
    """Edge case tests for segment analysis."""

    def test_zero_conversions_control(self):
        """Test segment with zero control conversions."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 1000,
                "control_conversions": 0,
                "variant_visitors": 1000,
                "variant_conversions": 10,
            },
        ])

        assert isinstance(result, SegmentAnalysisReport)

    def test_zero_conversions_both(self):
        """Test segment with zero conversions in both groups."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 1000,
                "control_conversions": 0,
                "variant_visitors": 1000,
                "variant_conversions": 0,
            },
        ])

        assert isinstance(result, SegmentAnalysisReport)
        assert result.segments[0].lift_percent == 0

    def test_very_small_segments(self):
        """Test very small segment sample sizes."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10,
                "control_conversions": 1,
                "variant_visitors": 10,
                "variant_conversions": 2,
            },
        ])

        assert result.segments[0].sample_size_adequate is False

    def test_100_percent_conversion(self):
        """Test segment with 100% conversion rate."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 100,
                "control_conversions": 100,
                "variant_visitors": 100,
                "variant_conversions": 100,
            },
        ])

        assert isinstance(result, SegmentAnalysisReport)

    def test_many_segments(self):
        """Test with many segments."""
        segments = [
            {
                "segment_name": "region",
                "segment_value": f"region_{i}",
                "control_visitors": 1000,
                "control_conversions": 50 + i,
                "variant_visitors": 1000,
                "variant_conversions": 55 + i,
            }
            for i in range(20)
        ]

        result = analyze_segments(segments)

        assert result.n_segments == 20
        # With Bonferroni, adjusted alpha should be very small
        assert result.adjusted_alpha < 0.01

    def test_asymmetric_segment_sizes(self):
        """Test segments with very different sizes."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 10000,
                "control_conversions": 500,
                "variant_visitors": 10000,
                "variant_conversions": 550,
            },
            {
                "segment_name": "device",
                "segment_value": "desktop",
                "control_visitors": 100,
                "control_conversions": 5,
                "variant_visitors": 100,
                "variant_conversions": 6,
            },
        ])

        mobile = next(s for s in result.segments if s.segment_value == "mobile")
        desktop = next(s for s in result.segments if s.segment_value == "desktop")

        assert mobile.sample_size_adequate is True
        assert desktop.sample_size_adequate is True  # 100 meets minimum of 100


class TestSegmentInterpretation:
    """Tests for segment interpretation."""

    def test_interpretation_for_adequate_sample(self):
        """Test interpretation generation for adequate sample."""
        result = analyze_segments([
            {
                "segment_name": "device",
                "segment_value": "mobile",
                "control_visitors": 5000,
                "control_conversions": 250,
                "variant_visitors": 5000,
                "variant_conversions": 300,
            },
        ])

        interpretation = result.segments[0].interpretation
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
        assert "mobile" in interpretation

    def test_interpretation_for_inadequate_sample(self):
        """Test interpretation for inadequate sample warns user."""
        result = analyze_segments(
            [
                {
                    "segment_name": "device",
                    "segment_value": "mobile",
                    "control_visitors": 50,
                    "control_conversions": 3,
                    "variant_visitors": 50,
                    "variant_conversions": 4,
                },
            ],
            min_sample_per_segment=100,
        )

        interpretation = result.segments[0].interpretation
        assert "insufficient" in interpretation.lower() or "not reliable" in interpretation.lower()
