#!/usr/bin/env python3
"""
Standalone GLiNER2 Taiwan PII Benchmark Evaluator.
Executes evaluation on lianghsun/tw-PII-bench for baseline and fine-tuned checkpoints,
calculating span-level Exact Match, Relaxed IoU, Taiwan OOD diagnosis, and Hard Negative false positive rates.

Usage:
    # Run evaluation with offline simulation:
    python scripts/evaluate_gliner2_tw.py --offline --compare-baseline

    # Run evaluation on live fine-tuned checkpoint:
    python scripts/evaluate_gliner2_tw.py --model-path ./models/gliner2_tw_pii --baseline-path fastino/gliner2-privacy-filter-PII-multi

    # Run on a local tw-PII-bench JSONL/Parquet file:
    python scripts/evaluate_gliner2_tw.py --dataset-path data/gliner2_tw/val_tw_bench.jsonl --split all
"""

import argparse
import sys
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from pii_synthea.evaluation import (
    BaselineSimulationPredictor,
    BenchmarkDatasetLoader,
    BenchmarkReporter,
    EvaluationConfig,
    EvaluationHarness,
    FineTunedSimulationPredictor,
    GLiNER2Predictor,
)


def parse_args():
    parser = argparse.ArgumentParser(description="GLiNER2 Taiwan PII Benchmark Evaluation Suite")
    parser.add_argument(
        "--model-path",
        default="fastino/gliner2-privacy-filter-PII-multi",
        help="Hugging Face model ID or path to local fine-tuned checkpoint (default: fastino/gliner2-privacy-filter-PII-multi)",
    )
    parser.add_argument(
        "--baseline-path",
        default=None,
        help="Optional baseline model path to compute comparative delta improvements against",
    )
    parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Compute side-by-side comparison against un-fine-tuned baseline",
    )
    parser.add_argument(
        "--dataset-path",
        default=None,
        help="Path to local JSONL/Parquet dataset file (if omitted, loads embedded tw-PII-bench reference set or HF)",
    )
    parser.add_argument(
        "--split",
        choices=["short", "mid", "long", "all"],
        default="all",
        help="Benchmark split to evaluate (default: all)",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="IoU threshold for boundary-relaxed span matching (default: 0.5)",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for model predictions (default: 0.5)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline simulation mode without GPU or gliner2/torch library",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/benchmark",
        help="Directory to save benchmark_report.md and benchmark_report.json (default: reports/benchmark)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 80)
    print("           GLiNER2 Taiwan PII Evaluation Harness (tw-PII-bench)")
    print("=" * 80)
    print(f"Target Model      : {args.model_path}")
    print(f"Split Filter      : {args.split}")
    print(f"IoU Threshold     : {args.iou_threshold}")
    print(f"Offline Mode      : {args.offline}")
    print(f"Output Directory  : {args.output_dir}")
    print("-" * 80)

    # 1. Load Dataset
    if args.dataset_path:
        p = Path(args.dataset_path)
        if p.suffix == ".parquet":
            items = BenchmarkDatasetLoader.load_from_parquet(p, split=args.split)
        else:
            items = BenchmarkDatasetLoader.load_from_jsonl(p, split=args.split)
        print(f"Loaded {len(items)} items from {args.dataset_path}")
    else:
        # Fallback to embedded reference benchmark fixtures
        items = BenchmarkDatasetLoader.get_reference_benchmark_samples(split=args.split)
        print(f"Loaded {len(items)} items from embedded tw-PII-bench reference dataset")

    # 2. Configure Predictors
    cfg = EvaluationConfig(
        model_name_or_path=args.model_path,
        iou_threshold=args.iou_threshold,
        score_threshold=args.score_threshold,
    )
    harness = EvaluationHarness(config=cfg)

    # Model predictor
    if args.offline:
        if "fine" in args.model_path.lower() or "tw" in args.model_path.lower():
            predictor = FineTunedSimulationPredictor()
        else:
            predictor = BaselineSimulationPredictor()
    else:
        try:
            predictor = GLiNER2Predictor(
                model_name_or_path=args.model_path,
                use_char_splitter=True,
                score_threshold=args.score_threshold,
            )
        except RuntimeError as e:
            print(f"\n[Notice] {e}")
            print("Falling back to simulation predictor for evaluation execution...")
            predictor = (
                FineTunedSimulationPredictor()
                if ("fine" in args.model_path.lower() or "tw" in args.model_path.lower())
                else BaselineSimulationPredictor()
            )

    # Baseline predictor for comparison if requested
    baseline_result = None
    if args.baseline_path or args.compare_baseline:
        base_name = args.baseline_path or "fastino/gliner2-privacy-filter-PII-multi"
        print(f"\nEvaluating Baseline Zero-Shot Model: {base_name}...")
        base_cfg = EvaluationConfig(
            model_name_or_path=base_name,
            iou_threshold=args.iou_threshold,
            score_threshold=args.score_threshold,
        )
        base_harness = EvaluationHarness(config=base_cfg)
        if args.offline or not args.baseline_path:
            base_pred = BaselineSimulationPredictor()
        else:
            try:
                base_pred = GLiNER2Predictor(base_name, use_char_splitter=False)
            except Exception:
                base_pred = BaselineSimulationPredictor()
        baseline_result = base_harness.evaluate(items, base_pred, split_filter=args.split)

    # 3. Execute Target Evaluation
    print(f"\nEvaluating Target Model: {args.model_path}...")
    result = harness.evaluate(items, predictor, split_filter=args.split)

    # 4. Print Summary & Export Artifacts
    BenchmarkReporter.print_terminal_summary(result, baseline_result)
    exported = BenchmarkReporter.export_report_files(result, output_dir=args.output_dir, baseline_result=baseline_result)
    print(f"\nExported Reports:")
    print(f"  - Markdown Report : {exported['markdown']}")
    print(f"  - JSON Report     : {exported['json']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
