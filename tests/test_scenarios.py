"""
Unit tests for Scenario Definitions, TagToSpanParser, PromptBuilder,
SeedTemplateLibrary, and ScenarioSynthesizer.
"""

import json
from pathlib import Path
import pytest

from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.generators.id_card import validate_national_id
from pii_synthea.scenarios.domains import (
    DomainCategory,
    ScenarioDefinition,
    ScenarioRegistry,
    TextLengthCategory,
)
from pii_synthea.scenarios.generator import ScenarioSynthesizer
from pii_synthea.scenarios.prompts import PromptBuilder
from pii_synthea.scenarios.tag_parser import TagToSpanParser
from pii_synthea.scenarios.templates import SeedTemplate, SeedTemplateLibrary
from pii_synthea.taxonomy import TaxonomyMapper


def test_domain_and_length_categories():
    """Verifies domain and length category definitions."""
    assert len(DomainCategory) == 6
    assert TextLengthCategory.categorize(50) == TextLengthCategory.SHORT
    assert TextLengthCategory.categorize(500) == TextLengthCategory.MID
    assert TextLengthCategory.categorize(2000) == TextLengthCategory.LONG

    scenarios = ScenarioRegistry.list_all()
    assert len(scenarios) >= 18  # At least 18 pre-registered scenarios

    # Check that each domain has at least one scenario in each length scale
    for domain in DomainCategory:
        dom_scenarios = ScenarioRegistry.list_by_domain(domain)
        assert len(dom_scenarios) >= 3
        lengths = {s.length_category for s in dom_scenarios}
        assert TextLengthCategory.SHORT in lengths
        assert TextLengthCategory.MID in lengths
        assert TextLengthCategory.LONG in lengths


def test_tag_to_span_parser_basic():
    """Tests parsing a single XML-tagged entity."""
    parser = TagToSpanParser(seed=42)
    raw = "病患 <person>林志豪</person> 先生您好。"
    result = parser.parse(raw)

    assert result.text == "病患 林志豪 先生您好。"
    assert len(result.spans) == 1
    span = result.spans[0]
    assert span.label == "person"
    assert span.text == "林志豪"
    assert span.start == 3
    assert span.end == 6
    assert result.text[span.start : span.end] == span.text
    assert result.validate() is True


def test_tag_to_span_parser_multiple_entities():
    """Tests parsing multiple entities with adjacent punctuation."""
    parser = TagToSpanParser(seed=42)
    raw = (
        "立約人 <person:1>王大明</person:1>（身分證字號：<national_id_number:1>A123456789</national_id_number:1>，"
        "電話：<phone_number:1>0912-345-678</phone_number:1>），現居於 <address:1>台北市大安區忠孝東路四段2號</address:1>，"
        "電子郵件信箱為 <email:1>daming@example.com</email:1>。"
    )
    result = parser.parse(raw)

    assert len(result.spans) == 5
    for s in result.spans:
        assert result.text[s.start : s.end] == s.text

    labels = [s.label for s in result.spans]
    assert "person" in labels
    assert "national_id_number" in labels
    assert "phone_number" in labels
    assert "address" in labels
    assert "email" in labels
    assert result.validate() is True


def test_tag_to_span_parser_varied_closing_tags():
    """Tests parsing when opening tag has ID or attributes and closing tag is simplified."""
    parser = TagToSpanParser(seed=42)
    # Opening tag has ID or attribute, closing tag has only label name
    raw = (
        "請致電 <person:1>陳小芬</person>，其聯絡電話為 <phone_number id='2'>0922-111-222</phone_number>。"
    )
    result = parser.parse(raw)

    assert len(result.spans) == 2
    assert result.spans[0].text == "陳小芬"
    assert result.spans[0].label == "person"
    assert result.spans[1].text == "0922-111-222"
    assert result.spans[1].label == "phone_number"
    assert result.validate() is True


def test_tag_to_span_parser_markdown_stripping():
    """Tests automatic stripping of markdown code fences from LLM responses."""
    parser = TagToSpanParser(seed=42)
    wrapped = """```xml
【通知】<person>張家豪</person> 先生，您的信用卡 <payment_card>4532</payment_card> 刷卡成功。
```"""
    result = parser.parse(wrapped)

    assert result.text == "【通知】張家豪 先生，您的信用卡 4532 刷卡成功。"
    assert len(result.spans) == 2
    assert result.spans[0].text == "張家豪"
    assert result.spans[1].text == "4532"
    assert result.validate() is True


