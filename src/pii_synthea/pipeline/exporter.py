"""
Dataset Exporter for GLiNER2, Parquet, and tw-PII-bench Formats.
Handles deterministic train/validation splitting and comprehensive metadata summary.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pii_synthea.generators.replacement import SynthesisResult
from pii_synthea.pipeline.config import PipelineConfig
from pii_synthea.pipeline.stats import PipelineStats
from pii_synthea.taxonomy import TaxonomyMapper


class DatasetExporter:
    """
    Exports synthetic samples to standard training formats:
    1. GLiNER2 JSONL format (train.jsonl, val.jsonl)
    2. Parquet format (train.parquet, val.parquet)
    3. tw-PII-bench evaluation format (train_tw_bench.jsonl, val_tw_bench.jsonl)
    4. Dataset summary & distribution analysis (summary.json)
    """

    def __init__(
        self,
        config: PipelineConfig,
        stats: Optional[PipelineStats] = None,
    ) -> None:
        self.config = config
        self.stats = stats or PipelineStats()

    def export(
        self,
        items: Sequence[Union[SynthesisResult, Dict[str, Any]]],
    ) -> Dict[str, Path]:
        """
        Splits items into train and validation sets, exports all target formats,
        and saves summary metadata.
        """
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Standardize items to dict format
        standard_items: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, SynthesisResult):
                it.validate()
                item_dict = {
                    "text": it.text,
                    "spans": [
                        {"start": s.start, "end": s.end, "label": s.label, "text": s.text}
                        for s in sorted(it.spans, key=lambda x: x.start)
                    ],
                    "domain": "unknown",
                    "length_cat": "mid",
                    "is_negative": len(it.spans) == 0,
                    "is_pure_negative": len(it.spans) == 0,
                }
            else:
                item_dict = it
            standard_items.append(item_dict)

        # Shuffle deterministically for train/val split
        rng = random.Random(self.config.seed)
        shuffled = list(standard_items)
        rng.shuffle(shuffled)

        val_count = int(len(shuffled) * self.config.val_ratio)
        train_count = len(shuffled) - val_count

        train_items = shuffled[:train_count]
        val_items = shuffled[train_count:]

        self.stats.train_count = len(train_items)
        self.stats.val_count = len(val_items)

        exported_paths: Dict[str, Path] = {}

        # 1. Export GLiNER2 JSONL
        train_jsonl = out_dir / "train.jsonl"
        val_jsonl = out_dir / "val.jsonl"
        self._write_gliner2_jsonl(train_items, train_jsonl)
        self._write_gliner2_jsonl(val_items, val_jsonl)
        exported_paths["train_jsonl"] = train_jsonl
        exported_paths["val_jsonl"] = val_jsonl

        # 2. Export Parquet if requested
        if self.config.export_parquet:
            train_pq = out_dir / "train.parquet"
            val_pq = out_dir / "val.parquet"
            self._write_parquet(train_items, train_pq)
            self._write_parquet(val_items, val_pq)
            exported_paths["train_parquet"] = train_pq
            exported_paths["val_parquet"] = val_pq

        # 3. Export tw-PII-bench format if requested
        if self.config.export_tw_bench:
            train_bench = out_dir / "train_tw_bench.jsonl"
            val_bench = out_dir / "val_tw_bench.jsonl"
            self._write_tw_bench_jsonl(train_items, train_bench)
            self._write_tw_bench_jsonl(val_items, val_bench)
            exported_paths["train_tw_bench"] = train_bench
            exported_paths["val_tw_bench"] = val_bench

        # 4. Export summary.json
        self.stats.finish()
        summary_path = out_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(self.stats.summary_dict(), f, ensure_ascii=False, indent=2)
        exported_paths["summary"] = summary_path

        return exported_paths

    @staticmethod
    def _write_gliner2_jsonl(items: List[Dict[str, Any]], path: Path) -> None:
        """Writes items in GLiNER2 standard JSONL format."""
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                gliner_entry = {
                    "text": it["text"],
                    "spans": [
                        {
                            "start": s["start"],
                            "end": s["end"],
                            "label": s["label"],
                            "text": s["text"],
                        }
                        for s in sorted(it.get("spans", []), key=lambda x: x["start"])
                    ],
                }
                f.write(json.dumps(gliner_entry, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_tw_bench_jsonl(items: List[Dict[str, Any]], path: Path) -> None:
        """Writes items in tw-PII-bench standard JSONL format."""
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                bench_spans = []
                for s in sorted(it.get("spans", []), key=lambda x: x["start"]):
                    bench_spans.append(
                        {
                            "start": s["start"],
                            "end": s["end"],
                            "label": TaxonomyMapper.map_to_tw_pii_bench(s["label"]),
                            "text": s["text"],
                            "gliner2_label": s["label"],
                        }
                    )
                entry = {
                    "text": it["text"],
                    "spans": bench_spans,
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_parquet(items: List[Dict[str, Any]], path: Path) -> None:
        """Writes items to Parquet via pyarrow."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as e:
            raise RuntimeError("pyarrow is required to export parquet datasets. Install via uv add pyarrow.") from e

        records = []
        for idx, it in enumerate(items):
            spans = it.get("spans", [])
            records.append(
                {
                    "id": idx,
                    "text": it["text"],
                    "spans": json.dumps(spans, ensure_ascii=False),
                    "spans_count": len(spans),
                    "domain": str(it.get("domain", "")),
                    "length_cat": str(it.get("length_cat", "")),
                    "is_negative": bool(it.get("is_negative", False)),
                    "is_pure_negative": bool(it.get("is_pure_negative", False)),
                }
            )

        table = pa.Table.from_pylist(records)
        pq.write_table(table, path)
