"""
GLiNER2 Training Data Formatter.
Converts SynthesisResult and raw dictionaries into standard GLiNER2 training records:
{"input": "...", "output": {"entities": {"label": ["mention1", ...]}}}
with optional bilingual entity descriptions from TaxonomyMapper.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pii_synthea.generators.replacement import Span, SynthesisResult
from pii_synthea.taxonomy import TaxonomyMapper


class GLiNER2DataFormatter:
    """
    Formats synthetic examples into GLiNER2 native training format.
    Ensures 100% boundary fidelity and compatibility with gliner2[train].
    """

    @classmethod
    def get_entity_descriptions(cls, lang: str = "en") -> Dict[str, str]:
        """
        Retrieves prompt descriptions for all 21 canonical entities from TaxonomyMapper.
        lang: 'en' for English prompt descriptions, 'zh' for Traditional Chinese descriptions.
        """
        descriptions: Dict[str, str] = {}
        for spec in TaxonomyMapper.all_specs():
            if lang == "zh":
                descriptions[spec.gliner2_label] = f"{spec.display_name_zh}（{spec.prompt_description_zh}）"
            else:
                descriptions[spec.gliner2_label] = spec.prompt_description_en
        return descriptions

    @classmethod
    def to_record(
        cls,
        text: str,
        spans: Sequence[Union[Span, Dict[str, Any]]],
        include_descriptions: bool = False,
        desc_lang: str = "en",
        keep_exact_spans: bool = True,
    ) -> Dict[str, Any]:
        """
        Converts a single text and span sequence into a GLiNER2 training dictionary.
        
        Output structure:
        - "input": text
        - "output": {"entities": {label: [mention1, mention2, ...]}}
        - "entity_descriptions": (optional) {label: description}
        - "text": text (backward compatibility with span validators)
        - "spans": [{"start": ..., "end": ..., "label": ..., "text": ...}]
        """
        entities: Dict[str, List[str]] = {}
        standard_spans: List[Dict[str, Any]] = []

        for s in spans:
            if isinstance(s, Span):
                start = s.start
                end = s.end
                label = s.label
                val_text = s.text
            else:
                start = int(s["start"])
                end = int(s["end"])
                label = str(s["label"])
                val_text = str(s.get("text", text[start:end]))

            # Validate slice
            if 0 <= start < end <= len(text):
                actual_text = text[start:end]
                if actual_text != val_text:
                    val_text = actual_text  # Reconcile exact text

            entities.setdefault(label, []).append(val_text)
            standard_spans.append({
                "start": start,
                "end": end,
                "label": label,
                "text": val_text,
            })

        # Sort spans by starting index
        standard_spans.sort(key=lambda x: x["start"])

        record: Dict[str, Any] = {
            "input": text,
            "output": {"entities": entities},
        }

        if include_descriptions:
            all_descs = cls.get_entity_descriptions(lang=desc_lang)
            # Only include descriptions for labels present in the record (or active taxonomy)
            record["entity_descriptions"] = {
                lbl: all_descs.get(lbl, lbl) for lbl in entities.keys()
            }

        if keep_exact_spans:
            record["text"] = text
            record["spans"] = standard_spans

        return record

    @classmethod
    def from_synthesis_result(
        cls,
        result: SynthesisResult,
        include_descriptions: bool = False,
        desc_lang: str = "en",
    ) -> Dict[str, Any]:
        """Converts a validated SynthesisResult object to GLiNER2 record."""
        result.validate()
        return cls.to_record(
            text=result.text,
            spans=result.spans,
            include_descriptions=include_descriptions,
            desc_lang=desc_lang,
        )

    @classmethod
    def format_dataset_file(
        cls,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        include_descriptions: bool = False,
        desc_lang: str = "en",
    ) -> int:
        """
        Reads an existing JSONL dataset and reformats it to strict GLiNER2 native structure.
        Returns the count of converted records.
        """
        in_p = Path(input_path)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        with open(in_p, "r", encoding="utf-8") as fin, open(out_p, "w", encoding="utf-8") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                text = item.get("input", item.get("text", ""))
                spans = item.get("spans", [])

                record = cls.to_record(
                    text=text,
                    spans=spans,
                    include_descriptions=include_descriptions,
                    desc_lang=desc_lang,
                )
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

        return count
