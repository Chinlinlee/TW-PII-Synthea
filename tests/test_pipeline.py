"""
Tests for PII-Synthea Pipeline Subsystem.
Covers:
- ValidationGate: span boundary, text integrity, overlap detection
- Deduplicator: content hashing, collision detection
- CheckpointManager: state persistence and resume
- DatasetExporter: JSONL, Parquet, train/val splitting
- BatchPipelineOrchestrator: end-to-end orchestration, balance, checkpoint/resume
"""

import json
import tempfile
from pathlib import Path

import pytest

from pii_synthea.generators.replacement import Span, SynthesisResult
from pii_synthea.pipeline.config import PipelineConfig
from pii_synthea.pipeline.dedup import Deduplicator
from pii_synthea.pipeline.validator import ValidationGate, ValidationReport


class TestValidationGate:
    """Tests strict span verification and anomaly detection."""

    def test_valid_item_passes(self):
        gate = ValidationGate()
        text = "病患陳大明於民國112年10月5日就醫"
        spans = [
            Span(start=2, end=5, label="person", text="陳大明"),
            Span(start=6, end=17, label="date", text="民國112年10月5日"),
        ]
        result = SynthesisResult(text=text, spans=spans)
        report = gate.validate(result)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_text_mismatch_fails(self):
        gate = ValidationGate()
        text = "病患陳大明於台北就醫"
        spans = [
            Span(start=2, end=5, label="person", text="李小華"),  # Mismatched text
        ]
        result = SynthesisResult(text=text, spans=spans)
        report = gate.validate(result)
        assert not report.is_valid
        assert any("mismatch" in e.lower() for e in report.errors)

    def test_boundary_out_of_bounds_fails(self):
        gate = ValidationGate()
        text = "短文本"
        spans = [
            Span(start=0, end=10, label="misc", text="短文本超過了"),
        ]
        result = SynthesisResult(text=text, spans=spans)
        report = gate.validate(result)
        assert not report.is_valid
        assert any("boundary" in e.lower() or "bounds" in e.lower() for e in report.errors)

    def test_overlapping_spans_fail(self):
        gate = ValidationGate()
        text = "台北市中正區重慶南路一段122號"
        spans = [
            Span(start=0, end=6, label="address", text="台北市中正區"),
            Span(start=3, end=10, label="address", text="中正區重慶南路"),  # Overlap
        ]
        result = SynthesisResult(text=text, spans=spans)
        report = gate.validate(result)
        assert not report.is_valid
        assert any("overlap" in e.lower() for e in report.errors)

    def test_empty_spans_allowed_for_pure_negatives(self):
        gate = ValidationGate()
        text = "這是一段完全沒有個人隱私資料的純負樣本句子。"
        result = SynthesisResult(text=text, spans=[])
        report = gate.validate(result)
        assert report.is_valid


class TestDeduplicator:
    """Tests duplicate detection and collision tracking."""

    def test_detects_duplicates(self):
        dedup = Deduplicator()
        text1 = "陳先生的手機號碼是0912-345-678"
        text2 = "陳先生的手機號碼是0912-345-678"
        text3 = "李小姐的電話是0988-111-222"

        assert not dedup.is_duplicate(text1)
        dedup.add(text1)
        assert dedup.is_duplicate(text1)
        assert dedup.is_duplicate(text2)
        assert not dedup.is_duplicate(text3)
        assert dedup.total_seen == 1
        assert dedup.total_duplicates == 0

        # Attempt to add duplicate
        added = dedup.add_if_unique(text2)
        assert not added
        assert dedup.total_duplicates == 1

        # Add unique
        added = dedup.add_if_unique(text3)
        assert added
        assert dedup.total_seen == 2


class TestRateLimiter:
    """Tests rate limiter behavior."""

    def test_disabled_rate_limiter_does_not_sleep(self):
        import time
        from pii_synthea.pipeline.rate_limiter import RateLimiter

        limiter = RateLimiter(rate_limit_per_sec=None)
        t0 = time.perf_counter()
        for _ in range(10):
            limiter.acquire()
        t1 = time.perf_counter()
        assert t1 - t0 < 0.1

    def test_rate_limiter_paces_calls(self):
        import time
        from pii_synthea.pipeline.rate_limiter import RateLimiter

        # 50 calls per second -> ~0.02s per call
        limiter = RateLimiter(rate_limit_per_sec=50.0)
        t0 = time.perf_counter()
        for _ in range(3):
            limiter.acquire()
        t1 = time.perf_counter()
        assert t1 - t0 >= 0.03


