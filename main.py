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

    args = parser.parse_args()
    if not args.command:
        # Default behavior: display taxonomy list
        cmd_list_taxonomy(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
