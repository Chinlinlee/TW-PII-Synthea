import pytest
import re
from pii_synthea.taxonomy import TaxonomyMapper, CANONICAL_TAXONOMY, LabelGroup


def test_taxonomy_completeness():
    assert len(CANONICAL_TAXONOMY) >= 20
    specs = TaxonomyMapper.all_specs()
    assert len(specs) == len(CANONICAL_TAXONOMY)


def test_gliner2_label_coverage():
    labels = TaxonomyMapper.get_gliner2_labels(include_extensions=True)
    # Check essential standard labels
    assert "person" in labels
    assert "national_id_number" in labels
    assert "tax_id" in labels
    assert "phone_number" in labels
    assert "address" in labels
    assert "email" in labels
    assert "date_of_birth" in labels
    assert "bank_account" in labels
    
    # Check Taiwan extensions
    assert "tw_nhi_card" in labels
    assert "license_plate" in labels
    assert "tw_line_id" in labels


def test_tw_pii_bench_bidirectional_mapping():
    # tw-PII-bench national id should map to national_id_number
    gliner_label = TaxonomyMapper.map_tw_pii_bench_to_gliner2("tw_national_id")
    assert gliner_label == "national_id_number"

    # tw-PII-bench company id should map to tax_id
    gliner_label = TaxonomyMapper.map_tw_pii_bench_to_gliner2("tw_company_id")
    assert gliner_label == "tax_id"

    # reverse mapping
    bench_label = TaxonomyMapper.map_to_tw_pii_bench("national_id_number")
    assert bench_label == "tw_national_id"


def test_regex_patterns_validity():
    for spec in CANONICAL_TAXONOMY.values():
        if spec.regex_pattern:
            # Must be valid regex syntax
            compiled = re.compile(spec.regex_pattern)
            # Must match at least one example
            matched = any(compiled.search(ex) for ex in spec.examples)
            assert matched, f"Regex {spec.regex_pattern} did not match any examples for {spec.canonical_id}: {spec.examples}"
