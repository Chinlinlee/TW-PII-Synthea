"""
Financial PII Generators & Validators.
Covers:
- Payment Card (Credit/Debit Card) with valid Luhn checksum (Visa, Mastercard, JCB)
- Card CVV/CVC (3 or 4 digits)
- Taiwan Bank Account Numbers (Commercial Banks and Chunghwa Post)
"""

from __future__ import annotations

import random
import re
from typing import Optional

# Common Taiwan Financial Institution Codes
TAIWAN_BANK_CODES: dict[str, str] = {
    "004": "台灣銀行 (Bank of Taiwan)",
    "005": "土地銀行 (Land Bank of Taiwan)",
    "006": "合作金庫 (Taiwan Cooperative Bank)",
    "007": "第一銀行 (First Bank)",
    "008": "華南銀行 (Hua Nan Bank)",
    "009": "彰化銀行 (Chang Hwa Bank)",
    "011": "上海商銀 (Shanghai Commercial Bank)",
    "012": "台北富邦 (Taipei Fubon Bank)",
    "013": "國泰世華 (Cathay United Bank)",
    "017": "兆豐銀行 (Mega International Commercial Bank)",
    "050": "台灣企銀 (Taiwan Business Bank)",
    "700": "中華郵政 (Chunghwa Post)",
    "808": "玉山銀行 (E.SUN Bank)",
    "812": "台新銀行 (Taishin International Bank)",
    "822": "中國信託 (CTBC Bank)",
}


def calculate_luhn_check_digit(number_without_check: str) -> int:
    """
    Computes the Luhn check digit for a string of digits.
    """
    digits = [int(ch) for ch in number_without_check]
    total = 0
    # From right to left, double every second digit starting from the rightmost
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:  # this will become an odd index from right when check digit is added
            d *= 2
            if d > 9:
                d -= 9
        total += d
    check_digit = (10 - (total % 10)) % 10
    return check_digit


def validate_credit_card(card_number: str) -> bool:
    """
    Validates a credit card number using the Luhn algorithm.
    Accepts raw digits or numbers formatted with dashes/spaces.
    Length must be between 13 and 19 digits (standard: 16 digits).
    """
    if not isinstance(card_number, str):
        return False

    clean = re.sub(r"[-\s]", "", card_number.strip())
    if not clean.isdigit() or not (13 <= len(clean) <= 19):
        return False

    digits = [int(d) for d in clean]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def generate_payment_card(
    card_brand: Optional[str] = None,
    format_style: str = "dashed",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a Luhn-valid 16-digit credit/debit card number.
    
    Args:
        card_brand: 'visa', 'mastercard', 'jcb', or None (random).
        format_style: 'dashed' (XXXX-XXXX-XXXX-XXXX), 'spaced', or 'compact'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if not card_brand or card_brand not in ("visa", "mastercard", "jcb"):
        card_brand = r.choice(["visa", "mastercard", "jcb"])

    if card_brand == "visa":
        prefix = "4" + "".join(str(r.randint(0, 9)) for _ in range(5))  # 6-digit BIN
    elif card_brand == "mastercard":
        bin_start = r.choice(["51", "52", "53", "54", "55", "22", "27"])
        prefix = bin_start + "".join(str(r.randint(0, 9)) for _ in range(4))
    else:  # JCB
        prefix = "35" + "".join(str(r.randint(28, 89))[:2]) + "".join(str(r.randint(0, 9)) for _ in range(2))

    # Generate next 9 digits (total 15 digits so far)
    body = "".join(str(r.randint(0, 9)) for _ in range(15 - len(prefix)))
    fifteen_digits = prefix + body

    check_digit = calculate_luhn_check_digit(fifteen_digits)
    sixteen_digits = f"{fifteen_digits}{check_digit}"

    assert validate_credit_card(sixteen_digits), f"Luhn validation failed for {sixteen_digits}"

    if format_style == "dashed":
        return f"{sixteen_digits[:4]}-{sixteen_digits[4:8]}-{sixteen_digits[8:12]}-{sixteen_digits[12:]}"
    elif format_style == "spaced":
        return f"{sixteen_digits[:4]} {sixteen_digits[4:8]} {sixteen_digits[8:12]} {sixteen_digits[12:]}"
    else:
        return sixteen_digits


def validate_card_cvv(cvv: str) -> bool:
    """
    Validates a credit card CVV/CVC code (3 or 4 digits).
    """
    if not isinstance(cvv, str):
        return False
    return bool(re.fullmatch(r"\d{3,4}", cvv.strip()))


def generate_card_cvv(
    digits: int = 3,
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a card security code (CVV/CVC).
    """
    r = rng if rng is not None else random
    if digits == 4:
        return f"{r.randint(0, 9999):04d}"
    return f"{r.randint(0, 999):03d}"


def validate_bank_account(acc: str) -> bool:
    """
    Validates a Taiwan bank account number (10 to 16 digits, with optional bank code and dashes).
    """
    if not isinstance(acc, str):
        return False
    clean = re.sub(r"[-\s]", "", acc.strip())
    return clean.isdigit() and 10 <= len(clean) <= 16


def generate_bank_account(
    bank_code: Optional[str] = None,
    format_style: str = "compact",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan bank or postal savings account number.
    
    Args:
        bank_code: Optional 3-digit bank code (e.g. '700', '013', '822').
        format_style: 'compact' or 'dashed'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if not bank_code or bank_code not in TAIWAN_BANK_CODES:
        bank_code = r.choice(list(TAIWAN_BANK_CODES.keys()))

    if bank_code == "700":
        # Chunghwa Post: 14 digits (often 7 digits account + 7 digits book)
        part1 = f"{r.randint(0, 9999999):07d}"
        part2 = f"{r.randint(0, 9999999):07d}"
        if format_style == "dashed":
            return f"700-{part1}-{part2}"
        return f"{part1}{part2}"
    else:
        # Commercial banks: typically 12 to 14 digits
        acc_len = r.choice([12, 13, 14])
        acc_body = "".join(str(r.randint(0, 9)) for _ in range(acc_len))
        if format_style == "dashed" and r.random() < 0.5:
            return f"{bank_code}-{acc_body}"
        return acc_body
