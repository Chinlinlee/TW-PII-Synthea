"""
Validation Gate for Synthetic PII Samples.
Enforces character-level span integrity, boundary validity, non-overlap, and label validity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from pii_synthea.generators.replacement import Span, SynthesisResult
from pii_synthea.taxonomy import TaxonomyMapper


@dataclass
class ValidationReport:
    """Report detailing validation status and detected errors."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    span_count: int = 0
    text_length: int = 0

    def add_error(self, err: str) -> None:
        self.errors.append(err)
        self.is_valid = False


class ValidationGate:
    """
    Validates synthesized PII items with zero-tolerance integrity checks:
    1. 0 <= span.start < span.end <= len(text)
    2. text[span.start:span.end] == span.text
    3. No overlapping spans (prev.end <= curr.start)
    4. Canonical label compatibility
    """

    def __init__(self, check_taxonomy: bool = False) -> None:
        self.check_taxonomy = check_taxonomy
        self.valid_labels = set(TaxonomyMapper.all_canonical_ids()) if check_taxonomy else set()

    def validate(self, item: Union[SynthesisResult, Dict[str, Any]]) -> ValidationReport:
        """
        Validates a SynthesisResult or raw dictionary.
        Returns a ValidationReport.
        """
        if isinstance(item, SynthesisResult):
            text = item.text
            spans = item.spans
        elif isinstance(item, dict):
            text = item.get("text", "")
            raw_spans = item.get("spans", [])
            spans = [
                Span(
                    start=s["start"],
                    end=s["end"],
                    label=s["label"],
                    text=s["text"],
                    canonical_id=s.get("canonical_id"),
                )
                for s in raw_spans
            ]
        else:
            report = ValidationReport(is_valid=False, errors=[f"Unsupported item type: {type(item)}"])
            return report

        report = ValidationReport(
            is_valid=True,
            errors=[],
            span_count=len(spans),
            text_length=len(text),
        )

        text_len = len(text)

        # Validate each span individually
        for i, s in enumerate(spans):
            if s.start < 0 or s.end > text_len or s.start >= s.end:
                report.add_error(
                    f"Span index {i} out of bounds: [{s.start}, {s.end}] for text length {text_len}"
                )
                continue

            extracted = text[s.start : s.end]
            if extracted != s.text:
                report.add_error(
                    f"Span text mismatch at [{s.start}:{s.end}] for label '{s.label}': "
                    f"expected '{s.text}', but found '{extracted}'"
                )

            if self.check_taxonomy and self.valid_labels:
                cid = s.canonical_id or s.label
                if cid not in self.valid_labels:
                    report.add_error(f"Unrecognized canonical label: '{cid}' at [{s.start}:{s.end}]")

        # Check for overlaps
        sorted_spans = sorted(spans, key=lambda s: s.start)
        for i in range(len(sorted_spans) - 1):
            curr_s = sorted_spans[i]
            next_s = sorted_spans[i + 1]
            if curr_s.end > next_s.start:
                report.add_error(
                    f"Overlapping spans detected between '{curr_s.text}' [{curr_s.start}:{curr_s.end}] "
                    f"and '{next_s.text}' [{next_s.start}:{next_s.end}]"
                )

        return report
