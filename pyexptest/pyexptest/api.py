from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
import os

from pyexptest import conversion_effect, numeric_effect

app = FastAPI(
    title="pyexptest API",
    description="Simple A/B testing tools for marketers and analysts",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class NumericSampleSizeRequest(BaseModel):
    current_mean: float = Field(..., description="Current average value (e.g., $50)")
    current_std: float = Field(..., gt=0, description="Standard deviation")
    lift_percent: float = Field(5, description="Minimum lift to detect in % (e.g., 5 for 5%)")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    power: int = Field(80, ge=50, le=99, description="Statistical power (50-99)")
    daily_visitors: Optional[int] = Field(None, gt=0, description="Optional: daily traffic for duration estimate")
    num_variants: int = Field(2, ge=2, le=10, description="Number of variants including control")


class NumericAnalyzeRequest(BaseModel):
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


class NumericVariant(BaseModel):
    name: str = Field(..., description="Variant name (e.g., 'control', 'variant_a')")
    visitors: int = Field(..., gt=0, description="Sample size")
    mean: float = Field(..., description="Average value")
    std: float = Field(..., ge=0, description="Standard deviation")


class NumericMultiAnalyzeRequest(BaseModel):
    variants: List[NumericVariant] = Field(..., min_length=2, description="List of variants")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level (80-99)")
    correction: Literal["bonferroni", "none"] = Field("bonferroni", description="Multiple comparison correction")
    test_name: str = Field("Multi-Variant Test", description="Name for the summary report")
    metric_name: str = Field("Average Value", description="Name of the metric")
    currency: str = Field("$", description="Currency symbol")


class NumericConfidenceIntervalRequest(BaseModel):
    visitors: int = Field(..., gt=1, description="Sample size")
    mean: float = Field(..., description="Sample mean")
    std: float = Field(..., ge=0, description="Standard deviation")
    confidence: int = Field(95, ge=80, le=99, description="Confidence level")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/conversion/sample-size")
def conversion_sample_size(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = conversion_effect.sample_size(
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
        result = conversion_effect.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        
        return {
            "control_rate": result.control_rate,
            "variant_rate": result.variant_rate,
            "lift_percent": result.lift_percent,
            "lift_absolute": result.lift_absolute,
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "confidence_interval": [result.confidence_interval_lower, result.confidence_interval_upper],
            "winner": result.winner,
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi")
def conversion_analyze_multi(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        
        result = conversion_effect.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        
        return {
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "test_statistic": result.test_statistic,
            "degrees_of_freedom": result.degrees_of_freedom,
            "best_variant": result.best_variant,
            "worst_variant": result.worst_variant,
            "variants": [
                {"name": v.name, "visitors": v.visitors, "conversions": v.conversions, "rate": v.rate}
                for v in result.variants
            ],
            "pairwise_comparisons": [
                {
                    "variant_a": p.variant_a,
                    "variant_b": p.variant_b,
                    "rate_a": p.rate_a,
                    "rate_b": p.rate_b,
                    "lift_percent": p.lift_percent,
                    "lift_absolute": p.lift_absolute,
                    "p_value": p.p_value,
                    "p_value_adjusted": p.p_value_adjusted,
                    "is_significant": p.is_significant,
                    "confidence_interval": [p.confidence_interval_lower, p.confidence_interval_upper],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze-multi/summary", response_class=PlainTextResponse)
def conversion_analyze_multi_summary(request: ConversionMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "conversions": v.conversions} for v in request.variants]
        
        result = conversion_effect.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        return conversion_effect.summarize_multi(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/analyze/summary", response_class=PlainTextResponse)
def conversion_analyze_summary(request: ConversionAnalyzeRequest):
    try:
        result = conversion_effect.analyze(
            control_visitors=request.control_visitors,
            control_conversions=request.control_conversions,
            variant_visitors=request.variant_visitors,
            variant_conversions=request.variant_conversions,
            confidence=request.confidence,
        )
        return conversion_effect.summarize(result, test_name=request.test_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/sample-size/summary", response_class=PlainTextResponse)
def conversion_sample_size_summary(request: ConversionSampleSizeRequest):
    try:
        rate = request.current_rate
        if rate > 1:
            rate = rate / 100
        
        plan = conversion_effect.sample_size(
            current_rate=rate,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return conversion_effect.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/conversion/confidence-interval")
def conversion_confidence_interval(request: ConversionConfidenceIntervalRequest):
    try:
        result = conversion_effect.confidence_interval(
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


@app.post("/api/numeric/sample-size")
def numeric_sample_size(request: NumericSampleSizeRequest):
    try:
        plan = numeric_effect.sample_size(
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


@app.post("/api/numeric/analyze")
def numeric_analyze(request: NumericAnalyzeRequest):
    try:
        result = numeric_effect.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        
        return {
            "control_mean": result.control_mean,
            "variant_mean": result.variant_mean,
            "lift_percent": result.lift_percent,
            "lift_absolute": result.lift_absolute,
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "confidence_interval": [result.confidence_interval_lower, result.confidence_interval_upper],
            "winner": result.winner,
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/numeric/analyze-multi")
def numeric_analyze_multi(request: NumericMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        
        result = numeric_effect.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        
        return {
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "p_value": result.p_value,
            "f_statistic": result.f_statistic,
            "df_between": result.df_between,
            "df_within": result.df_within,
            "best_variant": result.best_variant,
            "worst_variant": result.worst_variant,
            "variants": [
                {"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std}
                for v in result.variants
            ],
            "pairwise_comparisons": [
                {
                    "variant_a": p.variant_a,
                    "variant_b": p.variant_b,
                    "mean_a": p.mean_a,
                    "mean_b": p.mean_b,
                    "lift_percent": p.lift_percent,
                    "lift_absolute": p.lift_absolute,
                    "p_value": p.p_value,
                    "p_value_adjusted": p.p_value_adjusted,
                    "is_significant": p.is_significant,
                    "confidence_interval": [p.confidence_interval_lower, p.confidence_interval_upper],
                }
                for p in result.pairwise_comparisons
            ],
            "recommendation": result.recommendation,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/numeric/analyze-multi/summary", response_class=PlainTextResponse)
def numeric_analyze_multi_summary(request: NumericMultiAnalyzeRequest):
    try:
        variants = [{"name": v.name, "visitors": v.visitors, "mean": v.mean, "std": v.std} for v in request.variants]
        
        result = numeric_effect.analyze_multi(
            variants=variants,
            confidence=request.confidence,
            correction=request.correction,
        )
        return numeric_effect.summarize_multi(
            result,
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/numeric/analyze/summary", response_class=PlainTextResponse)
def numeric_analyze_summary(request: NumericAnalyzeRequest):
    try:
        result = numeric_effect.analyze(
            control_visitors=request.control_visitors,
            control_mean=request.control_mean,
            control_std=request.control_std,
            variant_visitors=request.variant_visitors,
            variant_mean=request.variant_mean,
            variant_std=request.variant_std,
            confidence=request.confidence,
        )
        return numeric_effect.summarize(
            result, 
            test_name=request.test_name,
            metric_name=request.metric_name,
            currency=request.currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/numeric/sample-size/summary", response_class=PlainTextResponse)
def numeric_sample_size_summary(request: NumericSampleSizeRequest):
    try:
        plan = numeric_effect.sample_size(
            current_mean=request.current_mean,
            current_std=request.current_std,
            lift_percent=request.lift_percent,
            confidence=request.confidence,
            power=request.power,
            num_variants=request.num_variants,
        )
        
        if request.daily_visitors:
            plan.with_daily_traffic(request.daily_visitors)
        
        return numeric_effect.summarize_plan(plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/numeric/confidence-interval")
def numeric_confidence_interval(request: NumericConfidenceIntervalRequest):
    try:
        result = numeric_effect.confidence_interval(
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
