"""
Checkpoint Persistence and Resume Manager for Batch Generation Pipeline.
Provides atomic writes, append-only logs, and seamless resumption.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pii_synthea.pipeline.dedup import Deduplicator


class CheckpointManager:
    """
    Persists pipeline generation state and validated samples across interruptions.
    Supports resuming partial runs to avoid duplicating generation effort.
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.metadata_file = self.checkpoint_dir / "metadata.json"
        self.records_file = self.checkpoint_dir / "records.jsonl"

    def exists(self) -> bool:
        """Checks if a valid checkpoint is present."""
        return self.metadata_file.is_file() and self.records_file.is_file()

    def save_checkpoint(
        self,
        records: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Saves full checkpoint atomically (overwrites current records.jsonl and metadata.json).
        """
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        meta = dict(metadata or {})
        meta["last_updated"] = time.time()
        meta["current_count"] = len(records)

        # Write records atomically using temporary file
        tmp_records = self.checkpoint_dir / "records.jsonl.tmp"
        with open(tmp_records, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp_records.replace(self.records_file)

        # Write metadata atomically
        tmp_meta = self.checkpoint_dir / "metadata.json.tmp"
        with open(tmp_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        tmp_meta.replace(self.metadata_file)

    def append_batch(
        self,
        batch_records: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Appends a newly generated batch of records to the checkpoint log.
        """
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        with open(self.records_file, "a", encoding="utf-8") as f:
            for r in batch_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # Update metadata
        meta = dict(metadata or {})
        meta["last_updated"] = time.time()
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def load_checkpoint(self) -> Tuple[List[Dict[str, Any]], Set[str], Dict[str, Any]]:
        """
        Loads all checkpointed records, builds the set of text hashes, and returns metadata.
        Returns: (records, seen_hashes, metadata)
        """
        if not self.exists():
            return [], set(), {}

        records: List[Dict[str, Any]] = []
        seen_hashes: Set[str] = set()

        with open(self.records_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                records.append(item)
                text = item.get("text", "")
                if text:
                    seen_hashes.add(Deduplicator.compute_hash(text))

        metadata: Dict[str, Any] = {}
        if self.metadata_file.is_file():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        return records, seen_hashes, metadata

    def clear(self) -> None:
        """Cleans up checkpoint files after successful dataset finalization."""
        if self.records_file.exists():
            self.records_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        try:
            self.checkpoint_dir.rmdir()
        except OSError:
            pass
