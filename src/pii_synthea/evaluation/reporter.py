"""
Benchmark Reporter and Visualizer.
Generates comprehensive Markdown, JSON, and terminal reports adhering to
lianghsun/tw-PII-bench publication layout and comparative delta metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pii_synthea.evaluation.harness import compare_evaluations
from pii_synthea.evaluation.metrics import (
    BenchmarkEvaluationResult,
    SplitEvaluationReport,
)


class BenchmarkReporter:
    """Formats benchmark results into Markdown reports, JSON metrics, and console summaries."""

    @classmethod
    def generate_markdown_report(
        cls,
        result: BenchmarkEvaluationResult,
        baseline_result: Optional[BenchmarkEvaluationResult] = None,
    ) -> str:
        """Generates a complete GitHub-flavored Markdown report matching tw-PII-bench specs."""
        lines: list[str] = []

        lines.append("# GLiNER2 Taiwan PII Benchmark Evaluation Report")
        lines.append("")
        lines.append(f"> **Target Model**: `{result.model_name}`  ")
        lines.append(f"> **Benchmark**: `lianghsun/tw-PII-bench`  ")
        lines.append(f"> **Evaluation Date**: `{result.evaluation_date}`  ")
        lines.append(f"> **Matching Mode**: IoU Threshold $\\ge {result.iou_threshold}$ (Relaxed) | Exact Character Span (Strict)")
        lines.append("")

        # 1. Comparative Headline Table if baseline is provided
        if baseline_result and baseline_result.overall and result.overall:
            delta = compare_evaluations(baseline_result, result)
            lines.append("## 1. Executive Summary & Baseline Comparison")
            lines.append("")
            lines.append("| Evaluation Dimension | Baseline (Zero-Shot) | Fine-Tuned (GLiNER2-TW) | Delta Improvement (Δ) |")
            lines.append("|:---------------------|:---------------------|:------------------------|:----------------------|")
            
            s_base = delta["in_schema"]["strict_micro_f1_baseline"] * 100
            s_fine = delta["in_schema"]["strict_micro_f1_finetuned"] * 100
            s_d = delta["in_schema"]["strict_micro_f1_delta"] * 100
            lines.append(f"| **In-schema Strict Micro F1** | {s_base:.1f}% | **{s_fine:.1f}%** | `+{s_d:.1f}%` |")

            r_base = delta["in_schema"]["relaxed_micro_f1_baseline"] * 100
            r_fine = delta["in_schema"]["relaxed_micro_f1_finetuned"] * 100
            r_d = delta["in_schema"]["relaxed_micro_f1_delta"] * 100
            lines.append(f"| **Boundary-Relaxed Micro F1** | {r_base:.1f}% | **{r_fine:.1f}%** | `+{r_d:.1f}%` |")

            o_base = delta["out_of_schema"]["generalization_rate_baseline"] * 100
            o_fine = delta["out_of_schema"]["generalization_rate_finetuned"] * 100
            o_d = delta["out_of_schema"]["generalization_rate_delta"] * 100
            lines.append(f"| **Taiwan OOD Generalization Rate** | {o_base:.1f}% | **{o_fine:.1f}%** | `+{o_d:.1f}%` |")

            f_base = delta["hard_negatives"]["fp_per_item_baseline"]
            f_fine = delta["hard_negatives"]["fp_per_item_finetuned"]
            f_red = delta["hard_negatives"]["fp_per_item_reduction"]
            lines.append(f"| **Hard Negative FP / Item** | {f_base:.2f} | **{f_fine:.2f}** | `-{f_red:.2f}` (suppressed) |")
            lines.append("")

        # 2. Per-split summary
        lines.append("## 2. Per-Split Performance Summary")
        lines.append("")
        lines.append("| Split | Items | In-schema Strict F1 | Relaxed F1 (IoU > 0.5) | OOD Generalization | Hard Neg FP/item |")
        lines.append("|:------|:------|:-------------------|:-----------------------|:-------------------|:-----------------|")

        splits_to_show = ["short", "mid", "long"]
        for s in splits_to_show:
            if s in result.splits:
                rep = result.splits[s]
                strict_f1 = rep.in_schema_strict_micro.f1 * 100
                relaxed_f1 = rep.in_schema_relaxed_micro.f1 * 100
                ood_gen = rep.ood_overall_generalization_rate * 100
                neg_fp = rep.hard_negative_fp_per_item
                neg_str = f"{neg_fp:.2f}" if rep.hard_negative_total_items > 0 else "—"
                lines.append(f"| `{s}` | {rep.total_items} | {strict_f1:.1f}% | {relaxed_f1:.1f}% | {ood_gen:.1f}% | {neg_str} |")

        if result.overall:
            ov = result.overall
            ov_strict = ov.in_schema_strict_micro.f1 * 100
            ov_relaxed = ov.in_schema_relaxed_micro.f1 * 100
            ov_gen = ov.ood_overall_generalization_rate * 100
            lines.append(f"| **Overall** | **{ov.total_items}** | **{ov_strict:.1f}%** | **{ov_relaxed:.1f}%** | **{ov_gen:.1f}%** | **{ov.hard_negative_fp_per_item:.2f}** |")
        lines.append("")

        # 3. In-schema detailed breakdown
        breakdown_rep = result.overall or (result.splits.get("short") if result.splits else None)
        if breakdown_rep:
            lines.append("## 3. Block A — In-Schema Entity Breakdown (8 Categories)")
            lines.append("")
            lines.append("| Label | Gold Mentions | TP | FP | FN | Precision | Recall | Strict F1 | Relaxed F1 |")
            lines.append("|:------|:--------------|:---|:---|:---|:----------|:-------|:----------|:-----------|")

            for label, cm in breakdown_rep.in_schema_metrics.items():
                strict_m = cm.strict
                relaxed_m = cm.relaxed
                p_pct = strict_m.precision * 100
                r_pct = strict_m.recall * 100
                f_pct = strict_m.f1 * 100
                rf_pct = relaxed_m.f1 * 100
                lines.append(f"| `{label}` | {cm.total_gold} | {strict_m.tp} | {strict_m.fp} | {strict_m.fn} | {p_pct:.1f}% | {r_pct:.1f}% | **{f_pct:.1f}%** | {rf_pct:.1f}% |")

            sm = breakdown_rep.in_schema_strict_micro
            rm = breakdown_rep.in_schema_relaxed_micro
            lines.append(f"| **Micro Average** | **—** | **{sm.tp}** | **{sm.fp}** | **{sm.fn}** | **{sm.precision*100:.1f}%** | **{sm.recall*100:.1f}%** | **{sm.f1*100:.1f}%** | **{rm.f1*100:.1f}%** |")
            lines.append(f"| **Macro Average** | **—** | **—** | **—** | **—** | **—** | **—** | **{breakdown_rep.in_schema_strict_macro.f1*100:.1f}%** | **{breakdown_rep.in_schema_relaxed_macro.f1*100:.1f}%** |")
            lines.append("")

            # 4. Out-of-schema Taiwan-specific diagnostic table
            lines.append("## 4. Block B — Taiwan-Specific OOD Entities (11 Categories)")
            lines.append("")
            lines.append("| OOD Label | Expected Fallback | Total | ✓ Correct | △ Wrong Label | ✗ Missed | Generalization Rate | Detection Rate |")
            lines.append("|:----------|:------------------|:------|:----------|:--------------|:---------|:--------------------|:---------------|")

            for ood_lbl, om in breakdown_rep.ood_metrics.items():
                fb_str = f"`{om.expected_fallback}`" if om.expected_fallback else "*(none)*"
                gen_pct = om.generalization_rate * 100
                det_pct = om.detection_rate * 100
                lines.append(f"| `{ood_lbl}` | {fb_str} | {om.total} | {om.correct} | {om.wrong_label} | {om.missed} | {gen_pct:.1f}% | {det_pct:.1f}% |")

            lines.append("")
            lines.append(f"- **OOD Overall Detection Rate (any span overlap)**: {breakdown_rep.ood_overall_detection_rate*100:.1f}%")
            lines.append(f"- **OOD Overall Generalization Rate (correct schema fallback)**: {breakdown_rep.ood_overall_generalization_rate*100:.1f}%")
            lines.append("")

            # 5. Hard Negatives table
            lines.append("## 5. Block C — Hard Negative False Positives (5 Subtypes)")
            lines.append("")
            lines.append("| Hard Negative Subtype | Total Items | False Positives (FPs) | FP / Item |")
            lines.append("|:----------------------|:------------|:----------------------|:----------|")

            for st, hm in breakdown_rep.hard_negative_metrics.items():
                lines.append(f"| `{st}` | {hm.total_items} | {hm.fps} | {hm.fp_per_item:.2f} |")

            lines.append(f"| **Total / Average** | **{breakdown_rep.hard_negative_total_items}** | **{breakdown_rep.hard_negative_total_fps}** | **{breakdown_rep.hard_negative_fp_per_item:.2f}** |")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def generate_json_report(
        cls,
        result: BenchmarkEvaluationResult,
        baseline_result: Optional[BenchmarkEvaluationResult] = None,
    ) -> Dict[str, Any]:
        """Serializes the complete benchmark result and optional comparison delta to JSON."""
        data = result.to_dict()
        if baseline_result:
            data["comparison_with_baseline"] = compare_evaluations(baseline_result, result)
        return data

    @classmethod
    def print_terminal_summary(
        cls,
        result: BenchmarkEvaluationResult,
        baseline_result: Optional[BenchmarkEvaluationResult] = None,
    ) -> None:
        """Prints a human-readable, clean console summary to standard output."""
        print(f"\n{'=' * 96}")
        print(f"                     GLiNER2 Taiwan PII Benchmark Evaluation Report")
        print(f" Model: {result.model_name} | Date: {result.evaluation_date}")
        print(f"{'=' * 96}")

        if baseline_result and baseline_result.overall and result.overall:
            delta = compare_evaluations(baseline_result, result)
            print("\n------------------------------ Baseline vs Fine-Tuned Delta ------------------------------")
            print(f"{'Metric':<34} | {'Baseline':<16} | {'Fine-Tuned':<16} | {'Delta':<12}")
            print("-" * 88)
            s_b = f"{delta['in_schema']['strict_micro_f1_baseline']*100:.1f}%"
            s_f = f"{delta['in_schema']['strict_micro_f1_finetuned']*100:.1f}%"
            s_d = f"+{delta['in_schema']['strict_micro_f1_delta']*100:.1f}%"
            print(f"{'In-schema Strict Micro F1':<34} | {s_b:<16} | {s_f:<16} | {s_d:<12}")

            r_b = f"{delta['in_schema']['relaxed_micro_f1_baseline']*100:.1f}%"
            r_f = f"{delta['in_schema']['relaxed_micro_f1_finetuned']*100:.1f}%"
            r_d = f"+{delta['in_schema']['relaxed_micro_f1_delta']*100:.1f}%"
            print(f"{'Boundary-Relaxed Micro F1':<34} | {r_b:<16} | {r_f:<16} | {r_d:<12}")

            o_b = f"{delta['out_of_schema']['generalization_rate_baseline']*100:.1f}%"
            o_f = f"{delta['out_of_schema']['generalization_rate_finetuned']*100:.1f}%"
            o_d = f"+{delta['out_of_schema']['generalization_rate_delta']*100:.1f}%"
            print(f"{'Taiwan OOD Generalization Rate':<34} | {o_b:<16} | {o_f:<16} | {o_d:<12}")

            f_b = f"{delta['hard_negatives']['fp_per_item_baseline']:.2f}"
            f_f = f"{delta['hard_negatives']['fp_per_item_finetuned']:.2f}"
            f_d = f"-{delta['hard_negatives']['fp_per_item_reduction']:.2f}"
            print(f"{'Hard Negative FP / Item':<34} | {f_b:<16} | {f_f:<16} | {f_d:<12}")
            print("-" * 88)

        print("\n------------------------------- Per-Split Performance Summary -------------------------------")
        print(f"{'Split':<10} | {'Items':<8} | {'Strict Micro F1':<18} | {'Relaxed Micro F1':<18} | {'OOD Gen Rate':<14} | {'Neg FP/item'}")
        print("-" * 96)
        for s in ["short", "mid", "long"]:
            if s in result.splits:
                rep = result.splits[s]
                sm = f"{rep.in_schema_strict_micro.f1*100:.1f}%"
                rm = f"{rep.in_schema_relaxed_micro.f1*100:.1f}%"
                og = f"{rep.ood_overall_generalization_rate*100:.1f}%"
                fp = f"{rep.hard_negative_fp_per_item:.2f}" if rep.hard_negative_total_items > 0 else "N/A"
                print(f"{s:<10} | {rep.total_items:<8} | {sm:<18} | {rm:<18} | {og:<14} | {fp}")

        if result.overall:
            ov = result.overall
            sm = f"{ov.in_schema_strict_micro.f1*100:.1f}%"
            rm = f"{ov.in_schema_relaxed_micro.f1*100:.1f}%"
            og = f"{ov.ood_overall_generalization_rate*100:.1f}%"
            print(f"{'Overall':<10} | {ov.total_items:<8} | {sm:<18} | {rm:<18} | {og:<14} | {ov.hard_negative_fp_per_item:.2f}")
        print("=" * 96)

    @classmethod
    def export_report_files(
        cls,
        result: BenchmarkEvaluationResult,
        output_dir: Union[str, Path] = "reports/benchmark",
        baseline_result: Optional[BenchmarkEvaluationResult] = None,
    ) -> Dict[str, Path]:
        """Exports both Markdown and JSON reports to disk."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        md_path = out / "benchmark_report.md"
        json_path = out / "benchmark_report.json"

        md_content = cls.generate_markdown_report(result, baseline_result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        json_data = cls.generate_json_report(result, baseline_result)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        return {"markdown": md_path, "json": json_path}
