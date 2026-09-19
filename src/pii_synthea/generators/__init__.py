"""
Taiwan Synthetic PII Generators and Offset-Preserving Span Engine.
"""

from pii_synthea.generators.address import (
    TAIWAN_ADMIN_DIVISIONS,
    GeneratedAddress,
    generate_address,
    generate_postal_code,
    validate_postal_code,
)
from pii_synthea.generators.business import (
    FAMOUS_TAIWAN_COMPANIES,
    calculate_tax_id_checksum_sum,
    generate_tax_id,
    validate_tax_id,
)
from pii_synthea.generators.financial import (
    TAIWAN_BANK_CODES,
    generate_bank_account,
    generate_card_cvv,
    generate_payment_card,
    validate_bank_account,
    validate_card_cvv,
    validate_credit_card,
)
from pii_synthea.generators.id_card import (
    COUNTY_LETTER_CODES,
    calculate_id_check_digit,
    generate_household_no,
    generate_national_id,
    validate_household_no,
    validate_national_id,
)
from pii_synthea.generators.master import TaiwanPIIGenerator
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
    validate_email,
    validate_license_plate,
    validate_line_id,
    validate_medical_license,
    validate_military_id,
    validate_nhi_card,
    validate_passport_number,
    validate_ptt_id,
)
from pii_synthea.generators.names import generate_person_name
from pii_synthea.generators.phone import (
    generate_landline_number,
    generate_mobile_number,
    generate_phone_number,
    validate_phone_number,
)
from pii_synthea.generators.replacement import (
    Span,
    SpanReplacer,
    SynthesisResult,
    TemplateEngine,
)

__all__ = [
    # Master Hub
    "TaiwanPIIGenerator",
    # Span & Replacement Engine
    "Span",
    "SynthesisResult",
    "TemplateEngine",
    "SpanReplacer",
    # ID Card
    "generate_national_id",
    "validate_national_id",
    "calculate_id_check_digit",
    "generate_household_no",
    "validate_household_no",
    "COUNTY_LETTER_CODES",
    # Business / Tax ID
    "generate_tax_id",
    "validate_tax_id",
    "calculate_tax_id_checksum_sum",
    "FAMOUS_TAIWAN_COMPANIES",
    # Address & Postal Code
    "generate_address",
    "generate_postal_code",
    "validate_postal_code",
    "GeneratedAddress",
    "TAIWAN_ADMIN_DIVISIONS",
    # Names
    "generate_person_name",
    # Phone
    "generate_phone_number",
    "generate_mobile_number",
    "generate_landline_number",
    "validate_phone_number",
    # Financial
    "generate_payment_card",
    "validate_credit_card",
    "generate_card_cvv",
    "validate_card_cvv",
    "generate_bank_account",
    "validate_bank_account",
    "TAIWAN_BANK_CODES",
    # Misc
    "generate_nhi_card",
    "validate_nhi_card",
    "generate_license_plate",
    "validate_license_plate",
    "generate_passport_number",
    "validate_passport_number",
    "generate_drivers_license_number",
    "generate_date_of_birth",
    "generate_line_id",
    "validate_line_id",
    "generate_ptt_id",
    "validate_ptt_id",
    "generate_medical_license",
    "validate_medical_license",
    "generate_military_id",
    "validate_military_id",
    "generate_email",
    "validate_email",
    "generate_secret",
]
