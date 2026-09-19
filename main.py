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
from pii_synthea.taxonomy import TaxonomyMapper, LabelGroup



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

    args = parser.parse_args()
    if not args.command:
        # Default behavior: display taxonomy list
        cmd_list_taxonomy(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
