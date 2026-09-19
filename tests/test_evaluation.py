"""
Unit test suite for GLiNER2 Taiwan PII Benchmark Evaluation Subsystem (Ticket 07).
Validates span metrics (strict and relaxed IoU), benchmark dataset loading,
OOD diagnosis, hard negative scoring, comparative reporting, and CLI integration.
"""

import json
from pathlib import Path
import pytest

from pii_synthea.evaluation import (
    BaselineSimulationPredictor,
    BenchmarkDatasetLoader,
    BenchmarkItem,
    BenchmarkReporter,
    EvaluationConfig,
    EvaluationHarness,
    EvaluationMode,
    FineTunedSimulationPredictor,
    HARD_NEGATIVE_SUBTYPES,
    IN_SCHEMA_BENCH_LABELS,
    OOD_BENCH_LABELS_WITH_FALLBACK,
    Span,
    compare_evaluations,
    compute_metric_score,
    compute_span_iou,
    match_spans_for_category,
)


def test_span_creation_and_iou():
    """Validates Span invariants and IoU calculation."""
    s1 = Span(start=5, end=15, label="person", text="1234567890")
    assert s1.length == 10

    with pytest.raises(ValueError):
        Span(start=10, end=5, label="person")

    # Exact overlap
    assert compute_span_iou(10, 20, 10, 20) == 1.0

    # Half overlap: [10, 20] and [15, 25] -> inter=5, union=15 -> 5/15 = 1/3
    iou = compute_span_iou(10, 20, 15, 25)
    assert pytest.approx(iou, 0.001) == 1 / 3

    # Disjoint
    assert compute_span_iou(10, 20, 25, 35) == 0.0

    # Adjacent (edge sharing, 0 intersection)
    assert compute_span_iou(10, 20, 20, 30) == 0.0


def test_compute_metric_score():
    """Validates Precision, Recall, and F1 calculations including edge cases."""
    # Standard values
    score = compute_metric_score(tp=8, fp=2, fn=2)
    assert pytest.approx(score.precision) == 0.8
    assert pytest.approx(score.recall) == 0.8
    assert pytest.approx(score.f1) == 0.8

    # Zero values
    empty = compute_metric_score(tp=0, fp=0, fn=0)
    assert empty.precision == 0.0
    assert empty.recall == 0.0
    assert empty.f1 == 0.0

    # Zero TP
    no_tp = compute_metric_score(tp=0, fp=5, fn=5)
    assert no_tp.precision == 0.0
    assert no_tp.recall == 0.0
    assert no_tp.f1 == 0.0


def test_match_spans_strict_and_relaxed():
    """Validates exact match and boundary-relaxed greedy bipartite matching."""
    golds = [
        Span(start=10, end=20, label="private_person"),
        Span(start=30, end=40, label="private_person"),
    ]
    # Prediction 1: exact match with gold 1
    # Prediction 2: relaxed match with gold 2 ([32, 40] vs [30, 40] -> inter=8, union=10 -> IoU=0.8)
    preds = [
        Span(start=10, end=20, label="private_person"),
        Span(start=32, end=40, label="private_person"),
    ]

    # Strict mode: only 1 TP (exact), 1 FN, 1 FP
    tp_s, fp_s, fn_s = match_spans_for_category(golds, preds, EvaluationMode.STRICT)
    assert tp_s == 1
    assert fp_s == 1
    assert fn_s == 1

    # Relaxed mode (IoU >= 0.5): 2 TP, 0 FP, 0 FN
    tp_r, fp_r, fn_r = match_spans_for_category(golds, preds, EvaluationMode.RELAXED, iou_threshold=0.5)
    assert tp_r == 2
    assert fp_r == 0
    assert fn_r == 0


def test_benchmark_dataset_loader_embedded():
    """Validates reference benchmark fixture coverage across blocks and splits."""
    items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split="all")
    assert len(items) >= 30

    splits = {it.split for it in items}
    assert splits == {"short", "mid", "long"}

    blocks = {it.block for it in items}
    assert {"A", "B", "C", "M", "L"}.issubset(blocks)

    # Check Block A (all 8 In-schema labels covered)
    labels_in_a = {s.label for it in items if it.block == "A" for s in it.spans}
    for expected_label in IN_SCHEMA_BENCH_LABELS:
        assert expected_label in labels_in_a, f"Missing in-schema label: {expected_label}"

    # Check Block B (all 11 OOD labels covered)
    labels_in_b = {s.label for it in items if it.block == "B" for s in it.spans}
    for expected_ood in OOD_BENCH_LABELS_WITH_FALLBACK.keys():
        assert expected_ood in labels_in_b, f"Missing OOD label: {expected_ood}"

    # Check Block C (all 5 hard negative subtypes covered, 0 spans)
    neg_items = [it for it in items if it.block == "C"]
    assert len(neg_items) >= 10
    for it in neg_items:
        assert it.is_negative is True
        assert len(it.spans) == 0
    neg_cats = {it.category for it in neg_items}
    for expected_subtype in HARD_NEGATIVE_SUBTYPES:
        assert expected_subtype in neg_cats, f"Missing hard negative subtype: {expected_subtype}"

    # Check split filtering
    short_items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split="short")
    assert all(it.split == "short" for it in short_items)
    assert len(short_items) < len(items)


