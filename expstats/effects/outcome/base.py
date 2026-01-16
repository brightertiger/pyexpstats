from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal


@dataclass
class EffectResult(ABC):
    is_significant: bool
    confidence: int
    p_value: float
    recommendation: str


@dataclass
class SampleSizePlanBase(ABC):
    subjects_per_group: int
    total_subjects: int
    confidence: int
    power: int
    test_duration_days: Optional[int] = None
    
    def with_daily_traffic(self, daily_visitors: int) -> 'SampleSizePlanBase':
        if daily_visitors > 0:
            import math
            self.test_duration_days = math.ceil(self.total_subjects / daily_visitors)
        return self


@dataclass
class ConfidenceIntervalBase(ABC):
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence: int
    margin_of_error: float


@dataclass
class PairwiseComparisonBase(ABC):
    variant_a: str
    variant_b: str
    difference: float
    p_value: float
    p_value_adjusted: float
    is_significant: bool


@dataclass
class MultiVariantResultBase(EffectResult):
    best_variant: str
    worst_variant: str
    pairwise_comparisons: List[PairwiseComparisonBase]


@dataclass
class DiffInDiffResultBase(EffectResult):
    control_change: float
    treatment_change: float
    diff_in_diff: float
    diff_in_diff_percent: float


class OutcomeEffectAnalyzer(ABC):
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> EffectResult:
        pass
    
    @abstractmethod
    def sample_size(self, *args, **kwargs) -> SampleSizePlanBase:
        pass
    
    @abstractmethod
    def summarize(self, result: EffectResult, test_name: str = "A/B Test") -> str:
        pass


class OutcomeEffectWithCI(OutcomeEffectAnalyzer):
    
    @abstractmethod
    def confidence_interval(self, *args, **kwargs) -> ConfidenceIntervalBase:
        pass


class MultiVariantAnalyzer(ABC):
    
    @abstractmethod
    def analyze_multi(self, variants: List[Dict[str, Any]], confidence: int = 95) -> MultiVariantResultBase:
        pass
    
    @abstractmethod
    def summarize_multi(self, result: MultiVariantResultBase, test_name: str = "Multi-Variant Test") -> str:
        pass


class DiffInDiffAnalyzer(ABC):
    
    @abstractmethod
    def diff_in_diff(self, *args, **kwargs) -> DiffInDiffResultBase:
        pass
    
    @abstractmethod
    def summarize_diff_in_diff(self, result: DiffInDiffResultBase, test_name: str = "DiD Analysis") -> str:
        pass


class FullOutcomeEffect(OutcomeEffectWithCI, MultiVariantAnalyzer, DiffInDiffAnalyzer):
    pass
