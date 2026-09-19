"""
Scenario Synthesizer and Pipeline Orchestrator.
Integrates domain definitions, seed templates, prompt construction, XML tag parsing,
and format export (GLiNER2 & tw-PII-bench) into a unified generation interface.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.generators.replacement import SynthesisResult, TemplateEngine
from pii_synthea.scenarios.domains import (
    DomainCategory,
    ScenarioDefinition,
    ScenarioRegistry,
    TextLengthCategory,
)
from pii_synthea.scenarios.prompts import PromptBuilder
from pii_synthea.scenarios.tag_parser import TagToSpanParser
from pii_synthea.scenarios.templates import SeedTemplate, SeedTemplateLibrary
from pii_synthea.taxonomy import TaxonomyMapper


class ScenarioSynthesizer:
    """
    High-level synthesizer for Taiwan PII scenarios and training texts.
    Supports both offline deterministic template synthesis and LLM-driven tagged generation.
    """

    def __init__(
        self,
        generator: Optional[TaiwanPIIGenerator] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.generator = generator or TaiwanPIIGenerator(seed=seed)
        self.tag_parser = TagToSpanParser(generator=self.generator, seed=seed)
        self.template_engine = TemplateEngine(generator=self.generator, seed=seed)

    def synthesize_from_seed(
        self,
        template_id: Optional[str] = None,
        domain: Optional[DomainCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
        seed: Optional[int] = None,
    ) -> SynthesisResult:
        """
        Synthesizes an annotated text using a seed template with algorithmically valid PII.

        Args:
            template_id: Specific template ID if known.
            domain: Filter templates by domain.
            length_cat: Filter templates by length category.
            seed: Reproducible generation seed.
        """
        if template_id:
            tpl = SeedTemplateLibrary.get(template_id)
            if not tpl:
                raise ValueError(f"Template with ID '{template_id}' not found in SeedTemplateLibrary.")
        else:
            candidates = SeedTemplateLibrary.filter(domain=domain, length_cat=length_cat)
            if not candidates:
                raise ValueError(
                    f"No seed templates found matching domain={domain} and length_cat={length_cat}."
                )
            local_rng = random.Random(seed) if seed is not None else self.rng
            tpl = local_rng.choice(candidates)

        # Parse tags and generate authentic Taiwan PII
        engine = TemplateEngine(generator=TaiwanPIIGenerator(seed=seed)) if seed is not None else self.template_engine
        # The template may contain XML-style <label:id> tags; TagToSpanParser handles them with exact offsets
        parser = TagToSpanParser(generator=TaiwanPIIGenerator(seed=seed)) if seed is not None else self.tag_parser
        return parser.parse(tpl.template_text, normalize_invalid=False)

    def synthesize_batch(
        self,
        count: int,
        domain_dist: Optional[Dict[DomainCategory, float]] = None,
        length_dist: Optional[Dict[TextLengthCategory, float]] = None,
        seed: Optional[int] = None,
    ) -> List[SynthesisResult]:
        """
        Synthesizes a batch of annotated texts adhering to domain and length distributions.
        """
        local_rng = random.Random(seed) if seed is not None else self.rng
        domains = list(DomainCategory)
        lengths = list(TextLengthCategory)

        # Default balanced distributions if unspecified
        domain_weights = [domain_dist.get(d, 1.0) if domain_dist else 1.0 for d in domains]
        length_weights = [length_dist.get(l, 1.0) if length_dist else 1.0 for l in lengths]

        results: List[SynthesisResult] = []
        for i in range(count):
            item_seed = local_rng.randint(1, 10_000_000)
            chosen_domain = local_rng.choices(domains, weights=domain_weights, k=1)[0]
            chosen_length = local_rng.choices(lengths, weights=length_weights, k=1)[0]

            res = self.synthesize_from_seed(
                domain=chosen_domain,
                length_cat=chosen_length,
                seed=item_seed,
            )
            results.append(res)

        return results

    def synthesize_batch_with_negatives(
        self,
        total_count: int,
        negative_ratio: float = 0.15,
        pure_negative_ratio: float = 0.5,
        seed: Optional[int] = None,
    ) -> List[SynthesisResult]:
        """
        Synthesizes a combined batch blending standard scenario PII data with hard negatives.

        Args:
            total_count: Total items to generate.
            negative_ratio: Fraction of items that are hard negatives (0.0 to 1.0).
            pure_negative_ratio: Among hard negatives, fraction that are pure (0 spans).
            seed: Reproducible seed.
        """
        from pii_synthea.negatives.generator import HardNegativeSynthesizer

        local_rng = random.Random(seed) if seed is not None else self.rng
        neg_count = round(total_count * negative_ratio)
        pos_count = total_count - neg_count

        results: List[SynthesisResult] = []

        # 1. Standard PII scenarios
        if pos_count > 0:
            pos_batch = self.synthesize_batch(
                count=pos_count,
                seed=local_rng.randint(1, 10_000_000),
            )
            results.extend(pos_batch)

        # 2. Hard negatives
        if neg_count > 0:
            neg_synth = HardNegativeSynthesizer(generator=self.generator, seed=local_rng.randint(1, 10_000_000))
            neg_batch = neg_synth.generate_batch(
                count=neg_count,
                pure_negative_ratio=pure_negative_ratio,
                seed=local_rng.randint(1, 10_000_000),
            )
            results.extend(neg_batch)

        local_rng.shuffle(results)
        return results

    def build_llm_prompt(
        self,
        scenario_id: Optional[str] = None,
        domain: Optional[DomainCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
        custom_instructions: Optional[str] = None,
        include_few_shot: bool = True,
        template_only: bool = False,
    ) -> Dict[str, str]:
        """
        Builds system and user prompts for an LLM to generate XML-annotated Taiwan PII text.
        """
        if scenario_id:
            scenario = ScenarioRegistry.get(scenario_id)
            if not scenario:
                raise ValueError(f"Scenario ID '{scenario_id}' not found in ScenarioRegistry.")
        else:
            candidates = ScenarioRegistry.filter(domain=domain, length_cat=length_cat)
            if not candidates:
                raise ValueError(
                    f"No scenarios found matching domain={domain} and length_cat={length_cat}."
                )
            scenario = self.rng.choice(candidates)

        return PromptBuilder.build_prompt(
            scenario=scenario,
            target_length=length_cat,
            custom_instructions=custom_instructions,
            include_few_shot=include_few_shot,
            template_only=template_only,
        )

    def ingest_llm_response(
        self,
        llm_output: str,
        normalize_invalid: bool = True,
    ) -> SynthesisResult:
        """
        Ingests raw text or markdown output from an LLM, parses all XML tags,
        computes exact character offsets, and validates span integrity.
        """
        return self.tag_parser.parse(
            raw_text=llm_output,
            normalize_invalid=normalize_invalid,
        )

    @staticmethod
    def to_tw_pii_bench_format(result: SynthesisResult) -> Dict[str, Any]:
        """
        Converts a SynthesisResult into tw-PII-bench format, mapping GLiNER2 labels
        to tw-PII-bench benchmark categories (e.g. tw_national_id, private_person, etc.).
        """
        result.validate()
        spans = []
        for s in sorted(result.spans, key=lambda x: x.start):
            bench_label = TaxonomyMapper.map_to_tw_pii_bench(s.label)
            spans.append(
                {
                    "start": s.start,
                    "end": s.end,
                    "label": bench_label,
                    "text": s.text,
                    "gliner2_label": s.label,
                }
            )
        return {
            "text": result.text,
            "spans": spans,
        }

    @classmethod
    def export_gliner2_dataset(
        cls,
        results: Sequence[SynthesisResult],
        file_path: Union[str, Path],
    ) -> int:
        """Exports synthesis results to a GLiNER2-compatible JSONL file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(p, "w", encoding="utf-8") as f:
            for r in results:
                item = r.to_gliner2_format()
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
        return count

    @classmethod
    def export_tw_pii_bench_dataset(
        cls,
        results: Sequence[SynthesisResult],
        file_path: Union[str, Path],
    ) -> int:
        """Exports synthesis results to a tw-PII-bench-compatible JSONL file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(p, "w", encoding="utf-8") as f:
            for r in results:
                item = cls.to_tw_pii_bench_format(r)
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
        return count
