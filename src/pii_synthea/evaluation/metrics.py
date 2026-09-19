"""
Span-level Evaluation Metrics and Statistics Engine.
Supports Strict (Exact Match) and Boundary-Relaxed (Partial Overlap / IoU) evaluations,
along with tw-PII-bench specialized OOD detection/generalization and hard negative false positive rates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


class EvaluationMode(str, Enum):
    """Span evaluation matching modes."""
    STRICT = "strict"    # Exact Match: start == start, end == end, label == label
    RELAXED = "relaxed"  # Boundary-Relaxed: label == label, IoU >= threshold


@dataclass(frozen=True)
class Span:
    """Represents an extracted or ground-truth entity span."""
    start: int
    end: int
    label: str
    text: Optional[str] = None
    score: Optional[float] = None
    expected_model_label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"Invalid span offsets: [{self.start}, {self.end}]")

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass
class MetricScore:
    """Standard classification and span extraction metrics."""
    tp: int = 0
    fp: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


@dataclass
class CategoryMetric:
    """Detailed metrics for a specific PII label category."""
    name: str
    total_gold: int
    strict: MetricScore = field(default_factory=MetricScore)
    relaxed: MetricScore = field(default_factory=MetricScore)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_gold": self.total_gold,
            "strict": self.strict.to_dict(),
            "relaxed": self.relaxed.to_dict(),
        }


@dataclass
class OODMetric:
    """
    Evaluation metrics for Out-of-Distribution (OOD) Taiwan-specific PII.
    Tracks detection rate (any prediction overlap) and generalization rate (fallback match).
    """
    label: str
    expected_fallback: Optional[str]
    total: int = 0
    correct: int = 0          # Prediction label == expected_fallback (or direct target)
    wrong_label: int = 0      # Prediction overlap exists, but label != expected_fallback
    missed: int = 0           # No overlapping prediction
    detection_rate: float = 0.0
    generalization_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "expected_fallback": self.expected_fallback,
            "total": self.total,
            "correct": self.correct,
            "wrong_label": self.wrong_label,
            "missed": self.missed,
            "detection_rate": round(self.detection_rate, 4),
            "generalization_rate": round(self.generalization_rate, 4),
        }


@dataclass
class HardNegativeMetric:
    """Tracks false positive behavior on hard negative texts (where true spans == 0)."""
    subtype: str
    total_items: int = 0
    fps: int = 0
    fp_per_item: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subtype": self.subtype,
            "total_items": self.total_items,
            "fps": self.fps,
            "fp_per_item": round(self.fp_per_item, 4),
        }


@dataclass
class SplitEvaluationReport:
    """Complete evaluation report for a single split (short, mid, long, or overall)."""
    split: str
    total_items: int = 0
    in_schema_metrics: Dict[str, CategoryMetric] = field(default_factory=dict)
    in_schema_strict_micro: MetricScore = field(default_factory=MetricScore)
    in_schema_strict_macro: MetricScore = field(default_factory=MetricScore)
    in_schema_relaxed_micro: MetricScore = field(default_factory=MetricScore)
    in_schema_relaxed_macro: MetricScore = field(default_factory=MetricScore)
    
    ood_metrics: Dict[str, OODMetric] = field(default_factory=dict)
    ood_total_spans: int = 0
    ood_overall_detection_rate: float = 0.0
    ood_overall_generalization_rate: float = 0.0
    
    hard_negative_metrics: Dict[str, HardNegativeMetric] = field(default_factory=dict)
    hard_negative_total_items: int = 0
    hard_negative_total_fps: int = 0
    hard_negative_fp_per_item: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "split": self.split,
            "total_items": self.total_items,
            "in_schema": {
                "categories": {k: v.to_dict() for k, v in self.in_schema_metrics.items()},
                "strict_micro": self.in_schema_strict_micro.to_dict(),
                "strict_macro": self.in_schema_strict_macro.to_dict(),
                "relaxed_micro": self.in_schema_relaxed_micro.to_dict(),
                "relaxed_macro": self.in_schema_relaxed_macro.to_dict(),
            },
            "out_of_schema": {
                "categories": {k: v.to_dict() for k, v in self.ood_metrics.items()},
                "total_spans": self.ood_total_spans,
                "overall_detection_rate": round(self.ood_overall_detection_rate, 4),
                "overall_generalization_rate": round(self.ood_overall_generalization_rate, 4),
            },
            "hard_negatives": {
                "subtypes": {k: v.to_dict() for k, v in self.hard_negative_metrics.items()},
                "total_items": self.hard_negative_total_items,
                "total_fps": self.hard_negative_total_fps,
                "fp_per_item": round(self.hard_negative_fp_per_item, 4),
            },
        }


@dataclass
class BenchmarkEvaluationResult:
    """Aggregated benchmark evaluation result across all splits and metrics."""
    model_name: str
    evaluation_date: str
    iou_threshold: float
    score_threshold: float
    splits: Dict[str, SplitEvaluationReport] = field(default_factory=dict)
    overall: Optional[SplitEvaluationReport] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "evaluation_date": self.evaluation_date,
            "iou_threshold": self.iou_threshold,
            "score_threshold": self.score_threshold,
            "splits": {k: v.to_dict() for k, v in self.splits.items()},
            "overall": self.overall.to_dict() if self.overall else None,
        }


def compute_span_iou(
    start1: int, end1: int, start2: int, end2: int
) -> float:
    """Computes character-level Intersection over Union (IoU) between two spans."""
    inter_start = max(start1, start2)
    inter_end = min(end1, end2)
    inter_len = max(0, inter_end - inter_start)
    if inter_len <= 0:
        return 0.0
    union_start = min(start1, start2)
    union_end = max(end1, end2)
    union_len = union_end - union_start
    return inter_len / union_len if union_len > 0 else 0.0


def compute_metric_score(tp: int, fp: int, fn: int) -> MetricScore:
    """Calculates Precision, Recall, and F1 score with zero-division handling."""
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    return MetricScore(tp=tp, fp=fp, fn=fn, precision=prec, recall=rec, f1=f1)


def match_spans_for_category(
    gold_spans: Sequence[Span],
    pred_spans: Sequence[Span],
    mode: EvaluationMode,
    iou_threshold: float = 0.5,
) -> Tuple[int, int, int]:
    """
    Performs greedy 1-to-1 bipartite matching for a specific entity category.
    Returns (TP, FP, FN).
    """
    matched_gold_indices: Set[int] = set()
    matched_pred_indices: Set[int] = set()

    # Find candidate matches
    candidates: List[Tuple[float, int, int]] = []
    for p_idx, p in enumerate(pred_spans):
        for g_idx, g in enumerate(gold_spans):
            if mode == EvaluationMode.STRICT:
                if p.start == g.start and p.end == g.end:
                    candidates.append((1.0, p_idx, g_idx))
            else:
                iou = compute_span_iou(p.start, p.end, g.start, g.end)
                if iou >= iou_threshold:
                    candidates.append((iou, p_idx, g_idx))

    # Sort matches by highest IoU first
    candidates.sort(key=lambda x: x[0], reverse=True)

    for iou_score, p_idx, g_idx in candidates:
        if p_idx not in matched_pred_indices and g_idx not in matched_gold_indices:
            matched_pred_indices.add(p_idx)
            matched_gold_indices.add(g_idx)

    tp = len(matched_gold_indices)
    fn = len(gold_spans) - tp
    fp = len(pred_spans) - len(matched_pred_indices)
    return tp, fp, fn
