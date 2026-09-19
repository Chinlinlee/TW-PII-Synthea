"""
Unified Taiwan PII Generator Hub.
Provides single-entry generation for all 21 canonical PII entity labels.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, Optional

from pii_synthea.generators.address import generate_address, generate_postal_code
from pii_synthea.generators.business import generate_tax_id
from pii_synthea.generators.financial import (
    generate_bank_account,
    generate_card_cvv,
    generate_payment_card,
)
from pii_synthea.generators.id_card import (
    generate_household_no,
    generate_national_id,
)
from pii_synthea.generators.misc import (
    generate_date_of_birth,
    generate_drivers_license_number,
    generate_email,
    generate_license_plate,
    generate_line_id,
    generate_medical_license,
    generate_military_id,
    generate_nhi_card,
    generate_passport_number,
    generate_ptt_id,
    generate_secret,
)
from pii_synthea.generators.names import generate_person_name
from pii_synthea.generators.phone import generate_phone_number
from pii_synthea.taxonomy import CANONICAL_TAXONOMY, TaxonomyMapper


class TaiwanPIIGenerator:
    """
    Unified generator that produces synthetically valid Taiwan PII for all 21 taxonomy classes.
    Supports random seed configuration for reproducible dataset generation.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self._dispatch_table: Dict[str, Callable[[], str]] = {
            "person": lambda: generate_person_name(rng=self.rng),
            "national_id_number": lambda: generate_national_id(rng=self.rng),
            "tw_nhi_card": lambda: generate_nhi_card(rng=self.rng),
            "tax_id": lambda: generate_tax_id(rng=self.rng),
            "license_plate": lambda: generate_license_plate(rng=self.rng),
            "passport_number": lambda: generate_passport_number(rng=self.rng),
            "drivers_license_number": lambda: generate_drivers_license_number(rng=self.rng),
            "phone_number": lambda: generate_phone_number(rng=self.rng),
            "email": lambda: generate_email(rng=self.rng),
            "address": lambda: generate_address(rng=self.rng).full_address,
            "postal_code": lambda: generate_postal_code(rng=self.rng),
            "date_of_birth": lambda: generate_date_of_birth(rng=self.rng),
            "bank_account": lambda: generate_bank_account(rng=self.rng),
            "payment_card": lambda: generate_payment_card(rng=self.rng),
            "card_cvv": lambda: generate_card_cvv(rng=self.rng),
            "tw_line_id": lambda: generate_line_id(rng=self.rng),
            "tw_ptt_id": lambda: generate_ptt_id(rng=self.rng),
            "tw_household_no": lambda: generate_household_no(rng=self.rng),
            "tw_medical_license": lambda: generate_medical_license(rng=self.rng),
            "tw_military_id": lambda: generate_military_id(rng=self.rng),
            "secret": lambda: generate_secret(rng=self.rng),
        }

    def set_seed(self, seed: Optional[int]) -> None:
        """Resets the internal random number generator seed."""
        self.rng = random.Random(seed)

    def generate(self, label: str) -> str:
        """
        Generates a synthetic value for a given canonical ID or GLiNER2 label.
        
        Args:
            label: Either canonical_id (e.g. 'national_id_number') or GLiNER2 label.
        """
        # Resolve to canonical ID if a GLiNER2 label was passed
        spec = TaxonomyMapper.get_spec(label)
        canonical_id = spec.canonical_id if spec else label

        generator_fn = self._dispatch_table.get(canonical_id)
        if not generator_fn:
            valid_labels = list(self._dispatch_table.keys())
            raise KeyError(f"Unknown PII label: '{label}'. Supported labels are: {valid_labels}")

        return generator_fn()

    def generate_all(self) -> Dict[str, str]:
        """Generates a complete dictionary containing one sample of all 21 entities."""
        return {label: fn() for label, fn in self._dispatch_table.items()}
