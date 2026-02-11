from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
import os

from pyexpstats.effects.outcome import conversion, magnitude, timing
from pyexpstats.methods import bayesian, sequential
from pyexpstats.diagnostics import srm, health, novelty
from pyexpstats.segments import analysis as segment_analysis
from pyexpstats.business import impact

app = FastAPI(
    title="pyexpstats API",
    description="Simple A/B testing tools for marketers and analysts",
    version="0.1.0",
)

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=CORS_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class ConversionSampleSizeRequest(BaseModel):
    current_rate: float = Field(..., description="Current conversion rate (e.g., 5 for 5% or 0.05)")
    lift_percent: float = Field(10, description="Minimum lift to detect in % (e.g., 10 for 10%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")
    num_variants: int = Field(2, ge=2, le=10, description="Number of variants including control")


class ConversionAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_conversions: int = Field(..., ge=0, description="Number of conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Number of conversions in variant")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("A/B Test", description="Name for the summary report")


class ConversionVariant(BaseModel):
    name: str = Field(..., description="Variant name (e.g., 'control', 'variant_a')")
    visitors: int = Field(..., gt=0, description="Number of visitors")
    conversions: int = Field(..., ge=0, description="Number of conversions")


class ConversionMultiAnalyzeRequest(BaseModel):
    variants: List[ConversionVariant] = Field(..., min_length=2, description="List of variants")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    correction: Literal["bonferroni", "none"] = Field("bonferroni", description="Multiple comparison correction")
    test_name: str = Field("Multi-Variant Test", description="Name for the summary report")


class ConversionConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=0, description="Total visitors")
    conversions: int = Field(..., ge=0, description="Total conversions")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class MagnitudeSampleSizeRequest(BaseModel):
    current_mean: float = Field(..., description="Current average value (e.g., $50)")
    current_std: float = Field(..., gt=0, description="Standard deviation")
    lift_percent: float = Field(5, description="Minimum lift to detect in % (e.g., 5 for 5%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")
    num_variants: int = Field(2, ge=2, le=10, description="Number of variants including control")


class MagnitudeAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_mean: float = Field(..., description="Average value in control")
    control_std: float = Field(..., ge=0, description="Standard deviation in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_mean: float = Field(..., description="Average value in variant")
    variant_std: float = Field(..., ge=0, description="Standard deviation in variant")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("Revenue Test", description="Name for the summary report")
    metric_name: str = Field("Average Order Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


class MagnitudeVariant(BaseModel):
    name: str = Field(..., description="Variant name (e.g., 'control', 'variant_a')")
    visitors: int = Field(..., gt=0, description="Sample size")
    mean: float = Field(..., description="Average value")
    std: float = Field(..., ge=0, description="Standard deviation")


class MagnitudeMultiAnalyzeRequest(BaseModel):
    variants: List[MagnitudeVariant] = Field(..., min_length=2, description="List of variants")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    correction: Literal["bonferroni", "none"] = Field("bonferroni", description="Multiple comparison correction")
    test_name: str = Field("Multi-Variant Test", description="Name for the summary report")
    metric_name: str = Field("Average Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


class MagnitudeConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=1, description="Sample size")
    mean: float = Field(..., description="Sample mean")
    std: float = Field(..., ge=0, description="Standard deviation")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class ConversionDiffInDiffRequest(BaseModel):
    control_pre_visitors: int = Field(..., gt=0, description="Control group pre-period visitors")
    control_pre_conversions: int = Field(..., ge=0, description="Control group pre-period conversions")
    control_post_visitors: int = Field(..., gt=0, description="Control group post-period visitors")
    control_post_conversions: int = Field(..., ge=0, description="Control group post-period conversions")
    treatment_pre_visitors: int = Field(..., gt=0, description="Treatment group pre-period visitors")
    treatment_pre_conversions: int = Field(..., ge=0, description="Treatment group pre-period conversions")
    treatment_post_visitors: int = Field(..., gt=0, description="Treatment group post-period visitors")
    treatment_post_conversions: int = Field(..., ge=0, description="Treatment group post-period conversions")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("Difference-in-Differences Analysis", description="Name for the summary report")


class MagnitudeDiffInDiffRequest(BaseModel):
    control_pre_n: int = Field(..., gt=0, description="Control group pre-period sample size")
    control_pre_mean: float = Field(..., description="Control group pre-period mean")
    control_pre_std: float = Field(..., ge=0, description="Control group pre-period std dev")
    control_post_n: int = Field(..., gt=0, description="Control group post-period sample size")
    control_post_mean: float = Field(..., description="Control group post-period mean")
    control_post_std: float = Field(..., ge=0, description="Control group post-period std dev")
    treatment_pre_n: int = Field(..., gt=0, description="Treatment group pre-period sample size")
    treatment_pre_mean: float = Field(..., description="Treatment group pre-period mean")
    treatment_pre_std: float = Field(..., ge=0, description="Treatment group pre-period std dev")
    treatment_post_n: int = Field(..., gt=0, description="Treatment group post-period sample size")
    treatment_post_mean: float = Field(..., description="Treatment group post-period mean")
    treatment_post_std: float = Field(..., ge=0, description="Treatment group post-period std dev")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    test_name: str = Field("Difference-in-Differences Analysis", description="Name for the summary report")
    metric_name: str = Field("Average Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


# Bayesian analysis models
class BayesianAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_conversions: int = Field(..., ge=0, description="Number of conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Number of conversions in variant")
    prior_alpha: float = Field(1, gt=0, description="Beta prior alpha parameter")
    prior_beta: float = Field(1, gt=0, description="Beta prior beta parameter")
    confidence_threshold: float = Field(0.95, gt=0, le=1, description="Probability threshold for winner")


# Sequential testing models
class SequentialAnalyzeRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Number of visitors in control")
    control_conversions: int = Field(..., ge=0, description="Number of conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Number of visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Number of conversions in variant")
    expected_visitors_per_variant: int = Field(..., gt=0, description="Planned sample size per variant")
    alpha: float = Field(0.05, gt=0, lt=1, description="Significance level")
    method: Literal["obrien-fleming", "pocock"] = Field("obrien-fleming", description="Boundary method")


# Diagnostics models
class SRMCheckRequest(BaseModel):
    control_visitors: int = Field(..., ge=0, description="Visitors in control")
    variant_visitors: int = Field(..., ge=0, description="Visitors in variant")
    expected_ratio: float = Field(0.5, gt=0, lt=1, description="Expected control proportion")


class HealthCheckRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Visitors in control")
    control_conversions: int = Field(..., ge=0, description="Conversions in control")
    variant_visitors: int = Field(..., gt=0, description="Visitors in variant")
    variant_conversions: int = Field(..., ge=0, description="Conversions in variant")
    expected_visitors_per_variant: Optional[int] = Field(None, description="Planned sample size")
    test_start_date: Optional[str] = Field(None, description="Test start date (YYYY-MM-DD)")
    expected_ratio: float = Field(0.5, gt=0, lt=1, description="Expected traffic split")
    minimum_sample_per_variant: int = Field(100, gt=0, description="Minimum sample required")
    minimum_days: int = Field(7, gt=0, description="Minimum test duration")
    num_peeks: int = Field(1, ge=1, description="Number of times results checked")


class NoveltyDailyData(BaseModel):
    day: int = Field(..., description="Day number")
    control_visitors: int = Field(..., ge=0, description="Daily control visitors")
    control_conversions: int = Field(..., ge=0, description="Daily control conversions")
    variant_visitors: int = Field(..., ge=0, description="Daily variant visitors")
    variant_conversions: int = Field(..., ge=0, description="Daily variant conversions")


class NoveltyCheckRequest(BaseModel):
    daily_results: List[NoveltyDailyData] = Field(..., description="Daily test results")
    min_days: int = Field(7, gt=0, description="Minimum days for analysis")


# Segment analysis models
class SegmentData(BaseModel):
    segment_name: str = Field(..., description="Segment dimension name")
    segment_value: str = Field(..., description="Segment value")
    control_visitors: int = Field(..., ge=0, description="Control visitors in segment")
    control_conversions: int = Field(..., ge=0, description="Control conversions in segment")
    variant_visitors: int = Field(..., ge=0, description="Variant visitors in segment")
    variant_conversions: int = Field(..., ge=0, description="Variant conversions in segment")


class SegmentAnalyzeRequest(BaseModel):
    segments: List[SegmentData] = Field(..., min_length=1, description="Segment data")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")
    correction_method: Literal["bonferroni", "holm", "none"] = Field("bonferroni", description="Multiple comparison correction")
    min_sample_per_segment: int = Field(100, gt=0, description="Minimum sample per segment")


# Business impact models
class ImpactProjectionRequest(BaseModel):
    control_visitors: int = Field(..., gt=0, description="Control visitors in test")
    control_conversions: int = Field(..., ge=0, description="Control conversions in test")
    variant_visitors: int = Field(..., gt=0, description="Variant visitors in test")
    variant_conversions: int = Field(..., ge=0, description="Variant conversions in test")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")
    average_order_value: float = Field(..., gt=0, description="Average revenue per conversion")
    annual_traffic: int = Field(..., gt=0, description="Expected annual visitors")
    profit_margin: float = Field(0.3, ge=0, le=1, description="Profit margin as decimal")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/conversion/sample-size")
def conversion_sample_size(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = conversion.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return {
            "visitors_per_variant": plan.visitors_per_variant,
            "total_visitors": plan.total_visitors,
            "current_rate": plan.current_rate,
            "expected_rate": plan.expected_rate,
            "lift_percent": plan.lift_percent,
            "confidence": plan.confidence,
            "power": plan.power,
            "test_duration_days": plan.test_duration_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze")
def conversion_analyze(request: ConversionAnalyzeRequest):
    try:
        result = conversion.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        
        return {
            "control_rate": float(result.control_rate),
            "variant_rate": float(result.variant_rate),
            "lift_percent": float(result.lift_percent),
            "lift_absolute": float(result.lift_absolute),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "winner": str(result.winner),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi")
def conversion_analyze_multi(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        
        result = conversion.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        
        return {
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "test_statistic": float(result.test_statistic),
            "degrees_of_freedom": int(result.degrees_of_freedom),
            "best_variant": str(result.best_variant),
            "worst_variant": str(result.worst_variant),
            "variants": [
                {"name": str(v.name), "visitors": int(v.visitors), "conversions": int(v.conversions), "rate": float(v.rate)}
                for v in result.variants
            ],
            "pairwise_comparisons": [
                {
                    "variant_a": str(p.variant_a),
                    "variant_b": str(p.variant_b),
                    "rate_a": float(p.rate_a),
                    "rate_b": float(p.rate_b),
                    "lift_percent": float(p.lift_percent),
                    "lift_absolute": float(p.lift_absolute),
                    "p_value": float(p.p_value),
                    "p_value_adjusted": float(p.p_value_adjusted),
                    "is_significant": bool(p.is_significant),
                    "confidence_interval": [float(p.confidence_interval_lower), float(p.confidence_interval_upper)],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi/summary", response_class=PlainTextResponse)
def conversion_analyze_multi_summary(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        
        result = conversion.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        return conversion.summarize_multi(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze/summary", response_class=PlainTextResponse)
def conversion_analyze_summary(request: ConversionAnalyzeRequest):
    try:
        result = conversion.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        return conversion.summarize(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/sample-size/summary", response_class=PlainTextResponse)
def conversion_sample_size_summary(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = conversion.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return conversion.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/confidence-interval")
def conversion_confidence_interval(request: ConversionConfidenceIntervalRequest):
    try:
        result = conversion.confidence_interval(
            visitors=request.visitors,
            conversions=request.conversions,
            confidence=request.confidence,
        )
        return {
            "rate": result.rate,
            "lower": result.lower,
            "upper": result.upper,
            "confidence": result.confidence,
            "margin_of_error": result.margin_of_error,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/sample-size")
def magnitude_sample_size(request: MagnitudeSampleSizeRequest):
    try:
        plan = magnitude.sample_size(
            current_mean=request.current_mean,
            current_std=request.current_std,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return {
            "visitors_per_variant": plan.visitors_per_variant,
            "total_visitors": plan.total_visitors,
            "current_mean": plan.current_mean,
            "expected_mean": plan.expected_mean,
            "standard_deviation": plan.standard_deviation,
            "lift_percent": plan.lift_percent,
            "confidence": plan.confidence,
            "power": plan.power,
            "test_duration_days": plan.test_duration_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze")
def magnitude_analyze(request: MagnitudeAnalyzeRequest):
    try:
        result = magnitude.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        
        return {
            "control_mean": float(result.control_mean),
            "variant_mean": float(result.variant_mean),
            "lift_percent": float(result.lift_percent),
            "lift_absolute": float(result.lift_absolute),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "winner": str(result.winner),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze-multi")
def magnitude_analyze_multi(request: MagnitudeMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        
        result = magnitude.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        
        return {
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "f_statistic": float(result.f_statistic),
            "df_between": int(result.df_between),
            "df_within": int(result.df_within),
            "best_variant": str(result.best_variant),
            "worst_variant": str(result.worst_variant),
            "variants": [
                {"name": str(v.name), "visitors": int(v.visitors), "mean": float(v.mean), "std": float(v.std)}
                for v in result.variants
            ],
            "pairwise_comparisons": [
                {
                    "variant_a": str(p.variant_a),
                    "variant_b": str(p.variant_b),
                    "mean_a": float(p.mean_a),
                    "mean_b": float(p.mean_b),
                    "lift_percent": float(p.lift_percent),
                    "lift_absolute": float(p.lift_absolute),
                    "p_value": float(p.p_value),
                    "p_value_adjusted": float(p.p_value_adjusted),
                    "is_significant": bool(p.is_significant),
                    "confidence_interval": [float(p.confidence_interval_lower), float(p.confidence_interval_upper)],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze-multi/summary", response_class=PlainTextResponse)
def magnitude_analyze_multi_summary(request: MagnitudeMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        
        result = magnitude.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        return magnitude.summarize_multi(
            result,
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/analyze/summary", response_class=PlainTextResponse)
def magnitude_analyze_summary(request: MagnitudeAnalyzeRequest):
    try:
        result = magnitude.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        return magnitude.summarize(
            result, 
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/sample-size/summary", response_class=PlainTextResponse)
def magnitude_sample_size_summary(request: MagnitudeSampleSizeRequest):
    try:
        plan = magnitude.sample_size(
            current_mean=request.current_mean,
            current_std=request.current_std,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return magnitude.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/confidence-interval")
def magnitude_confidence_interval(request: MagnitudeConfidenceIntervalRequest):
    try:
        result = magnitude.confidence_interval(
            visitors=request.visitors,
            mean=request.mean,
            std=request.std,
            confidence=request.confidence,
        )
        return {
            "mean": result.mean,
            "lower": result.lower,
            "upper": result.upper,
            "confidence": result.confidence,
            "margin_of_error": result.margin_of_error,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/diff-in-diff")
def conversion_diff_in_diff(request: ConversionDiffInDiffRequest):
    try:
        result = conversion.diff_in_diff(
            control_pre_visitors=request.control_pre_visitors,
            control_pre_conversions=request.control_pre_conversions,
            control_post_visitors=request.control_post_visitors,
            control_post_conversions=request.control_post_conversions,
            treatment_pre_visitors=request.treatment_pre_visitors,
            treatment_pre_conversions=request.treatment_pre_conversions,
            treatment_post_visitors=request.treatment_post_visitors,
            treatment_post_conversions=request.treatment_post_conversions,
            confidence=request.confidence,
        )
        
        return {
            "control_pre_rate": float(result.control_pre_rate),
            "control_post_rate": float(result.control_post_rate),
            "treatment_pre_rate": float(result.treatment_pre_rate),
            "treatment_post_rate": float(result.treatment_post_rate),
            "control_change": float(result.control_change),
            "treatment_change": float(result.treatment_change),
            "diff_in_diff": float(result.diff_in_diff),
            "diff_in_diff_percent": float(result.diff_in_diff_percent),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "z_statistic": float(result.z_statistic),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/diff-in-diff/summary", response_class=PlainTextResponse)
def conversion_diff_in_diff_summary(request: ConversionDiffInDiffRequest):
    try:
        result = conversion.diff_in_diff(
            control_pre_visitors=request.control_pre_visitors,
            control_pre_conversions=request.control_pre_conversions,
            control_post_visitors=request.control_post_visitors,
            control_post_conversions=request.control_post_conversions,
            treatment_pre_visitors=request.treatment_pre_visitors,
            treatment_pre_conversions=request.treatment_pre_conversions,
            treatment_post_visitors=request.treatment_post_visitors,
            treatment_post_conversions=request.treatment_post_conversions,
            confidence=request.confidence,
        )
        return conversion.summarize_diff_in_diff(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/diff-in-diff")
def magnitude_diff_in_diff(request: MagnitudeDiffInDiffRequest):
    try:
        result = magnitude.diff_in_diff(
            control_pre_n=request.control_pre_n,
            control_pre_mean=request.control_pre_mean,
            control_pre_std=request.control_pre_std,
            control_post_n=request.control_post_n,
            control_post_mean=request.control_post_mean,
            control_post_std=request.control_post_std,
            treatment_pre_n=request.treatment_pre_n,
            treatment_pre_mean=request.treatment_pre_mean,
            treatment_pre_std=request.treatment_pre_std,
            treatment_post_n=request.treatment_post_n,
            treatment_post_mean=request.treatment_post_mean,
            treatment_post_std=request.treatment_post_std,
            confidence=request.confidence,
        )
        
        return {
            "control_pre_mean": float(result.control_pre_mean),
            "control_post_mean": float(result.control_post_mean),
            "treatment_pre_mean": float(result.treatment_pre_mean),
            "treatment_post_mean": float(result.treatment_post_mean),
            "control_change": float(result.control_change),
            "treatment_change": float(result.treatment_change),
            "diff_in_diff": float(result.diff_in_diff),
            "diff_in_diff_percent": float(result.diff_in_diff_percent),
            "is_significant": bool(result.is_significant),
            "confidence": int(result.confidence),
            "p_value": float(result.p_value),
            "t_statistic": float(result.t_statistic),
            "degrees_of_freedom": float(result.degrees_of_freedom),
            "confidence_interval": [float(result.confidence_interval_lower), float(result.confidence_interval_upper)],
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/magnitude/diff-in-diff/summary", response_class=PlainTextResponse)
def magnitude_diff_in_diff_summary(request: MagnitudeDiffInDiffRequest):
    try:
        result = magnitude.diff_in_diff(
            control_pre_n=request.control_pre_n,
            control_pre_mean=request.control_pre_mean,
            control_pre_std=request.control_pre_std,
            control_post_n=request.control_post_n,
            control_post_mean=request.control_post_mean,
            control_post_std=request.control_post_std,
            treatment_pre_n=request.treatment_pre_n,
            treatment_pre_mean=request.treatment_pre_mean,
            treatment_pre_std=request.treatment_pre_std,
            treatment_post_n=request.treatment_post_n,
            treatment_post_mean=request.treatment_post_mean,
            treatment_post_std=request.treatment_post_std,
            confidence=request.confidence,
        )
        return magnitude.summarize_diff_in_diff(
            result,
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TimingAnalyzeRequest(BaseModel):
    control_times: List[float] = Field(..., description="Time values for control group")
    control_events: List[int] = Field(..., description="Event indicators for control (1=event, 0=censored)")
    treatment_times: List[float] = Field(..., description="Time values for treatment group")
    treatment_events: List[int] = Field(..., description="Event indicators for treatment (1=event, 0=censored)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class TimingSampleSizeRequest(BaseModel):
    control_median: float = Field(..., description="Expected median time for control group")
    treatment_median: float = Field(..., description="Expected median time for treatment group")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")
    power: int = Field(80, ge=50, le=99, description="Statistical power")
    dropout_rate: float = Field(0.1, ge=0, lt=1, description="Expected dropout/censoring rate")


class TimingSurvivalCurveRequest(BaseModel):
    times: List[float] = Field(..., description="Time values")
    events: List[int] = Field(..., description="Event indicators (1=event, 0=censored)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class TimingRateAnalyzeRequest(BaseModel):
    control_events: int = Field(..., ge=0, description="Number of events in control group")
    control_exposure: float = Field(..., gt=0, description="Total exposure time for control group")
    treatment_events: int = Field(..., ge=0, description="Number of events in treatment group")
    treatment_exposure: float = Field(..., gt=0, description="Total exposure time for treatment group")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


class TimingSummaryRequest(BaseModel):
    control_times: List[float]
    control_events: List[int]
    treatment_times: List[float]
    treatment_events: List[int]
    confidence: int = Field(95)
    test_name: str = Field("Timing Effect Test")


class TimingRateSummaryRequest(BaseModel):
    control_events: int
    control_exposure: float
    treatment_events: int
    treatment_exposure: float
    confidence: int = Field(95)
    test_name: str = Field("Event Rate Test")
    unit: str = Field("events per day")


@app.post("/api/timing/analyze")
def timing_analyze(request: TimingAnalyzeRequest):
    try:
        result = timing.analyze(
            control_times=request.control_times,
            control_events=request.control_events,
            treatment_times=request.treatment_times,
            treatment_events=request.treatment_events,
            confidence=request.confidence,
        )
        return {
            "control_median_time": result.control_median_time,
            "treatment_median_time": result.treatment_median_time,
            "control_events": result.control_events,
            "control_censored": result.control_censored,
            "treatment_events": result.treatment_events,
            "treatment_censored": result.treatment_censored,
            "hazard_ratio": float(result.hazard_ratio),
            "hazard_ratio_ci": [float(result.hazard_ratio_ci_lower), float(result.hazard_ratio_ci_upper)],
            "time_saved": result.time_saved,
            "time_saved_percent": result.time_saved_percent,
            "is_significant": bool(result.is_significant),
            "confidence": result.confidence,
            "p_value": float(result.p_value),
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/analyze/summary")
def timing_analyze_summary(request: TimingSummaryRequest):
    try:
        result = timing.analyze(
            control_times=request.control_times,
            control_events=request.control_events,
            treatment_times=request.treatment_times,
            treatment_events=request.treatment_events,
            confidence=request.confidence,
        )
        return PlainTextResponse(timing.summarize(result, test_name=request.test_name))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/sample-size")
def timing_sample_size(request: TimingSampleSizeRequest):
    try:
        plan = timing.sample_size(
            control_median=request.control_median,
            treatment_median=request.treatment_median,
            confidence=request.confidence,
            power=request.power,
            dropout_rate=request.dropout_rate,
        )
        return {
            "subjects_per_group": plan.subjects_per_group,
            "total_subjects": plan.total_subjects,
            "expected_events_per_group": plan.expected_events_per_group,
            "total_expected_events": plan.total_expected_events,
            "control_median": plan.control_median,
            "treatment_median": plan.treatment_median,
            "hazard_ratio": float(plan.hazard_ratio),
            "confidence": plan.confidence,
            "power": plan.power,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/survival-curve")
def timing_survival_curve(request: TimingSurvivalCurveRequest):
    try:
        curve = timing.survival_curve(
            times=request.times,
            events=request.events,
            confidence=request.confidence,
        )
        return {
            "times": curve.times,
            "survival_probabilities": curve.survival_probabilities,
            "confidence_lower": curve.confidence_lower,
            "confidence_upper": curve.confidence_upper,
            "median_time": curve.median_time,
            "events": curve.events,
            "censored": curve.censored,
            "total": curve.total,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/rates/analyze")
def timing_rate_analyze(request: TimingRateAnalyzeRequest):
    try:
        result = timing.analyze_rates(
            control_events=request.control_events,
            control_exposure=request.control_exposure,
            treatment_events=request.treatment_events,
            treatment_exposure=request.treatment_exposure,
            confidence=request.confidence,
        )
        return {
            "control_rate": float(result.control_rate),
            "treatment_rate": float(result.treatment_rate),
            "control_events": result.control_events,
            "control_exposure": float(result.control_exposure),
            "treatment_events": result.treatment_events,
            "treatment_exposure": float(result.treatment_exposure),
            "rate_ratio": float(result.rate_ratio),
            "rate_ratio_ci": [float(result.rate_ratio_ci_lower), float(result.rate_ratio_ci_upper)],
            "rate_difference": float(result.rate_difference),
            "rate_difference_percent": float(result.rate_difference_percent),
            "is_significant": bool(result.is_significant),
            "confidence": result.confidence,
            "p_value": float(result.p_value),
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/timing/rates/analyze/summary")
def timing_rate_analyze_summary(request: TimingRateSummaryRequest):
    try:
        result = timing.analyze_rates(
            control_events=request.control_events,
            control_exposure=request.control_exposure,
            treatment_events=request.treatment_events,
            treatment_exposure=request.treatment_exposure,
            confidence=request.confidence,
        )
        return PlainTextResponse(timing.summarize_rates(result, test_name=request.test_name, unit=request.unit))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bayesian A/B Testing endpoints
@app.post("/api/bayesian/analyze")
def bayesian_analyze(request: BayesianAnalyzeRequest):
    try:
        result = bayesian.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            prior_alpha=request.prior_alpha,
            prior_beta=request.prior_beta,
            confidence_threshold=request.confidence_threshold,
        )
        return {
            "control_rate": float(result.control_rate),
            "variant_rate": float(result.variant_rate),
            "probability_variant_better": float(result.probability_variant_better),
            "probability_control_better": float(result.probability_control_better),
            "expected_loss_choosing_variant": float(result.expected_loss_choosing_variant),
            "expected_loss_choosing_control": float(result.expected_loss_choosing_control),
            "control_credible_interval": [float(result.control_credible_interval[0]), float(result.control_credible_interval[1])],
            "variant_credible_interval": [float(result.variant_credible_interval[0]), float(result.variant_credible_interval[1])],
            "lift_credible_interval": [float(result.lift_credible_interval[0]), float(result.lift_credible_interval[1])],
            "lift_percent": float(result.lift_percent),
            "has_winner": bool(result.has_winner),
            "winner": str(result.winner),
            "confidence_threshold": float(result.confidence_threshold),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Sequential Testing endpoints
@app.post("/api/sequential/analyze")
def sequential_analyze(request: SequentialAnalyzeRequest):
    try:
        result = sequential.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            expected_visitors_per_variant=request.expected_visitors_per_variant,
            alpha=request.alpha,
            method=request.method,
        )
        return {
            "control_rate": float(result.control_rate),
            "variant_rate": float(result.variant_rate),
            "can_stop": bool(result.can_stop),
            "decision": str(result.decision),
            "lift_percent": float(result.lift_percent),
            "z_statistic": float(result.z_statistic),
            "p_value": float(result.p_value),
            "upper_boundary": float(result.upper_boundary),
            "lower_boundary": float(result.lower_boundary),
            "current_statistic": float(result.current_statistic),
            "confidence_variant_better": float(result.confidence_variant_better),
            "confidence_control_better": float(result.confidence_control_better),
            "adjusted_alpha": float(result.adjusted_alpha),
            "information_fraction": float(result.information_fraction),
            "estimated_remaining_visitors": result.estimated_remaining_visitors,
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Diagnostics endpoints
@app.post("/api/diagnostics/srm")
def check_srm(request: SRMCheckRequest):
    try:
        result = srm.check_sample_ratio(
            control_visitors=request.control_visitors,
            variant_visitors=request.variant_visitors,
            expected_ratio=request.expected_ratio,
        )
        return {
            "observed_ratio": float(result.observed_ratio),
            "is_valid": bool(result.is_valid),
            "p_value": float(result.p_value),
            "chi2_statistic": float(result.chi2_statistic),
            "severity": str(result.severity),
            "deviation_percent": float(result.deviation_percent),
            "warning": str(result.warning),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/diagnostics/health")
def check_test_health(request: HealthCheckRequest):
    try:
        result = health.check_health(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            expected_visitors_per_variant=request.expected_visitors_per_variant,
            test_start_date=request.test_start_date,
            expected_ratio=request.expected_ratio,
            minimum_sample_per_variant=request.minimum_sample_per_variant,
            minimum_days=request.minimum_days,
            num_peeks=request.num_peeks,
        )
        return {
            "overall_status": str(result.overall_status),
            "score": int(result.score),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details,
                }
                for check in result.checks
            ],
            "total_visitors": result.total_visitors,
            "test_duration_days": result.test_duration_days,
            "can_trust_results": bool(result.can_trust_results),
            "primary_issues": result.primary_issues,
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/diagnostics/novelty")
def check_novelty_effect(request: NoveltyCheckRequest):
    try:
        daily_data = [
            {
                "day": d.day,
                "control_visitors": d.control_visitors,
                "control_conversions": d.control_conversions,
                "variant_visitors": d.variant_visitors,
                "variant_conversions": d.variant_conversions,
            }
            for d in request.daily_results
        ]
        result = novelty.detect_novelty_effect(
            daily_results=daily_data,
            min_days=request.min_days,
        )
        return {
            "effect_detected": bool(result.effect_detected),
            "effect_type": str(result.effect_type),
            "initial_lift": float(result.initial_lift),
            "current_lift": float(result.current_lift),
            "trend_slope": float(result.trend_slope),
            "trend_p_value": float(result.trend_p_value),
            "projected_steady_state_lift": result.projected_steady_state_lift,
            "days_to_steady_state": result.days_to_steady_state,
            "confidence": float(result.confidence),
            "daily_lifts": result.daily_lifts,
            "smoothed_lifts": result.smoothed_lifts,
            "warning": str(result.warning),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Segment Analysis endpoints
@app.post("/api/segments/analyze")
def analyze_segments(request: SegmentAnalyzeRequest):
    try:
        segments_data = [
            {
                "segment_name": s.segment_name,
                "segment_value": s.segment_value,
                "control_visitors": s.control_visitors,
                "control_conversions": s.control_conversions,
                "variant_visitors": s.variant_visitors,
                "variant_conversions": s.variant_conversions,
            }
            for s in request.segments
        ]
        result = segment_analysis.analyze_segments(
            segments_data=segments_data,
            confidence=request.confidence,
            correction_method=request.correction_method,
            min_sample_per_segment=request.min_sample_per_segment,
        )
        return {
            "overall_lift": float(result.overall_lift),
            "overall_is_significant": bool(result.overall_is_significant),
            "segments": [
                {
                    "segment_name": seg.segment_name,
                    "segment_value": seg.segment_value,
                    "control_visitors": seg.control_visitors,
                    "control_conversions": seg.control_conversions,
                    "variant_visitors": seg.variant_visitors,
                    "variant_conversions": seg.variant_conversions,
                    "control_rate": float(seg.control_rate),
                    "variant_rate": float(seg.variant_rate),
                    "lift_percent": float(seg.lift_percent),
                    "lift_ci_lower": float(seg.lift_ci_lower),
                    "lift_ci_upper": float(seg.lift_ci_upper),
                    "p_value": float(seg.p_value),
                    "is_significant": bool(seg.is_significant),
                    "winner": str(seg.winner),
                    "sample_size_adequate": bool(seg.sample_size_adequate),
                }
                for seg in result.segments
            ],
            "n_segments": result.n_segments,
            "best_segment": result.best_segment,
            "worst_segment": result.worst_segment,
            "heterogeneity_detected": bool(result.heterogeneity_detected),
            "simpsons_paradox_risk": bool(result.simpsons_paradox_risk),
            "correction_method": str(result.correction_method),
            "adjusted_alpha": float(result.adjusted_alpha),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Business Impact endpoints
@app.post("/api/business/impact")
def project_business_impact(request: ImpactProjectionRequest):
    try:
        # Calculate rates and lift from raw data
        control_rate = request.control_conversions / request.control_visitors if request.control_visitors > 0 else 0
        variant_rate = request.variant_conversions / request.variant_visitors if request.variant_visitors > 0 else 0
        lift_percent = ((variant_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0

        # Calculate confidence interval for lift
        import math
        from scipy.stats import norm

        alpha = 1 - request.confidence / 100
        z = norm.ppf(1 - alpha / 2)

        se_c = math.sqrt(control_rate * (1 - control_rate) / request.control_visitors) if request.control_visitors > 0 and 0 < control_rate < 1 else 0
        se_v = math.sqrt(variant_rate * (1 - variant_rate) / request.variant_visitors) if request.variant_visitors > 0 and 0 < variant_rate < 1 else 0
        se_diff = math.sqrt(se_c**2 + se_v**2)

        diff = variant_rate - control_rate
        diff_lower = diff - z * se_diff
        diff_upper = diff + z * se_diff

        lift_ci_lower = (diff_lower / control_rate * 100) if control_rate > 0 else 0
        lift_ci_upper = (diff_upper / control_rate * 100) if control_rate > 0 else 0

        # Calculate monthly visitors from annual
        monthly_visitors = request.annual_traffic // 12

        result = impact.project_impact(
            control_rate=control_rate,
            variant_rate=variant_rate,
            lift_percent=lift_percent,
            lift_ci_lower=lift_ci_lower,
            lift_ci_upper=lift_ci_upper,
            monthly_visitors=monthly_visitors,
            revenue_per_conversion=request.average_order_value,
            confidence=request.confidence,
        )

        # Calculate additional metrics
        additional_conversions = int(result.annual_additional_conversions)
        additional_revenue = float(result.annual_revenue_lift)
        additional_profit = float(additional_revenue * request.profit_margin)

        # Check significance
        is_significant = bool(lift_ci_lower > 0 or lift_ci_upper < 0)

        return {
            "is_significant": is_significant,
            "lift_percent": float(lift_percent),
            "additional_conversions": additional_conversions,
            "additional_revenue": additional_revenue,
            "additional_profit": additional_profit,
            "roi_percent": float(additional_profit / max(additional_revenue, 1) * 100) if additional_revenue != 0 else 0.0,
            "confidence": request.confidence,
            "confidence_interval": {
                "revenue_lower": float(result.revenue_lift_range[0]),
                "revenue_upper": float(result.revenue_lift_range[1]),
            },
            "probability_positive": float(result.probability_positive_impact),
            "recommendation": str(result.recommendation),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
