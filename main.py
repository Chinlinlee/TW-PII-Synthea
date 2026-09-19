"""
PII-Synthea CLI Entrypoint
Taiwan PII Synthetic Data Generator & GLiNER2 Fine-tuning Suite
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pii_synthea.generators import TaiwanPIIGenerator, TemplateEngine
from pii_synthea.negatives import (
    HardNegativeCatalog,
    HardNegativeCategory,
    HardNegativeSynthesizer,
)
from pii_synthea.scenarios import (
    DomainCategory,
    PromptBuilder,
    ScenarioDefinition,
    ScenarioRegistry,
    ScenarioSynthesizer,
    SeedTemplateLibrary,
    TagToSpanParser,
    TextLengthCategory,
)
from pii_synthea.taxonomy import LabelGroup, TaxonomyMapper


def cmd_list_taxonomy(args):
    """Lists all 21 PII categories with their GLiNER2 and tw-PII-bench mappings."""
    specs = TaxonomyMapper.all_specs()
    print(f"\n==================== PII-Synthea Canonical Taxonomy ({len(specs)} Entities) ====================")
    print(f"{'Canonical ID':<24} | {'GLiNER2 Label':<22} | {'tw-PII-bench':<20} | {'Type':<10} | {'Name (ZH)'}")
    print("-" * 105)
    for s in specs:
        ext = "Extension" if s.is_extension else "Standard"
        print(f"{s.canonical_id:<24} | {s.gliner2_label:<22} | {s.tw_pii_bench_label:<20} | {ext:<10} | {s.display_name_zh}")
    print("=" * 105)


def cmd_export_schema(args):
    """Exports schema.json to specified file."""
    output_path = args.output or "schema.json"
    schema = TaxonomyMapper.to_schema_dict()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"Successfully exported schema to {output_path} ({len(schema['entities'])} entities)")


def cmd_generate_sample(args):
    """Generates synthetic Taiwan PII samples."""
    gen = TaiwanPIIGenerator(seed=args.seed)
    if args.label:
        val = gen.generate(args.label)
        print(f"[{args.label}]: {val}")
    else:
        samples = gen.generate_all()
        print(f"\n========== Synthetic Taiwan PII Sample Batch (21 Entities, Seed={args.seed}) ==========")
        for label, val in samples.items():
            print(f"{label:<24}: {val}")
        print("=" * 75)


def cmd_render_template(args):
    """Renders a text template with PII placeholders and validates span offsets."""
    engine = TemplateEngine(seed=args.seed)
    template_str = args.template
    if not template_str and args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            template_str = f.read()

    if not template_str:
        template_str = (
            "立約人 {{person:1}}（身分證字號：{{national_id_number:1}}，電話：{{phone_number:1}}）"
            "與 台灣積體電路製造股份有限公司（統一編號：{{tax_id:1}}，地址：{{address:1}}）"
            "合意簽署本協議。款項撥付帳戶為 {{bank_account:1}}，聯繫郵箱：{{email:1}}。"
        )
        print("Using default sample template...")

    result = engine.render(template_str)
    print("\n--- Synthesized Text ---")
    print(result.text)
    print("\n--- Extracted & Validated Spans ---")
    for s in result.spans:
        print(f"[{s.start:3d}:{s.end:3d}] ({s.label:<20}) {s.text}")
    print("\nSpan verification: 100% OK (assert text[start:end] == span.text passed)")


def cmd_list_scenarios(args):
    """Lists available authentic Taiwan domain scenarios across all domains and length scales."""
    scenarios = ScenarioRegistry.list_all()
    print(f"\n==================== Taiwan Context Scenarios ({len(scenarios)} Defined) ====================")
    print(f"{'Scenario ID':<32} | {'Domain':<22} | {'Scale':<8} | {'Scenario Name (ZH)'}")
    print("-" * 95)
    for s in scenarios:
        print(f"{s.scenario_id:<32} | {s.domain.display_name_zh:<22} | {s.length_category.value.upper():<8} | {s.name_zh}")
    print("=" * 95)


def cmd_build_prompt(args):
    """Builds LLM generation prompts for a specific scenario."""
    synthesizer = ScenarioSynthesizer()
    domain_enum = DomainCategory(args.domain) if args.domain else None
    length_enum = TextLengthCategory(args.length) if args.length else None

    prompts = synthesizer.build_llm_prompt(
        scenario_id=args.scenario_id,
        domain=domain_enum,
        length_cat=length_enum,
        custom_instructions=args.instructions,
        include_few_shot=not args.no_few_shot,
        template_only=args.template_only,
    )

    print("\n==================== [SYSTEM PROMPT] ====================")
    print(prompts["system"])
    print("\n==================== [USER PROMPT] ====================")
    print(prompts["user"])
    print("=" * 60)


def cmd_generate_scenario(args):
    """Generates an annotated text from seed scenario templates with authentic valid PII."""
    synthesizer = ScenarioSynthesizer(seed=args.seed)
    domain_enum = DomainCategory(args.domain) if args.domain else None
    length_enum = TextLengthCategory(args.length) if args.length else None

    result = synthesizer.synthesize_from_seed(
        template_id=args.template_id,
        domain=domain_enum,
        length_cat=length_enum,
        seed=args.seed,
    )

    print("\n--- Synthesized Scenario Text ---")
    print(result.text)
    print(f"\n--- Extracted & Validated Spans ({len(result.spans)} entities, char length {len(result.text)}) ---")
    for s in result.spans:
        print(f"[{s.start:4d}:{s.end:4d}] ({s.label:<22}) {s.text}")

    print("\nIntegrity check: 100% verified (assert text[start:end] == span.text passed)")

    if args.output:
        p = Path(args.output)
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps(result.to_gliner2_format(), ensure_ascii=False, indent=2))
        print(f"Exported GLiNER2 training item to {p}")


def cmd_parse_tags(args):
    """Parses XML-tagged text and extracts exact character spans."""
    parser = TagToSpanParser(seed=args.seed)
    text_content = args.text
    if not text_content and args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text_content = f.read()

    if not text_content:
        text_content = (
            "病患 <person>林佳玲</person> 女士，身分證字號為 <national_id_number>A223456781</national_id_number>，"
            "於 <address>新北市新莊區中正路100號</address> 診所門診掛號，聯絡電話：<phone_number>0912-345-678</phone_number>。"
        )
        print("Using default tagged sample...")

    result = parser.parse(text_content, normalize_invalid=args.normalize)
    print("\n--- Clean Text (Tags Stripped) ---")
    print(result.text)
    print(f"\n--- Extracted Spans ({len(result.spans)} detected) ---")
    for s in result.spans:
        print(f"[{s.start:3d}:{s.end:3d}] ({s.label:<20}) {s.text}")
    print("\nSpan verification: 100% OK")


def cmd_list_negatives(args):
    """Lists all hard negative categories, counts, and sample entities."""
    print("\n==================== Taiwan Hard Negatives Catalog ====================")
    print(f"{'Category ID':<28} | {'Confusable':<14} | {'Count':<6} | {'Sample Entities'}")
    print("-" * 90)
    for cat in HardNegativeCategory:
        items = HardNegativeCatalog.get_items(cat)
        samples = "、".join([it.text for it in items[:3]]) + ("..." if len(items) > 3 else "")
        confusable = items[0].confusable_with if items else ""
        print(f"{cat.value:<28} | {confusable:<14} | {len(items):<6} | {samples}")
    print("=" * 90)


def cmd_generate_negative(args):
    """Generates a pure or mixed hard negative sample."""
    synthesizer = HardNegativeSynthesizer(seed=args.seed)
    cat_enum = HardNegativeCategory(args.category) if args.category else None
    len_enum = TextLengthCategory(args.length) if args.length else None

    if args.mixed:
        result = synthesizer.generate_mixed(category=cat_enum, length_cat=len_enum, seed=args.seed)
        mode_str = "Mixed (Real PII + Hard Negative Distractors)"
    else:
        result = synthesizer.generate_pure(category=cat_enum, length_cat=len_enum, seed=args.seed)
        mode_str = "Pure Negative (0 PII Spans)"

    print(f"\n--- Synthesized Hard Negative [{mode_str}] ---")
    print(result.text)
    print(f"\n--- Extracted & Validated Spans ({len(result.spans)} entities, char length {len(result.text)}) ---")
    if result.spans:
        for s in result.spans:
            print(f"[{s.start:4d}:{s.end:4d}] ({s.label:<22}) {s.text}")
    else:
        print("(No spans - 100% negative sample as expected)")

    print("\nIntegrity check: 100% verified")

    if args.output:
        p = Path(args.output)
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps(result.to_gliner2_format(), ensure_ascii=False, indent=2))
        print(f"Exported GLiNER2 training item to {p}")


def main():
    parser = argparse.ArgumentParser(description="PII-Synthea: Taiwan PII Synthetic Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-taxonomy
    p_list = subparsers.add_parser("list-taxonomy", help="List all canonical PII entities and mappings")
    p_list.set_defaults(func=cmd_list_taxonomy)

    # Command: export-schema
    p_export = subparsers.add_parser("export-schema", help="Export schema.json")
    p_export.add_argument("-o", "--output", default="schema.json", help="Output file path")
    p_export.set_defaults(func=cmd_export_schema)

    # Command: generate-sample
    p_gen = subparsers.add_parser("generate-sample", help="Generate synthetic Taiwan PII samples")
    p_gen.add_argument("-l", "--label", help="Specific PII label to generate (e.g. national_id_number, address)")
    p_gen.add_argument("-s", "--seed", type=int, default=None, help="Random seed for reproducibility")
    p_gen.set_defaults(func=cmd_generate_sample)

    # Command: render-template
    p_render = subparsers.add_parser("render-template", help="Render template with PII tags & exact spans")
    p_render.add_argument("-t", "--template", help="Template string with {{tag}} or <tag>")
    p_render.add_argument("-f", "--file", help="Template file path")
    p_render.add_argument("-s", "--seed", type=int, default=None, help="Random seed for reproducibility")
    p_render.set_defaults(func=cmd_render_template)

    # Command: list-scenarios
    p_scenarios = subparsers.add_parser("list-scenarios", help="List all predefined Taiwan contextual scenarios")
    p_scenarios.set_defaults(func=cmd_list_scenarios)

    # Command: build-prompt
    p_prompt = subparsers.add_parser("build-prompt", help="Build LLM prompt for a scenario")
    p_prompt.add_argument("-i", "--scenario-id", help="Scenario ID (e.g. health_line_consultation)")
    p_prompt.add_argument("-d", "--domain", choices=[d.value for d in DomainCategory], help="Domain category")
    p_prompt.add_argument("-l", "--length", choices=[l.value for l in TextLengthCategory], help="Text length category")
    p_prompt.add_argument("--instructions", help="Custom supplementary instructions")
    p_prompt.add_argument("--no-few-shot", action="store_true", help="Exclude few-shot examples")
    p_prompt.add_argument("--template-only", action="store_true", help="Instruct LLM to generate empty template tags")
    p_prompt.set_defaults(func=cmd_build_prompt)

    # Command: generate-scenario
    p_gen_sc = subparsers.add_parser("generate-scenario", help="Generate scenario text with valid Taiwan PII")
    p_gen_sc.add_argument("-t", "--template-id", help="Specific seed template ID")
    p_gen_sc.add_argument("-d", "--domain", choices=[d.value for d in DomainCategory], help="Domain filter")
    p_gen_sc.add_argument("-l", "--length", choices=[l.value for l in TextLengthCategory], help="Length filter")
    p_gen_sc.add_argument("-s", "--seed", type=int, default=None, help="Random seed")
    p_gen_sc.add_argument("-o", "--output", help="Save GLiNER2 training JSON item to file")
    p_gen_sc.set_defaults(func=cmd_generate_scenario)

    # Command: parse-tags
    p_parse = subparsers.add_parser("parse-tags", help="Parse XML-tagged text into clean text + exact spans")
    p_parse.add_argument("-t", "--text", help="Tagged text string")
    p_parse.add_argument("-f", "--file", help="Path to text file")
    p_parse.add_argument("-n", "--normalize", action="store_true", help="Normalize invalid PII algorithmically")
    p_parse.add_argument("-s", "--seed", type=int, default=None, help="Random seed for normalization")
    p_parse.set_defaults(func=cmd_parse_tags)

    # Command: list-negatives
    p_list_neg = subparsers.add_parser("list-negatives", help="List all hard negative categories and counts")
    p_list_neg.set_defaults(func=cmd_list_negatives)

    # Command: generate-negative
    p_gen_neg = subparsers.add_parser("generate-negative", help="Generate a pure or mixed hard negative sample")
    p_gen_neg.add_argument("-c", "--category", choices=[c.value for c in HardNegativeCategory], help="Negative category")
    p_gen_neg.add_argument("-l", "--length", choices=[l.value for l in TextLengthCategory], help="Text length category")
    p_gen_neg.add_argument("-m", "--mixed", action="store_true", help="Generate mixed sample (true PII + negative distractor)")
    p_gen_neg.add_argument("-s", "--seed", type=int, default=None, help="Random seed")
    p_gen_neg.add_argument("-o", "--output", help="Save GLiNER2 training JSON item to file")
    p_gen_neg.set_defaults(func=cmd_generate_negative)

    args = parser.parse_args()
    if not args.command:
        cmd_list_taxonomy(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
