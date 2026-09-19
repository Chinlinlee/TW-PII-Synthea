"""
Pipeline Configuration dataclasses and settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class PipelineConfig:
    """Configuration settings for synthetic batch dataset generation."""

    total_count: int = 1000
    output_dir: Path = field(default_factory=lambda: Path("data/gliner2_tw"))
    val_ratio: float = 0.20
    negative_ratio: float = 0.15
    pure_negative_ratio: float = 0.50
    batch_size: int = 100
    checkpoint_interval: int = 100
    resume: bool = False
    export_parquet: bool = True
    export_tw_bench: bool = False
    rate_limit_per_sec: Optional[float] = None
    seed: Optional[int] = 42
    max_retries_per_item: int = 10

    def __post_init__(self) -> None:
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if self.total_count <= 0:
            raise ValueError(f"total_count must be positive, got {self.total_count}")
        if not (0.0 <= self.val_ratio < 1.0):
            raise ValueError(f"val_ratio must be in [0.0, 1.0), got {self.val_ratio}")
        if not (0.0 <= self.negative_ratio <= 1.0):
            raise ValueError(f"negative_ratio must be in [0.0, 1.0], got {self.negative_ratio}")
        if not (0.0 <= self.pure_negative_ratio <= 1.0):
            raise ValueError(f"pure_negative_ratio must be in [0.0, 1.0], got {self.pure_negative_ratio}")
