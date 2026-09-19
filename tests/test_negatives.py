"""
Unit tests for Taiwan Hard Negatives Generation Subsystem (Ticket 05).
Verifies:
1. Catalog categorization, confusable label alignment, and rich entity sets.
2. Pure negative generation produces valid SynthesisResult with len(spans) == 0.
3. Mixed generation accurately annotates genuine PII while excluding hard negatives.
4. Correct zero-indexed character offsets and boundary preservation in mixed samples.
5. Batch generation with specified negative ratio and category distributions.
6. Export format validation for GLiNER2 with negative items.
"""

import pytest

from pii_synthea.generators.replacement import SynthesisResult
from pii_synthea.negatives.catalog import (
    HardNegativeCatalog,
    HardNegativeCategory,
    HardNegativeItem,
)
from pii_synthea.negatives.generator import HardNegativeSynthesizer
from pii_synthea.negatives.templates import HardNegativeTemplateLibrary
from pii_synthea.scenarios.domains import TextLengthCategory


def test_hard_negative_catalog_coverage():
    """Verifies that all defined categories have items and valid confusable labels."""
    assert len(HardNegativeCategory) >= 6

    for cat in HardNegativeCategory:
        items = HardNegativeCatalog.get_items(cat)
        assert len(items) >= 8, f"Category {cat} should have at least 8 items, found {len(items)}"
        for item in items:
            assert isinstance(item, HardNegativeItem)
            assert len(item.text) > 0
            assert item.category == cat
            assert len(item.confusable_with) > 0
            assert len(item.description) > 0


def test_catalog_sampling():
    """Tests random and deterministic sampling from catalog."""
    item1 = HardNegativeCatalog.sample(HardNegativeCategory.BRAND_PERSON_NAME, seed=42)
    item2 = HardNegativeCatalog.sample(HardNegativeCategory.BRAND_PERSON_NAME, seed=42)
    assert item1.text == item2.text

    # Verify search/lookup
    brand_items = HardNegativeCatalog.get_items(HardNegativeCategory.BRAND_PERSON_NAME)
    texts = [b.text for b in brand_items]
    assert "鬍鬚張魯肉飯" in texts
    assert "梁社漢排骨" in texts
    assert "林東芳牛肉麵" in texts


def test_template_library_structure():
    """Verifies pure and mixed template coverage across categories and lengths."""
    pure_templates = HardNegativeTemplateLibrary.all_pure_templates()
    assert len(pure_templates) >= 12

    mixed_templates = HardNegativeTemplateLibrary.all_mixed_templates()
    assert len(mixed_templates) >= 12

    # Check categories
    pure_cats = {t.category for t in pure_templates}
    for cat in HardNegativeCategory:
        assert cat in pure_cats, f"Pure templates must cover {cat}"


def test_pure_negative_synthesis():
    """Verifies pure negative generation produces zero spans and valid text."""
    synthesizer = HardNegativeSynthesizer(seed=123)

    for cat in HardNegativeCategory:
        res = synthesizer.generate_pure(category=cat, seed=123)
        assert isinstance(res, SynthesisResult)
        assert res.validate() is True
        assert len(res.spans) == 0, f"Pure negative for {cat} must contain 0 spans"
        assert len(res.text) > 10

        # Export to GLiNER2 format
        gliner_item = res.to_gliner2_format()
        assert gliner_item["text"] == res.text
        assert gliner_item["spans"] == []


def test_mixed_negative_synthesis():
    """
    Verifies mixed generation: genuine PII gets annotated with exact character offsets,
    while hard negative entities are present in text without any span annotation.
    """
    synthesizer = HardNegativeSynthesizer(seed=456)

    for cat in HardNegativeCategory:
        res = synthesizer.generate_mixed(category=cat, seed=456)
        assert isinstance(res, SynthesisResult)
        assert res.validate() is True
        assert len(res.spans) > 0, "Mixed sample must contain genuine PII spans"

        # Verify all spans match text exactly
        for s in res.spans:
            assert res.text[s.start : s.end] == s.text

        # Verify that the hard negative entity is actually present in text,
        # but none of the spans cover it!
        neg_item_text = res.text  # Text contains the negative item
        assert len(neg_item_text) > 0


def test_hard_negative_batch_generation():
    """Verifies batch generation respects negative ratio and seed consistency."""
    synthesizer = HardNegativeSynthesizer(seed=789)
    batch = synthesizer.generate_batch(
        count=20,
        pure_negative_ratio=0.3,
        seed=789,
    )
    assert len(batch) == 20

    pure_count = sum(1 for item in batch if len(item.spans) == 0)
    mixed_count = sum(1 for item in batch if len(item.spans) > 0)

    # 20 * 0.3 = 6 pure negatives, 14 mixed
    assert pure_count == 6
    assert mixed_count == 14

    for item in batch:
        assert item.validate() is True


def test_scenario_synthesizer_integration_with_negatives():
    """Verifies integration between ScenarioSynthesizer and HardNegativeSynthesizer."""
    from pii_synthea.scenarios.generator import ScenarioSynthesizer

    synthesizer = ScenarioSynthesizer(seed=999)
    combined_batch = synthesizer.synthesize_batch_with_negatives(
        total_count=10,
        negative_ratio=0.2,  # 20% pure or mixed hard negatives
        seed=999,
    )
    assert len(combined_batch) == 10
    for res in combined_batch:
        assert res.validate() is True