def test_benchmark_dataset_loader_jsonl_roundtrip(tmp_path: Path):
    """Validates export and import of tw-PII-bench format JSONL files."""
    test_file = tmp_path / "test_bench.jsonl"
    sample_data = [
        {
            "id": "test_001",
            "split": "short",
            "block": "A",
            "category": "private_person",
            "text": "病患林佳玲就診紀錄。",
            "spans": [{"start": 2, "end": 5, "label": "private_person", "text": "林佳玲"}],
            "is_negative": False,
        },
        {
            "id": "test_002",
            "split": "short",
            "block": "C",
            "category": "neg_business_name",
            "text": "訂購梁社漢排骨便當。",
            "spans": [],
            "is_negative": True,
        },
    ]
    with open(test_file, "w", encoding="utf-8") as f:
        for entry in sample_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    loaded = BenchmarkDatasetLoader.load_from_jsonl(test_file)
    assert len(loaded) == 2
    assert loaded[0].id == "test_001"
    assert loaded[0].spans[0].label == "private_person"
    assert loaded[1].is_negative is True


def test_evaluation_harness_execution():
    """Validates end-to-end evaluation with baseline and fine-tuned predictors."""
    items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split="short")
    harness = EvaluationHarness(EvaluationConfig(iou_threshold=0.5))

    # Evaluate Baseline
    base_pred = BaselineSimulationPredictor()
    res_base = harness.evaluate(items, base_pred, split_filter="short")
    assert "short" in res_base.splits
    rep_base = res_base.splits["short"]

    assert rep_base.total_items == len(items)
    assert 0.0 <= rep_base.in_schema_strict_micro.f1 <= 1.0
    assert 0.0 <= rep_base.in_schema_relaxed_micro.f1 <= 1.0
    assert 0.0 <= rep_base.ood_overall_generalization_rate <= 1.0
    assert rep_base.hard_negative_total_items == 10
    assert rep_base.hard_negative_fp_per_item >= 0.0

    # Evaluate Fine-tuned
    fine_pred = FineTunedSimulationPredictor()
    res_fine = harness.evaluate(items, fine_pred, split_filter="short")
    rep_fine = res_fine.splits["short"]

    # Fine-tuned should have higher relaxed F1 and OOD generalization, and lower FP
    assert rep_fine.in_schema_relaxed_micro.f1 > rep_base.in_schema_relaxed_micro.f1
    assert rep_fine.ood_overall_generalization_rate > rep_base.ood_overall_generalization_rate
    assert rep_fine.hard_negative_fp_per_item < rep_base.hard_negative_fp_per_item


def test_compare_evaluations():
    """Validates comparative delta calculations between two evaluation results."""
    items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split="all")
    harness = EvaluationHarness()

    res_base = harness.evaluate(items, BaselineSimulationPredictor())
    res_fine = harness.evaluate(items, FineTunedSimulationPredictor())

    delta = compare_evaluations(res_base, res_fine)
    assert "in_schema" in delta
    assert "out_of_schema" in delta
    assert "hard_negatives" in delta

    # Delta assertions
    assert delta["in_schema"]["relaxed_micro_f1_delta"] > 0
    assert delta["out_of_schema"]["generalization_rate_delta"] > 0
    assert delta["hard_negatives"]["fp_per_item_reduction"] > 0


def test_benchmark_reporter_markdown_and_json(tmp_path: Path):
    """Validates report formatting and file export."""
    items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split="all")
    harness = EvaluationHarness()

    res_base = harness.evaluate(items, BaselineSimulationPredictor())
    res_fine = harness.evaluate(items, FineTunedSimulationPredictor())

    # Generate Markdown
    md = BenchmarkReporter.generate_markdown_report(res_fine, baseline_result=res_base)
    assert "# GLiNER2 Taiwan PII Benchmark Evaluation Report" in md
    assert "Block A — In-Schema Entity Breakdown" in md
    assert "Block B — Taiwan-Specific OOD Entities" in md
    assert "Block C — Hard Negative False Positives" in md
    assert "Executive Summary & Baseline Comparison" in md

    # Generate JSON
    data = BenchmarkReporter.generate_json_report(res_fine, baseline_result=res_base)
    assert data["model_name"] == res_fine.model_name
    assert "comparison_with_baseline" in data

    # Export to disk
    out_files = BenchmarkReporter.export_report_files(res_fine, output_dir=tmp_path, baseline_result=res_base)
    assert out_files["markdown"].exists()
    assert out_files["json"].exists()
    assert out_files["markdown"].stat().st_size > 500
    assert out_files["json"].stat().st_size > 500
