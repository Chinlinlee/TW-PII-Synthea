"""
Taiwan Phone Number Generator and Validator.
Covers:
- 09xx Mobile Numbers (Compact, Dashed, Spaced, and International +886 format)
- Regional Landlines (02 Taipei/New Taipei/Keelung, 03, 04, 05, 06, 07 Kaohsiung, 08, 082, 0836)
- Extensions (分機, ext., #)
"""

from __future__ import annotations

import random
import re
from typing import Optional

# Mobile Prefixes (Chunghwa Telecom, Taiwan Mobile, FarEasTone, etc.)
MOBILE_PREFIXES: list[str] = [
    "0910", "0911", "0912", "0918", "0919", "0920", "0921", "0922", "0926",
    "0928", "0930", "0932", "0933", "0935", "0937", "0952", "0953", "0955",
    "0958", "0960", "0963", "0965", "0970", "0972", "0975", "0982", "0987",
    "0988", "0989",
]

# Regional Landline Area Codes and local digit lengths
LANDLINE_REGIONS: dict[str, dict] = {
    "02": {"name": "大台北/基隆", "digits": 8},
    "03": {"name": "桃竹苗/宜花", "digits": 7},
    "04": {"name": "台中/彰化", "digits": 8},
    "05": {"name": "雲林/嘉義", "digits": 7},
    "06": {"name": "台南/澎湖", "digits": 7},
    "07": {"name": "高雄", "digits": 8},
    "08": {"name": "屏東/台東", "digits": 7},
    "082": {"name": "金門", "digits": 6},
    "0836": {"name": "馬祖", "digits": 5},
}


def validate_phone_number(phone_str: str) -> bool:
    """
    Validates a Taiwan mobile or landline phone number.
    Accepts:
    - Mobile: 09xx... or +886-9xx... or +886 9xx...
    - Landline: (0x)... or 0x-...
    """
    if not isinstance(phone_str, str):
        return False

    clean = phone_str.strip()

    # Mobile patterns
    mobile_pattern = r"^(?:\+?886[-\s]?)?0?9\d{2}[-\s]?\d{3}[-\s]?\d{3}$"
    if re.fullmatch(mobile_pattern, clean):
        return True

    # Landline patterns (with optional extension)
    landline_pattern = r"^(?:\(0[2-8]\)|0[2-8][-\s]?)\s*\d{3,4}[-\s]?\d{4}(?:\s*(?:分機|ext\.?|#)\s*\d{1,5})?$"
    if re.fullmatch(landline_pattern, clean, re.IGNORECASE):
        return True

    # Matsu/Kinmen
    island_pattern = r"^(?:082|0836)[-\s]?\d{5,6}$"
    if re.fullmatch(island_pattern, clean):
        return True

    return False


def generate_mobile_number(
    format_style: str = "dashed",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan mobile number (09xx).
    
    Args:
        format_style: 'dashed' (0912-345-678), 'compact' (0912345678),
                      'spaced' (0912 345 678), 'intl_dashed' (+886-912-345-678),
                      'intl_spaced' (+886 912 345 678), 'intl_compact' (+886912345678).
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random
    prefix = r.choice(MOBILE_PREFIXES)
    part2 = f"{r.randint(0, 999):03d}"
    part3 = f"{r.randint(0, 999):03d}"

    if format_style == "compact":
        return f"{prefix}{part2}{part3}"
    elif format_style == "spaced":
        return f"{prefix} {part2} {part3}"
    elif format_style == "intl_dashed":
        return f"+886-{prefix[1:]}-{part2}-{part3}"
    elif format_style == "intl_spaced":
        return f"+886 {prefix[1:]} {part2} {part3}"
    elif format_style == "intl_compact":
        return f"+886{prefix[1:]}{part2}{part3}"
    else:  # 'dashed'
        return f"{prefix}-{part2}-{part3}"


def generate_landline_number(
    area_code: Optional[str] = None,
    include_extension: bool = False,
    format_style: str = "dashed",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan landline phone number.
    
    Args:
        area_code: Optional code like '02', '04', '07', etc.
        include_extension: Whether to append an extension (e.g. 分機 123).
        format_style: 'dashed', 'parentheses', or 'compact'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if not area_code or area_code not in LANDLINE_REGIONS:
        area_code = r.choice(["02", "03", "04", "07", "06", "05", "08"])

    info = LANDLINE_REGIONS[area_code]
    num_digits = info["digits"]

    if num_digits == 8:
        # e.g. 2345-6789
        p1 = f"{r.randint(2, 8)}{r.randint(0, 999):03d}"
        p2 = f"{r.randint(0, 9999):04d}"
        local_dashed = f"{p1}-{p2}"
        local_compact = f"{p1}{p2}"
    else:
        # e.g. 7 digits: 512-3456
        p1 = f"{r.randint(2, 9)}{r.randint(0, 99):02d}"
        p2 = f"{r.randint(0, 9999):04d}"
        local_dashed = f"{p1}-{p2}"
        local_compact = f"{p1}{p2}"

    if format_style == "parentheses":
        base_phone = f"({area_code}) {local_dashed}"
    elif format_style == "compact":
        base_phone = f"{area_code}{local_compact}"
    else:  # dashed
        base_phone = f"{area_code}-{local_dashed}"

    if include_extension:
        ext_num = r.randint(10, 9999)
        ext_style = r.choice([" 分機 ", " ext. ", " #"])
        base_phone = f"{base_phone}{ext_style}{ext_num}"

    return base_phone


def generate_phone_number(
    phone_type: str = "any",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Unified phone generator.
    
    Args:
        phone_type: 'mobile', 'landline', or 'any' (75% mobile, 25% landline).
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if phone_type == "any":
        phone_type = "mobile" if r.random() < 0.75 else "landline"

    if phone_type == "mobile":
        style = r.choice(["dashed", "compact", "spaced", "intl_dashed", "intl_compact"])
        return generate_mobile_number(format_style=style, rng=rng)
    else:
        style = r.choice(["dashed", "parentheses", "compact"])
        ext = r.random() < 0.2
        return generate_landline_number(include_extension=ext, format_style=style, rng=rng)
