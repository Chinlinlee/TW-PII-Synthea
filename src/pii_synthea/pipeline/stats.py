"""
Statistics Tracking and Distribution Balance Analyzer for PII Generation Pipeline.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from pii_synthea.generators.replacement import SynthesisResult


@dataclass
class PipelineStats:
    """Tracks pipeline metrics, entity balance, and operational performance."""

    total_generated: int = 0
    total_valid: int = 0
    total_duplicates_skipped: int = 0
    total_validation_failures: int = 0
    train_count: int = 0
    val_count: int = 0

    # Categorical distributions
    domains: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    lengths: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    entity_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    negative_categories: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    pure_negative_count: int = 0
    mixed_negative_count: int = 0
    positive_count: int = 0

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def record_item(
        self,
        item: Union[SynthesisResult, Dict[str, Any]],
        domain: Optional[str] = None,
        length_cat: Optional[str] = None,
        is_negative: bool = False,
        is_pure_negative: bool = False,
        negative_category: Optional[str] = None,
    ) -> None:
        """Records metadata and label frequencies of a validated synthesized item."""
        self.total_generated += 1
        self.total_valid += 1

        if isinstance(item, SynthesisResult):
            spans = item.spans
            text_len = len(item.text)
        else:
            spans = item.get("spans", [])
            text_len = len(item.get("text", ""))
            domain = domain or item.get("domain")
            length_cat = length_cat or item.get("length_cat")
            is_negative = is_negative or item.get("is_negative", False)
            is_pure_negative = is_pure_negative or item.get("is_pure_negative", False)
            negative_category = negative_category or item.get("negative_category")

        # Record domain and length
        if domain:
            self.domains[domain] += 1
        if length_cat:
            self.lengths[length_cat] += 1

        # Record negatives vs positives
        if is_negative:
            if is_pure_negative or len(spans) == 0:
                self.pure_negative_count += 1
            else:
                self.mixed_negative_count += 1
            if negative_category:
                self.negative_categories[negative_category] += 1
        else:
            self.positive_count += 1

        # Record entity spans
        for s in spans:
            if isinstance(s, dict):
                label = str(s.get("label", "unknown"))
            elif hasattr(s, "label"):
                label = str(getattr(s, "label"))
            else:
                label = "unknown"
            self.entity_counts[label] += 1

    def finish(self) -> None:
        """Marks completion timestamp."""
        if self.end_time is None:
            self.end_time = time.time()

    @property
    def duration_sec(self) -> float:
        end = self.end_time or time.time()
        return max(0.001, end - self.start_time)

    @property
    def throughput_per_sec(self) -> float:
        return self.total_valid / self.duration_sec

    def summary_dict(self) -> Dict[str, Any]:
        """Returns structured dictionary of execution stats and distribution."""
        return {
            "total_samples": self.total_valid,
            "train_samples": self.train_count,
            "val_samples": self.val_count,
            "total_generated": self.total_generated,
            "duplicates_skipped": self.total_duplicates_skipped,
            "validation_failures": self.total_validation_failures,
            "duration_seconds": round(self.duration_sec, 2),
            "throughput_samples_per_second": round(self.throughput_per_sec, 2),
            "composition": {
                "positive_samples": self.positive_count,
                "pure_negative_samples": self.pure_negative_count,
                "mixed_negative_samples": self.mixed_negative_count,
                "total_negatives": self.pure_negative_count + self.mixed_negative_count,
                "negative_ratio": round(
                    (self.pure_negative_count + self.mixed_negative_count) / max(1, self.total_valid), 4
                ),
            },
            "domains": dict(sorted(self.domains.items())),
            "lengths": dict(sorted(self.lengths.items())),
            "entity_counts": dict(sorted(self.entity_counts.items(), key=lambda x: -x[1])),
            "negative_categories": dict(sorted(self.negative_categories.items())),
        }