class TestCheckpointManager:
    """Tests checkpoint persistence and resume functionality."""

    def test_save_and_load_checkpoint(self, tmp_path):
        from pii_synthea.pipeline.checkpoint import CheckpointManager

        ckpt_dir = tmp_path / "checkpoint_test"
        manager = CheckpointManager(checkpoint_dir=ckpt_dir)

        assert not manager.exists()

        records = [
            {
                "text": "測試文本1",
                "spans": [{"start": 0, "end": 4, "label": "misc", "text": "測試文本"}],
                "domain": "healthcare",
                "length_cat": "short",
                "is_negative": False,
            },
            {
                "text": "測試文本2",
                "spans": [],
                "domain": "hard_negative",
                "length_cat": "short",
                "is_negative": True,
            },
        ]
        metadata = {"total_target": 100, "current_count": 2, "seed": 42}

        manager.save_checkpoint(records=records, metadata=metadata)
        assert manager.exists()

        loaded_records, seen_hashes, loaded_meta = manager.load_checkpoint()
        assert len(loaded_records) == 2
        assert len(seen_hashes) == 2
        assert loaded_meta["total_target"] == 100
        assert loaded_records[0]["text"] == "測試文本1"

    def test_append_batch(self, tmp_path):
        from pii_synthea.pipeline.checkpoint import CheckpointManager

        ckpt_dir = tmp_path / "ckpt_append"
        manager = CheckpointManager(checkpoint_dir=ckpt_dir)

        r1 = [{"text": "句子1", "spans": []}]
        manager.append_batch(r1, metadata={"current_count": 1})

        r2 = [{"text": "句子2", "spans": []}]
        manager.append_batch(r2, metadata={"current_count": 2})

        loaded_records, seen_hashes, meta = manager.load_checkpoint()
        assert len(loaded_records) == 2
        assert meta["current_count"] == 2


class TestDatasetExporter:
    """Tests splitting and file export across JSONL, Parquet, and tw-PII-bench."""

    def test_export_gliner2_and_parquet(self, tmp_path):
        import pyarrow.parquet as pq
        from pii_synthea.pipeline.config import PipelineConfig
        from pii_synthea.pipeline.exporter import DatasetExporter
        from pii_synthea.pipeline.stats import PipelineStats

        out_dir = tmp_path / "dataset_out"
        config = PipelineConfig(
            total_count=10,
            output_dir=out_dir,
            val_ratio=0.2,
            export_parquet=True,
            export_tw_bench=True,
            seed=42,
        )
        stats = PipelineStats()

        # 10 sample items
        items = []
        for i in range(10):
            text = f"民眾王小明{i}的身分證字號為A12345678{i%10}"
            spans = [
                {"start": 2, "end": 5 + len(str(i)), "label": "person", "text": f"王小明{i}"},
                {"start": 13 + len(str(i)), "end": 23 + len(str(i)), "label": "national_id_number", "text": f"A12345678{i%10}"},
            ]
            items.append({
                "text": text,
                "spans": spans,
                "domain": "healthcare",
                "length_cat": "short",
                "is_negative": False,
            })
            stats.record_item(items[-1])

        exporter = DatasetExporter(config=config, stats=stats)
        exported_files = exporter.export(items)

        # Check train.jsonl and val.jsonl
        train_jsonl = out_dir / "train.jsonl"
        val_jsonl = out_dir / "val.jsonl"
        assert train_jsonl.exists()
        assert val_jsonl.exists()

        train_lines = train_jsonl.read_text(encoding="utf-8").strip().split("\n")
        val_lines = val_jsonl.read_text(encoding="utf-8").strip().split("\n")
        assert len(train_lines) == 8
        assert len(val_lines) == 2

        # Check parquet files
        train_pq = out_dir / "train.parquet"
        val_pq = out_dir / "val.parquet"
        assert train_pq.exists()
        assert val_pq.exists()

        t_table = pq.read_table(train_pq)
        assert t_table.num_rows == 8
        assert "text" in t_table.column_names
        assert "spans" in t_table.column_names

        # Check tw_bench files
        train_bench = out_dir / "train_tw_bench.jsonl"
        assert train_bench.exists()

        # Check summary.json
        summary_file = out_dir / "summary.json"
        assert summary_file.exists()
        summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary_data["total_samples"] == 10
        assert summary_data["train_samples"] == 8
        assert summary_data["val_samples"] == 2


