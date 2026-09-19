"""
PII-Synthea Evaluation & Benchmark Harness Subsystem.
Provides full evaluation, metrics calculation, and comparative reporting against lianghsun/tw-PII-bench.
"""

from pii_synthea.evaluation.benchmark_dataset import (
    HARD_NEGATIVE_SUBTYPES,
    IN_SCHEMA_BENCH_LABELS,
    OOD_BENCH_LABELS_WITH_FALLBACK,
    BenchmarkDatasetLoader,
    BenchmarkItem,
)
from pii_synthea.evaluation.harness import (
    BasePredictor,
    BaselineSimulationPredictor,
    EvaluationConfig,
    EvaluationHarness,
    FineTunedSimulationPredictor,
    GLiNER2Predictor,
    compare_evaluations,
)
from pii_synthea.evaluation.metrics import (
    BenchmarkEvaluationResult,
    CategoryMetric,
    EvaluationMode,
    HardNegativeMetric,
    MetricScore,
    OODMetric,
    Span,
    SplitEvaluationReport,
    compute_metric_score,
    compute_span_iou,
    match_spans_for_category,
)
from pii_synthea.evaluation.reporter import BenchmarkReporter

__all__ = [
    "Span",
    "EvaluationMode",
    "MetricScore",
    "CategoryMetric",
    "OODMetric",
    "HardNegativeMetric",
    "SplitEvaluationReport",
    "BenchmarkEvaluationResult",
    "compute_span_iou",
    "compute_metric_score",
    "match_spans_for_category",
    "BenchmarkItem",
    "BenchmarkDatasetLoader",
    "IN_SCHEMA_BENCH_LABELS",
    "OOD_BENCH_LABELS_WITH_FALLBACK",
    "HARD_NEGATIVE_SUBTYPES",
    "EvaluationConfig",
    "BasePredictor",
    "GLiNER2Predictor",
    "BaselineSimulationPredictor",
    "FineTunedSimulationPredictor",
    "EvaluationHarness",
    "compare_evaluations",
    "BenchmarkReporter",
]
