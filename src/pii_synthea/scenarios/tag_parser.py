"""
Robust XML-style Tag-to-Span Parser and Entity Normalization Engine.
Extracts tagged spans from LLM generation outputs and seed templates, calculates exact character offsets,
validates span boundaries, and optionally normalizes hallucinated entities into
algorithmically valid Taiwan PII.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from pii_synthea.generators.business import validate_tax_id
from pii_synthea.generators.financial import (
    validate_bank_account,
    validate_card_cvv,
    validate_credit_card,
)
from pii_synthea.generators.id_card import (
    validate_household_no,
    validate_national_id,
)
from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.generators.misc import (
    validate_email,
    validate_license_plate,
    validate_line_id,
    validate_medical_license,
    validate_military_id,
    validate_nhi_card,
    validate_passport_number,
    validate_ptt_id,
)
from pii_synthea.generators.phone import validate_phone_number
from pii_synthea.generators.replacement import Span, SpanReplacer, SynthesisResult
from pii_synthea.taxonomy import TaxonomyMapper


class TagToSpanParser:
    """
    Parses XML-style entity annotations produced by LLMs or seed templates,
    strips enclosing tags, computes exact character-level offsets, and produces verified
    SynthesisResults with optional algorithmic validation and normalization.

    Supports:
    - Enclosing tags: `<person>林志豪</person>`, `<person:1>林志豪</person:1>`
    - Self-closing / empty tags: `<person/>`, `<person></person>`
    - Standalone placeholder tags: `<person:1>`, `{{person:1}}`
    """

    TAG_MASTER_REGEX = re.compile(
        # 1. Enclosing tag with inner content: <label:id ...>content</label>
        r"<([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?(?:\s+id=[\"']([^\"']+)[\"'])?\s*>([^<]+?)</\1(?::[a-zA-Z0-9_]+)?>|"
        # 2. Empty enclosing tag: <label:id ...></label>
        r"<([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?(?:\s+id=[\"']([^\"']+)[\"'])?\s*></\5(?::[a-zA-Z0-9_]+)?>|"
        # 3. Self-closing tag: <label:id .../>
        r"<([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?(?:\s+id=[\"']([^\"']+)[\"'])?\s*/>|"
        # 4. Mustache placeholder: {{label:id}}
        r"\{\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}\}|"
        # 5. Standalone single tag: <label:id ...>
        r"<([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?(?:\s+id=[\"']([^\"']+)[\"'])?\s*>",
        re.MULTILINE,
    )

    MARKDOWN_CODEBLOCK_REGEX = re.compile(
        r"^\s*```(?:xml|json|markdown|text)?\s*\n([\s\S]*?)\n\s*```\s*$",
        re.MULTILINE,
    )

    def __init__(
        self,
        generator: Optional[TaiwanPIIGenerator] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.generator = generator or TaiwanPIIGenerator(seed=seed)
        self._validators: Dict[str, Callable[[str], bool]] = {
            "national_id_number": validate_national_id,
            "tw_national_id": validate_national_id,
            "tax_id": validate_tax_id,
            "tw_company_id": validate_tax_id,
            "phone_number": validate_phone_number,
            "private_phone": validate_phone_number,
            "payment_card": validate_credit_card,
            "card_cvv": validate_card_cvv,
            "bank_account": validate_bank_account,
            "account_number": validate_bank_account,
            "tw_nhi_card": validate_nhi_card,
            "license_plate": validate_license_plate,
            "tw_license_plate": validate_license_plate,
            "passport_number": validate_passport_number,
            "tw_passport": validate_passport_number,
            "tw_line_id": validate_line_id,
            "tw_ptt_id": validate_ptt_id,
            "tw_household_no": validate_household_no,
            "tw_medical_license": validate_medical_license,
            "tw_military_id": validate_military_id,
            "email": validate_email,
            "private_email": validate_email,
        }

    @classmethod
    def strip_markdown(cls, raw_text: str) -> str:
        """Removes outer markdown code fences if output was wrapped by an LLM."""
        trimmed = raw_text.strip()
        match = cls.MARKDOWN_CODEBLOCK_REGEX.match(trimmed)
        if match:
            return match.group(1).strip()
        return trimmed

    def is_valid_entity(self, label: str, value: str) -> bool:
        """Checks whether a string value passes algorithmic validation for the given label."""
        spec = TaxonomyMapper.get_spec(label)
        canonical_id = spec.canonical_id if spec else label
        gliner2_label = spec.gliner2_label if spec else label

        validator = (
            self._validators.get(canonical_id)
            or self._validators.get(gliner2_label)
            or self._validators.get(label)
        )
        if validator is None:
            return len(value.strip()) > 0

        return validator(value.strip())

    def parse(
        self,
        raw_text: str,
        normalize_invalid: bool = False,
        strip_inner_whitespace: bool = True,
    ) -> SynthesisResult:
        """
        Parses XML-tagged text or templates into a SynthesisResult with exact character offsets.
        """
        cleaned_source = self.strip_markdown(raw_text)

        spans: List[Span] = []
        assembled_parts: List[str] = []
        current_len = 0
        last_idx = 0

        # Maintain shared bindings for tags with IDs (e.g. person:1)
        tag_id_bindings: Dict[str, str] = {}

        for match in self.TAG_MASTER_REGEX.finditer(cleaned_source):
            start_tag_pos = match.start()
            end_tag_pos = match.end()

            # Identify which branch matched
            if match.group(1) is not None:
                # 1. Enclosing tag with inner content
                raw_label = match.group(1)
                tag_id = match.group(2) or match.group(3)
                inner_content = match.group(4)
            elif match.group(5) is not None:
                # 2. Empty enclosing tag
                raw_label = match.group(5)
                tag_id = match.group(6) or match.group(7)
                inner_content = ""
            elif match.group(8) is not None:
                # 3. Self-closing tag
                raw_label = match.group(8)
                tag_id = match.group(9) or match.group(10)
                inner_content = ""
            elif match.group(11) is not None:
                # 4. Mustache tag
                raw_label = match.group(11)
                tag_id = match.group(12)
                inner_content = ""
            elif match.group(13) is not None:
                # 5. Standalone single tag
                raw_label = match.group(13)
                tag_id = match.group(14) or match.group(15)
                inner_content = ""
            else:
                continue

            # Check if this raw_label is a recognized taxonomy entity
            spec = TaxonomyMapper.get_spec(raw_label)
            if spec is None:
                # If standalone tag is not a known PII label, treat it as static text
                if match.group(13) is not None:
                    continue

            canonical_id = spec.canonical_id if spec else raw_label
            gliner2_label = spec.gliner2_label if spec else raw_label

            # Preceding static text before this tag
            static_text = cleaned_source[last_idx:start_tag_pos]
            if static_text:
                assembled_parts.append(static_text)
                current_len += len(static_text)

            # Handle whitespace inside inner content
            leading_space = ""
            trailing_space = ""
            if strip_inner_whitespace and inner_content:
                stripped_val = inner_content.strip()
                l_len = len(inner_content) - len(inner_content.lstrip())
                r_len = len(inner_content) - len(inner_content.rstrip())
                leading_space = inner_content[:l_len]
                trailing_space = inner_content[len(inner_content) - r_len :] if r_len > 0 else ""
                entity_text = stripped_val
            else:
                entity_text = inner_content

            # Handle tag ID reuse or generation
            binding_key = f"{canonical_id}:{tag_id}" if tag_id else None

            if not entity_text:
                if binding_key and binding_key in tag_id_bindings:
                    entity_text = tag_id_bindings[binding_key]
                else:
                    entity_text = self.generator.generate(canonical_id)
                    if binding_key:
                        tag_id_bindings[binding_key] = entity_text
            else:
                if binding_key:
                    if binding_key in tag_id_bindings:
                        entity_text = tag_id_bindings[binding_key]
                    else:
                        tag_id_bindings[binding_key] = entity_text

            if leading_space:
                assembled_parts.append(leading_space)
                current_len += len(leading_space)

            # Compute exact start and end offsets in clean text
            start_offset = current_len
            end_offset = start_offset + len(entity_text)

            span = Span(
                start=start_offset,
                end=end_offset,
                label=gliner2_label,
                text=entity_text,
                canonical_id=canonical_id,
                metadata={"tag_id": tag_id} if tag_id else {},
            )
            spans.append(span)

            assembled_parts.append(entity_text)
            current_len = end_offset

            if trailing_space:
                assembled_parts.append(trailing_space)
                current_len += len(trailing_space)

            last_idx = end_tag_pos

        # Trailing static text
        trailing_text = cleaned_source[last_idx:]
        if trailing_text:
            assembled_parts.append(trailing_text)

        full_clean_text = "".join(assembled_parts)
        result = SynthesisResult(text=full_clean_text, spans=spans)
        result.validate()

        if normalize_invalid:
            result = self.normalize_invalid_spans(result)

        return result

    def normalize_invalid_spans(self, result: SynthesisResult) -> SynthesisResult:
        """
        Scans all spans in the SynthesisResult; if any entity fails algorithmic validation,
        generates an authentic valid Taiwan replacement and shifts all downstream offsets.
        """
        replacements: Dict[int, str] = {}
        binding_cache: Dict[str, str] = {}

        for idx, span in enumerate(result.spans):
            target_key = span.canonical_id or span.label
            val = span.text

            is_valid = self.is_valid_entity(target_key, val)
            if not is_valid:
                tag_id = span.metadata.get("tag_id")
                cache_key = f"{target_key}:{tag_id}" if tag_id else None

                if cache_key and cache_key in binding_cache:
                    new_val = binding_cache[cache_key]
                else:
                    new_val = self.generator.generate(target_key)
                    if cache_key:
                        binding_cache[cache_key] = new_val

                replacements[idx] = new_val

        if not replacements:
            return result

        return SpanReplacer.replace_spans(
            text=result.text,
            spans=result.spans,
            replacements=replacements,
        )