def test_tag_to_span_parser_self_closing_or_empty():
    """Tests that empty or self-closing tags are filled with synthetic values."""
    parser = TagToSpanParser(seed=123)
    raw = "您的門診掛號病患為 <person/>，身分證為 <national_id_number></national_id_number>。"
    result = parser.parse(raw)

    assert len(result.spans) == 2
    assert len(result.spans[0].text) >= 2  # generated name
    assert len(result.spans[1].text) == 10  # generated national ID
    assert result.validate() is True


def test_tag_to_span_parser_normalization():
    """Tests normalization of algorithmically invalid PII into valid Taiwan PII."""
    parser = TagToSpanParser(seed=999)
    # A123456780 is known to fail Taiwan ID checksum (checksum is 9, not 0)
    assert validate_national_id("A123456780") is False

    raw = "病患姓名 <person>林大同</person>，身分證字號為 <national_id_number>A123456780</national_id_number>。"
    # Parse with normalize_invalid=True
    result = parser.parse(raw, normalize_invalid=True)

    assert len(result.spans) == 2
    id_span = result.spans[1]
    assert id_span.label == "national_id_number"
    assert id_span.text != "A123456780"  # Was replaced with valid ID
    assert validate_national_id(id_span.text) is True
    # Verify exact offset integrity after replacement
    assert result.text[id_span.start : id_span.end] == id_span.text
    assert result.validate() is True


def test_prompt_builder():
    """Tests building LLM prompts for different scenarios and lengths."""
    scenario = ScenarioRegistry.get("health_sms_reminder")
    assert scenario is not None

    prompts = PromptBuilder.build_prompt(
        scenario=scenario,
        target_length=TextLengthCategory.SHORT,
        include_few_shot=True,
    )
    assert "system" in prompts and "user" in prompts
    assert "台灣繁體中文" in prompts["system"]
    assert "門診預約與檢查簡訊提醒" in prompts["user"]
    assert "SHORT" in prompts["user"]
    assert "【範例（短句 SHORT）】" in prompts["user"]


def test_seed_template_library_integrity():
    """Verifies that every single seed template renders and validates 100%."""
    templates = SeedTemplateLibrary.list_all()
    assert len(templates) >= 18

    parser = TagToSpanParser(seed=42)
    for tpl in templates:
        result = parser.parse(tpl.template_text, normalize_invalid=False)
        assert result.validate() is True
        assert len(result.spans) > 0

        # Check character length scale
        if tpl.length_category == TextLengthCategory.SHORT:
            assert len(result.text) >= 15
        elif tpl.length_category == TextLengthCategory.MID:
            assert len(result.text) >= 150
        elif tpl.length_category == TextLengthCategory.LONG:
            assert len(result.text) >= 700  # Detailed contracts/records


def test_scenario_synthesizer_synthesis_and_batch():
    """Tests high-level ScenarioSynthesizer generation and batching."""
    synthesizer = ScenarioSynthesizer(seed=42)

    # 1. Synthesize single from seed
    res = synthesizer.synthesize_from_seed(
        domain=DomainCategory.REAL_ESTATE,
        length_cat=TextLengthCategory.SHORT,
        seed=100,
    )
    assert res.validate() is True
    assert len(res.spans) > 0

    # 2. Synthesize batch
    batch = synthesizer.synthesize_batch(count=6, seed=200)
    assert len(batch) == 6
    for item in batch:
        assert item.validate() is True

    # 3. Format conversion: tw-PII-bench
    bench_item = ScenarioSynthesizer.to_tw_pii_bench_format(res)
    assert "text" in bench_item and "spans" in bench_item
    for s in bench_item["spans"]:
        assert "start" in s and "end" in s and "label" in s
        # Verify slice
        assert bench_item["text"][s["start"] : s["end"]] == s["text"]


def test_scenario_synthesizer_export_files(tmp_path: Path):
    """Tests exporting generated dataset to GLiNER2 and tw-PII-bench format JSONL files."""
    synthesizer = ScenarioSynthesizer(seed=42)
    batch = synthesizer.synthesize_batch(count=4, seed=300)

    gliner_path = tmp_path / "train_gliner2.jsonl"
    bench_path = tmp_path / "tw_pii_bench.jsonl"

    count1 = ScenarioSynthesizer.export_gliner2_dataset(batch, gliner_path)
    count2 = ScenarioSynthesizer.export_tw_pii_bench_dataset(batch, bench_path)

    assert count1 == 4
    assert count2 == 4
    assert gliner_path.exists()
    assert bench_path.exists()

    # Read and inspect one line
    with open(gliner_path, "r", encoding="utf-8") as f:
        line = json.loads(f.readline())
        assert "text" in line
        assert "spans" in line
        assert len(line["spans"]) > 0
        first_span = line["spans"][0]
        assert line["text"][first_span["start"] : first_span["end"]] == first_span["text"]
