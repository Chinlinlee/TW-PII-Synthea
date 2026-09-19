"""
Offset-Preserving Span Replacement Engine & Synthesis Result Validator.
Guarantees 100% character-level annotation integrity:
- Exact span verification: assert text[span.start:span.end] == span.text
- Boundary preservation & collision prevention
- Template-based dynamic replacement with deterministic variable binding
- In-place span replacement and downstream offset shifting
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from pii_synthea.generators.master import TaiwanPIIGenerator
from pii_synthea.taxonomy import TaxonomyMapper


@dataclass
class Span:
    """Represents a character-level entity span annotation."""
    start: int
    end: int
    label: str
    text: str
    canonical_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "start": self.start,
            "end": self.end,
            "label": self.label,
            "text": self.text,
        }
        if self.canonical_id:
            d["canonical_id"] = self.canonical_id
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class SynthesisResult:
    """Holds synthesized text alongside exact character-level entity span annotations."""
    text: str
    spans: List[Span]

    def validate(self) -> bool:
        """
        Rigorous verification of span boundary integrity:
        1. assert 0 <= span.start < span.end <= len(text)
        2. assert text[span.start:span.end] == span.text
        3. assert no overlapping spans
        Raises ValueError if any condition fails.
        """
        text_len = len(self.text)
        for i, s in enumerate(self.spans):
            if s.start < 0 or s.end > text_len or s.start >= s.end:
                raise ValueError(
                    f"Span boundary invalid at index {i}: [{s.start}, {s.end}] for text length {text_len}"
                )

            extracted = self.text[s.start:s.end]
            if extracted != s.text:
                raise ValueError(
                    f"Span text mismatch at [{s.start}:{s.end}] for label '{s.label}': "
                    f"expected '{s.text}', but found '{extracted}' in text."
                )

        # Check for overlaps
        sorted_spans = sorted(self.spans, key=lambda s: s.start)
        for i in range(len(sorted_spans) - 1):
            curr_s = sorted_spans[i]
            next_s = sorted_spans[i + 1]
            if curr_s.end > next_s.start:
                raise ValueError(
                    f"Overlapping spans detected between '{curr_s.text}' [{curr_s.start}:{curr_s.end}] "
                    f"and '{next_s.text}' [{next_s.start}:{next_s.end}]"
                )

        return True

    def to_gliner2_format(self) -> Dict[str, Any]:
        """Converts to GLiNER2 training item format."""
        self.validate()
        return {
            "text": self.text,
            "spans": [
                {"start": s.start, "end": s.end, "label": s.label, "text": s.text}
                for s in sorted(self.spans, key=lambda x: x.start)
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "spans": [s.to_dict() for s in sorted(self.spans, key=lambda x: x.start)],
        }


class TemplateEngine:
    """
    Renders templates containing PII placeholder tags into validated SynthesisResults.
    
    Supports placeholder formats:
    - Mustache: `{{person}}`, `{{national_id_number}}`
    - XML/Tag: `<person>`, `<national_id_number>`
    - Indexed: `{{person:1}}` (subsequent occurrences of `{{person:1}}` reuse the same value)
    """

    # Matches {{label}} or {{label:id}} or <label> or <label:id>
    PLACEHOLDER_REGEX = re.compile(
        r"\{\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}\}|<([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?>"
    )

    def __init__(
        self,
        generator: Optional[TaiwanPIIGenerator] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.generator = generator or TaiwanPIIGenerator(seed=seed)

    def render(
        self,
        template: str,
        context: Optional[Dict[str, str]] = None,
        custom_generators: Optional[Dict[str, Callable[[], str]]] = None,
    ) -> SynthesisResult:
        """
        Renders a template string by replacing placeholders with synthetic PII values
        and tracking exact character offsets.
        
        Args:
            template: String with placeholders like '您好 {{person:1}}，身分證為 {{national_id_number:1}}'
            context: Optional predefined values for indexed tags, e.g. {'person:1': '陳大明'}
            custom_generators: Optional overrides for specific labels
        """
        bound_values: Dict[str, str] = dict(context or {})
        spans: List[Span] = []
        assembled_parts: List[str] = []
        current_len = 0
        last_idx = 0

        for match in self.PLACEHOLDER_REGEX.finditer(template):
            # Non-placeholder static text before this tag
            static_text = template[last_idx:match.start()]
            if static_text:
                assembled_parts.append(static_text)
                current_len += len(static_text)

            # Determine label and identifier
            if match.group(1) is not None:
                # Mustache format: {{label:id}}
                label = match.group(1)
                tag_id = match.group(2)
            else:
                # Tag format: <label:id>
                label = match.group(3)
                tag_id = match.group(4)

            # Key for binding (e.g. 'person:1' or 'tax_id')
            binding_key = f"{label}:{tag_id}" if tag_id else None

            # Retrieve or generate value
            if binding_key and binding_key in bound_values:
                val = bound_values[binding_key]
            elif custom_generators and label in custom_generators:
                val = custom_generators[label]()
                if binding_key:
                    bound_values[binding_key] = val
            else:
                val = self.generator.generate(label)
                if binding_key:
                    bound_values[binding_key] = val

            # Compute exact start and end offsets in assembled text
            start_offset = current_len
            end_offset = start_offset + len(val)

            # Map label to GLiNER2 label
            spec = TaxonomyMapper.get_spec(label)
            gliner2_label = spec.gliner2_label if spec else label
            canonical_id = spec.canonical_id if spec else label

            spans.append(
                Span(
                    start=start_offset,
                    end=end_offset,
                    label=gliner2_label,
                    text=val,
                    canonical_id=canonical_id,
                )
            )

            assembled_parts.append(val)
            current_len = end_offset
            last_idx = match.end()

        # Trailing static text
        trailing_text = template[last_idx:]
        if trailing_text:
            assembled_parts.append(trailing_text)

        full_text = "".join(assembled_parts)
        result = SynthesisResult(text=full_text, spans=spans)
        result.validate()
        return result


class SpanReplacer:
    """
    Performs dynamic replacement of existing spans in an annotated text,
    properly shifting downstream offsets and validating the transformed text.
    """

    @staticmethod
    def replace_spans(
        text: str,
        spans: Sequence[Span],
        replacements: Dict[int, str],
    ) -> SynthesisResult:
        """
        Replaces spans at specified indices with new values, updating all offsets.
        
        Args:
            text: Source text.
            spans: Existing list of Span objects.
            replacements: Mapping from span index (in `spans`) to new text value.
        """
        # Sort replacements in reverse order of span start index (right-to-left)
        # to ensure that edits do not invalidate earlier offsets
        indexed_spans = list(enumerate(spans))
        # Ensure all existing spans are valid initially
        temp_result = SynthesisResult(text=text, spans=list(spans))
        temp_result.validate()

        current_text = text
        new_spans = [
            Span(
                start=s.start,
                end=s.end,
                label=s.label,
                text=s.text,
                canonical_id=s.canonical_id,
                metadata=dict(s.metadata),
            )
            for s in spans
        ]

        # Process from right to left (descending order of start index)
        sorted_by_pos = sorted(indexed_spans, key=lambda x: x[1].start, reverse=True)

        for orig_idx, span in sorted_by_pos:
            if orig_idx not in replacements:
                continue

            new_val = replacements[orig_idx]
            old_val_len = span.end - span.start
            delta = len(new_val) - old_val_len

            # Replace in text
            current_text = current_text[:span.start] + new_val + current_text[span.end:]

            # Update the replaced span itself
            new_spans[orig_idx].text = new_val
            new_spans[orig_idx].end = span.start + len(new_val)

            # Shift all spans strictly after this span to the right
            for j, other in enumerate(new_spans):
                if j != orig_idx and other.start >= span.end:
                    other.start += delta
                    other.end += delta

        result = SynthesisResult(text=current_text, spans=new_spans)
        result.validate()
        return result