class TestBatchPipelineOrchestrator:
    """Tests end-to-end batch generation orchestrator."""

    def test_orchestrator_generates_batch(self, tmp_path):
        from pii_synthea.pipeline.config import PipelineConfig
        from pii_synthea.pipeline.orchestrator import BatchPipelineOrchestrator
        from pii_synthea.pipeline.validator import ValidationGate

        out_dir = tmp_path / "orchestrator_test"
        config = PipelineConfig(
            total_count=30,
            output_dir=out_dir,
            val_ratio=0.20,
            negative_ratio=0.20,
            pure_negative_ratio=0.50,
            batch_size=10,
            checkpoint_interval=10,
            seed=123,
            export_parquet=True,
        )

        orchestrator = BatchPipelineOrchestrator(config=config)
        result = orchestrator.run()

        assert result["total_samples"] == 30
        assert (out_dir / "train.jsonl").exists()
        assert (out_dir / "val.jsonl").exists()
        assert (out_dir / "train.parquet").exists()
        assert (out_dir / "val.parquet").exists()
        assert (out_dir / "summary.json").exists()

        # Validate every line in train.jsonl and val.jsonl
        gate = ValidationGate()
        for f in ["train.jsonl", "val.jsonl"]:
            with open(out_dir / f, "r", encoding="utf-8") as fp:
                for line in fp:
                    item = json.loads(line)
                    rep = gate.validate(item)
                    assert rep.is_valid, f"Validation failed: {rep.errors}"

        # Check stats distribution
        stats = result["stats"]
        assert stats["total_samples"] == 30
        assert stats["train_samples"] == 24
        assert stats["val_samples"] == 6
        assert stats["composition"]["total_negatives"] > 0
        assert stats["composition"]["positive_samples"] > 0

    def test_orchestrator_checkpoint_and_resume(self, tmp_path):
        from pii_synthea.pipeline.config import PipelineConfig
        from pii_synthea.pipeline.orchestrator import BatchPipelineOrchestrator

        out_dir = tmp_path / "resume_test"

        # Phase 1: Generate 15 items
        config1 = PipelineConfig(
            total_count=15,
            output_dir=out_dir,
            val_ratio=0.20,
            batch_size=5,
            checkpoint_interval=5,
            seed=42,
            resume=False,
        )
        orch1 = BatchPipelineOrchestrator(config=config1)
        res1 = orch1.run()
        assert res1["total_samples"] == 15

        # Checkpoint should exist
        ckpt_dir = out_dir / ".checkpoint"
        assert ckpt_dir.exists()

        # Phase 2: Resume to generate up to 25 items
        config2 = PipelineConfig(
            total_count=25,
            output_dir=out_dir,
            val_ratio=0.20,
            batch_size=5,
            checkpoint_interval=5,
            seed=42,
            resume=True,
        )
        orch2 = BatchPipelineOrchestrator(config=config2)
        res2 = orch2.run()

        assert res2["total_samples"] == 25
        assert res2["stats"]["train_samples"] == 20
        assert res2["stats"]["val_samples"] == 5


class TestPipelineCLI:
    """Tests CLI integration of the batch dataset generator."""

    def test_cli_generate_dataset(self, tmp_path, capsys):
        import argparse
        import sys
        repo_root = str(Path(__file__).parent.parent)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        import main

        out_dir = tmp_path / "cli_dataset_test"
        args = argparse.Namespace(
            count=20,
            output_dir=str(out_dir),
            val_ratio=0.20,
            negative_ratio=0.15,
            pure_negative_ratio=0.50,
            batch_size=10,
            checkpoint_interval=10,
            resume=False,
            no_parquet=False,
            export_tw_bench=True,
            rate_limit=None,
            seed=99,
        )

        main.cmd_generate_dataset(args)
        captured = capsys.readouterr()
        assert "Pipeline Run Completed" in captured.out
        assert (out_dir / "train.jsonl").exists()
        assert (out_dir / "val.jsonl").exists()
        assert (out_dir / "train.parquet").exists()
        assert (out_dir / "train_tw_bench.jsonl").exists()
        assert (out_dir / "summary.json").exists()



