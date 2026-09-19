"""
Batch Pipeline Orchestrator.
Manages balanced high-throughput synthetic generation, validation, deduplication,
rate limiting, checkpointing, and dataset export.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.negatives.catalog import HardNegativeCategory
from pii_synthea.negatives.generator import HardNegativeSynthesizer
from pii_synthea.pipeline.checkpoint import CheckpointManager
from pii_synthea.pipeline.config import PipelineConfig
from pii_synthea.pipeline.dedup import Deduplicator
from pii_synthea.pipeline.exporter import DatasetExporter
from pii_synthea.pipeline.rate_limiter import RateLimiter
from pii_synthea.pipeline.stats import PipelineStats
from pii_synthea.pipeline.validator import ValidationGate
from pii_synthea.scenarios.domains import DomainCategory, TextLengthCategory
from pii_synthea.scenarios.generator import ScenarioSynthesizer


class BatchPipelineOrchestrator:
    """
    High-reliability orchestrator capable of stably generating 10,000+ synthetic samples.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        generator: Optional[TaiwanPIIGenerator] = None,
        scenario_synthesizer: Optional[ScenarioSynthesizer] = None,
        negative_synthesizer: Optional[HardNegativeSynthesizer] = None,
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.generator = generator or TaiwanPIIGenerator(seed=self.config.seed)
        self.scenario_synthesizer = scenario_synthesizer or ScenarioSynthesizer(
            generator=self.generator, seed=self.config.seed
        )
        self.negative_synthesizer = negative_synthesizer or HardNegativeSynthesizer(
            generator=self.generator, seed=self.config.seed
        )
        self.progress_callback = progress_callback

        self.checkpoint_dir = self.config.output_dir / ".checkpoint"
        self.checkpoint_manager = CheckpointManager(checkpoint_dir=self.checkpoint_dir)
        self.deduplicator = Deduplicator()
        self.validator = ValidationGate()
        self.rate_limiter = RateLimiter(rate_limit_per_sec=self.config.rate_limit_per_sec)
        self.stats = PipelineStats()

        self.rng = random.Random(self.config.seed)

    def run(self) -> Dict[str, Any]:
        """
        Executes generation pipeline until total_count valid, unique items are collected,
        then exports datasets.
        """
        records: List[Dict[str, Any]] = []

        # 1. Resume from checkpoint if requested and available
        if self.config.resume and self.checkpoint_manager.exists():
            existing_records, seen_hashes, _ = self.checkpoint_manager.load_checkpoint()
            self.deduplicator = Deduplicator(initial_hashes=seen_hashes)
            for r in existing_records:
                self.stats.record_item(r)
                records.append(r)

        target = self.config.total_count
        target_negatives = round(target * self.config.negative_ratio)

        domains = list(DomainCategory)
        lengths = list(TextLengthCategory)
        neg_categories = list(HardNegativeCategory)

        max_attempts = (target - len(records)) * self.config.max_retries_per_item + 100
        attempts = 0

        # 2. Main generation loop
        while len(records) < target and attempts < max_attempts:
            attempts += 1
            item_seed = self.rng.randint(1, 100_000_000)

            # Determine whether this item should be a hard negative or positive scenario
            current_negatives = self.stats.pure_negative_count + self.stats.mixed_negative_count
            should_be_negative = (current_negatives < target_negatives) and (
                (len(records) == 0) or ((current_negatives / max(1, len(records))) < self.config.negative_ratio)
            )

            if should_be_negative:
                # Decide pure negative vs mixed negative
                should_be_pure = (
                    self.stats.pure_negative_count < (target_negatives * self.config.pure_negative_ratio)
                )
                neg_cat = self.rng.choice(neg_categories)
                length_cat = self.rng.choice(lengths)

                if should_be_pure:
                    res = self.negative_synthesizer.generate_pure(
                        category=neg_cat,
                        length_cat=length_cat,
                        seed=item_seed,
                    )
                    is_pure = True
                else:
                    res = self.negative_synthesizer.generate_mixed(
                        category=neg_cat,
                        length_cat=length_cat,
                        seed=item_seed,
                    )
                    is_pure = False

                domain_str = "hard_negative"
                length_str = length_cat.value
                is_negative = True
                neg_cat_str = neg_cat.value

            else:
                # Positive scenario: select domain and length
                # Pick domain with lowest current count for balance
                chosen_domain = min(domains, key=lambda d: self.stats.domains[d.value])
                chosen_length = min(lengths, key=lambda l: self.stats.lengths[l.value])

                res = self.scenario_synthesizer.synthesize_from_seed(
                    domain=chosen_domain,
                    length_cat=chosen_length,
                    seed=item_seed,
                )
                domain_str = chosen_domain.value
                length_str = chosen_length.value
                is_negative = False
                is_pure = False
                neg_cat_str = None

            # 3. Deduplication Check
            if not self.deduplicator.add_if_unique(res.text):
                self.stats.total_duplicates_skipped += 1
                continue

            # 4. Strict Validation Gate
            report = self.validator.validate(res)
            if not report.is_valid:
                self.stats.total_validation_failures += 1
                continue

            # 5. Rate Limiting
            self.rate_limiter.acquire()

            # 6. Record validated sample
            item_record = {
                "text": res.text,
                "spans": [s.to_dict() for s in res.spans],
                "domain": domain_str,
                "length_cat": length_str,
                "is_negative": is_negative,
                "is_pure_negative": is_pure,
                "negative_category": neg_cat_str,
            }

            self.stats.record_item(
                item=item_record,
                domain=domain_str,
                length_cat=length_str,
                is_negative=is_negative,
                is_pure_negative=is_pure,
                negative_category=neg_cat_str,
            )
            records.append(item_record)

            # Checkpoint at periodic intervals
            if len(records) % self.config.checkpoint_interval == 0:
                self.checkpoint_manager.save_checkpoint(
                    records=records,
                    metadata={"total_target": target, "seed": self.config.seed},
                )

            # Progress callback
            if self.progress_callback:
                self.progress_callback(len(records), target, self.stats.summary_dict())

        # Save final checkpoint
        self.checkpoint_manager.save_checkpoint(
            records=records,
            metadata={"total_target": target, "seed": self.config.seed},
        )

        # 7. Dataset Export
        exporter = DatasetExporter(config=self.config, stats=self.stats)
        exported_files = exporter.export(records)

        return {
            "total_samples": len(records),
            "exported_files": exported_files,
            "stats": self.stats.summary_dict(),
        }
