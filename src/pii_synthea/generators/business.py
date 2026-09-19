"""
Taiwan Unified Business Number (統編 / Tax ID) Generator & Validator.
Covers:
- 8-digit Unified Business Number (UBN / 營利事業統一編號)
- Ministry of Finance (MOF) checksum logic (mod 10 and 7th digit = 7 exception)
- Known real-world corporate Tax IDs for realistic domain testing
"""

from __future__ import annotations

import random
from typing import Optional

_UBN_WEIGHTS: list[int] = [1, 2, 1, 2, 1, 2, 4, 1]

# Well-known reference corporations in Taiwan
FAMOUS_TAIWAN_COMPANIES: dict[str, str] = {
    "台積電": "22099131",  # 台灣積體電路製造
    "鴻海": "04541302",    # 鴻海精密工業
    "聯發科": "84149961",  # 聯發科技
    "中華電信": "96979933",# 中華電信
    "統一超商": "22555003",# 統一超商 (7-Eleven)
    "富邦金控": "03374805",# 富邦金融控股
    "國泰金控": "70827406",# 國泰金融控股
    "台達電": "34051920",  # 台達電子
    "華碩": "23638777",    # 華碩電腦 (Real-world example of 7th digit=7 special rule)
    "廣達": "22822281",    # 廣達電腦
}


def calculate_tax_id_checksum_sum(digits_8: list[int]) -> int:
    """
    Computes sum of cross-products according to Taiwan MOF rules:
    sum((d * w) // 10 + (d * w) % 10)
    """
    total = 0
    for d, w in zip(digits_8, _UBN_WEIGHTS):
        prod = d * w
        total += (prod // 10) + (prod % 10)
    return total


def validate_tax_id(tax_id: str) -> bool:
    """
    Validates a Taiwan 8-digit Unified Business Number (統編).
    Ministry of Finance standard:
    - 8 digits.
    - Weighted cross-product sum mod 10 == 0.
    - If 7th digit (index 6) is '7', (sum - 1) mod 10 == 0 is also accepted.
    """
    if not isinstance(tax_id, str):
        return False

    tax_id_clean = tax_id.strip()
    if len(tax_id_clean) != 8 or not tax_id_clean.isdigit():
        return False

    digits = [int(ch) for ch in tax_id_clean]
    total = calculate_tax_id_checksum_sum(digits)

    if total % 10 == 0:
        return True

    # Special case when 7th digit is 7: 7 * 4 = 28. (2+8=10 -> 1+0=1 vs 0)
    if digits[6] == 7 and (total - 1) % 10 == 0:
        return True

    return False


def generate_tax_id(
    force_seventh_digit_seven: bool = False,
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates an algorithmically valid Taiwan 8-digit Unified Business Number.
    
    Args:
        force_seventh_digit_seven: If True, forces the 7th digit to be 7 (testing the edge case).
        rng: Optional random.Random instance for seeded reproducibility.
    """
    r = rng if rng is not None else random

    # Generate first 7 digits
    digits_7 = [r.randint(0, 9) for _ in range(7)]
    if force_seventh_digit_seven:
        digits_7[6] = 7

    # Calculate sum of first 7 digits
    subtotal = 0
    for d, w in zip(digits_7, _UBN_WEIGHTS[:7]):
        prod = d * w
        subtotal += (prod // 10) + (prod % 10)

    # Since weight for 8th digit is 1: prod = d8 * 1 < 10, so sum contribution is d8.
    # We want (subtotal + d8) % 10 == 0
    # Therefore d8 = (10 - (subtotal % 10)) % 10
    d8 = (10 - (subtotal % 10)) % 10

    digits_8 = digits_7 + [d8]
    ubn = "".join(str(d) for d in digits_8)

    # Double check sanity
    assert validate_tax_id(ubn), f"Generated invalid UBN: {ubn}"
    return ubn
