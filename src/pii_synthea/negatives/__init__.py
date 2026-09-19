"""
Taiwan Hard Negatives Synthesis Subsystem (Ticket 05).
Generates context-rich synthetic data containing entities that mimic PII
(brand names with person names, public figures, landmarks, hotlines, public emails, code numbers)
without labeling them as private personal data.
"""

from pii_synthea.negatives.catalog import (
    HardNegativeCatalog,
    HardNegativeCategory,
    HardNegativeItem,
)
from pii_synthea.negatives.generator import HardNegativeSynthesizer
from pii_synthea.negatives.templates import (
    HardNegativeTemplateLibrary,
    MixedNegativeTemplate,
    PureNegativeTemplate,
)

__all__ = [
    "HardNegativeCategory",
    "HardNegativeItem",
    "HardNegativeCatalog",
    "PureNegativeTemplate",
    "MixedNegativeTemplate",
    "HardNegativeTemplateLibrary",
    "HardNegativeSynthesizer",
]
