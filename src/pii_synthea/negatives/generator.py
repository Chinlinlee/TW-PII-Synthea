"""
Hard Negative Synthesizer & Batch Generator (Ticket 05).
Generates pure negative samples (producing len(spans) == 0) and mixed samples
(where authentic Taiwan PII is annotated with exact character offsets while
hard negative distractors remain unannotated).
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence

from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.generators.replacement import SynthesisResult
from pii_synthea.negatives.catalog import (
    HardNegativeCatalog,
    HardNegativeCategory,
    HardNegativeItem,
)
from pii_synthea.negatives.templates import (
    HardNegativeTemplateLibrary,
    MixedNegativeTemplate,
    PureNegativeTemplate,
)
from pii_synthea.scenarios.domains import TextLengthCategory
from pii_synthea.scenarios.tag_parser import TagToSpanParser


class HardNegativeSynthesizer:
    """
    Synthesizer for Taiwan hard negatives.
    Provides methods for generating pure negative texts and mixed texts with distractors.
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

    def generate_pure(
        self,
        category: Optional[HardNegativeCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
        seed: Optional[int] = None,
    ) -> SynthesisResult:
        """
        Generates a pure negative sample where NO spans are annotated (len(spans) == 0).
        """
        local_rng = random.Random(seed) if seed is not None else self.rng
        chosen_cat = category or local_rng.choice(list(HardNegativeCategory))

        templates = HardNegativeTemplateLibrary.get_pure(category=chosen_cat, length_cat=length_cat)
        if not templates:
            # Fallback to any template for the category
            templates = HardNegativeTemplateLibrary.get_pure(category=chosen_cat)
        if not templates:
            templates = HardNegativeTemplateLibrary.all_pure_templates()

        tpl = local_rng.choice(templates)

        # Substitute negative entity placeholders
        brand_item = HardNegativeCatalog.sample(HardNegativeCategory.BRAND_PERSON_NAME, seed=local_rng.randint(1, 10_000_000))
        hist_item = HardNegativeCatalog.sample(HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE, seed=local_rng.randint(1, 10_000_000))
        landmark_item = HardNegativeCatalog.sample(HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS, seed=local_rng.randint(1, 10_000_000))
        hotline_item = HardNegativeCatalog.sample(HardNegativeCategory.PUBLIC_HOTLINE, seed=local_rng.randint(1, 10_000_000))
        email_item = HardNegativeCatalog.sample(HardNegativeCategory.PUBLIC_EMAIL, seed=local_rng.randint(1, 10_000_000))
        code_item = HardNegativeCatalog.sample(HardNegativeCategory.OFFICIAL_CODE_NUMBER, seed=local_rng.randint(1, 10_000_000))
        neg_item = HardNegativeCatalog.sample(chosen_cat, seed=local_rng.randint(1, 10_000_000))

        rendered = tpl.template_text.format(
            brand=brand_item.text,
            public_figure=hist_item.text,
            landmark=landmark_item.text,
            hotline=hotline_item.text,
            public_email=email_item.text,
            code_number=code_item.text,
            neg_entity=neg_item.text,
        )

        res = SynthesisResult(text=rendered, spans=[])
        res.validate()
        return res

    def generate_mixed(
        self,
        category: Optional[HardNegativeCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
        seed: Optional[int] = None,
    ) -> SynthesisResult:
        """
        Generates a mixed sample where genuine PII placeholders are annotated with
        exact character offsets, but hard negative distractors remain unannotated.
        """
        local_rng = random.Random(seed) if seed is not None else self.rng
        chosen_cat = category or local_rng.choice(list(HardNegativeCategory))

        templates = HardNegativeTemplateLibrary.get_mixed(category=chosen_cat, length_cat=length_cat)
        if not templates:
            templates = HardNegativeTemplateLibrary.get_mixed(category=chosen_cat)
        if not templates:
            templates = HardNegativeTemplateLibrary.all_mixed_templates()

        tpl = local_rng.choice(templates)

        # Sample the negative distractor
        distractor = HardNegativeCatalog.sample(chosen_cat, seed=local_rng.randint(1, 10_000_000))

        # Substitute negative placeholder directly without XML tags
        text_with_pii_tags = tpl.template_text.replace("{neg_entity}", distractor.text)

        # Parse tags using TagToSpanParser with local seed for authentic PII replacement
        parser = TagToSpanParser(
            generator=TaiwanPIIGenerator(seed=local_rng.randint(1, 10_000_000)),
            seed=local_rng.randint(1, 10_000_000),
        )
        res = parser.parse(text_with_pii_tags, normalize_invalid=False)

        # Double check: Ensure the distractor text was not accidentally labeled as a span
        for s in res.spans:
            if s.text == distractor.text:
                raise ValueError(
                    f"Distractor text '{distractor.text}' was erroneously labeled as span: {s}"
                )

        res.validate()
        return res

    def generate_batch(
        self,
        count: int,
        pure_negative_ratio: float = 0.5,
        category_dist: Optional[Dict[HardNegativeCategory, float]] = None,
        seed: Optional[int] = None,
    ) -> List[SynthesisResult]:
        """
        Generates a batch of hard negative samples (pure + mixed).

        Args:
            count: Total number of samples.
            pure_negative_ratio: Ratio of pure negative samples (0.0 to 1.0).
            category_dist: Optional distribution weights across categories.
            seed: Random seed for reproducibility.
        """
        local_rng = random.Random(seed) if seed is not None else self.rng
        categories = list(HardNegativeCategory)
        cat_weights = [category_dist.get(c, 1.0) if category_dist else 1.0 for c in categories]

        pure_count = round(count * pure_negative_ratio)
        mixed_count = count - pure_count

        results: List[SynthesisResult] = []

        # 1. Pure negatives
        for _ in range(pure_count):
            item_seed = local_rng.randint(1, 10_000_000)
            cat = local_rng.choices(categories, weights=cat_weights, k=1)[0]
            results.append(self.generate_pure(category=cat, seed=item_seed))

        # 2. Mixed negatives
        for _ in range(mixed_count):
            item_seed = local_rng.randint(1, 10_000_000)
            cat = local_rng.choices(categories, weights=cat_weights, k=1)[0]
            results.append(self.generate_mixed(category=cat, seed=item_seed))

        # Shuffle to mix pure and mixed evenly
        local_rng.shuffle(results)
        return results
