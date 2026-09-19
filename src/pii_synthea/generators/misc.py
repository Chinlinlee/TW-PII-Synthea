"""
Miscellaneous Taiwan PII Generators and Validators.
Covers:
- Taiwan National Health Insurance (NHI) Card Number (12 digits)
- Vehicle License Plates (New and Old formats for autos and motorcycles)
- Taiwan Passport Number (9 digits or alphanumeric)
- Driver's License Number
- Dates of Birth (ROC / 民國 calendar and Gregorian ISO calendar)
- LINE ID & PTT BBS ID
- Professional & Military IDs (Medical license, Military ID)
- Email Address (Personal & Taiwanese ISP domains)
- Credentials & Secrets (OTP, Passwords, API Keys)
"""

from __future__ import annotations

import random
import re
from typing import Optional

from pii_synthea.generators.id_card import generate_national_id

# Common Email Domains in Taiwan
TAIWAN_EMAIL_DOMAINS: list[str] = [
    "gmail.com", "yahoo.com.tw", "msa.hinet.net", "hotmail.com",
    "outlook.com", "pchome.com.tw", "seed.net.tw", "ntu.edu.tw",
    "nctu.edu.tw", "ithome.com.tw", "company.com.tw",
]

# Medical License Prefixes (Ministry of Health and Welfare)
MEDICAL_PREFIXES: list[str] = [
    "醫字第", "護理字第", "藥字第", "醫檢字第", "物理治療字第", "齒字第",
]

# Military ID Prefixes (Ministry of National Defense)
MILITARY_PREFIXES: list[str] = [
    "陸字第", "海字第", "空字第", "憲字第", "聯字第",
]


# ── NHI Card (健保卡) ─────────────────────────────────────────────────────────


def validate_nhi_card(nhi_str: str) -> bool:
    """
    Validates a Taiwan National Health Insurance (NHI) card number (12 digits).
    """
    if not isinstance(nhi_str, str):
        return False
    clean = re.sub(r"[-\s]", "", nhi_str.strip())
    return clean.isdigit() and len(clean) == 12


def generate_nhi_card(
    format_style: str = "compact",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a 12-digit Taiwan NHI IC card number.
    
    Args:
        format_style: 'compact' (000012345678), 'spaced' (0000 1234 5678), or 'dashed' (0000-1234-5678).
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random
    prefix = r.choice(["0000", "0001", "0002"])
    part2 = f"{r.randint(0, 9999):04d}"
    part3 = f"{r.randint(0, 9999):04d}"

    if format_style == "spaced":
        return f"{prefix} {part2} {part3}"
    elif format_style == "dashed":
        return f"{prefix}-{part2}-{part3}"
    return f"{prefix}{part2}{part3}"


# ── Vehicle License Plate (車牌號碼) ──────────────────────────────────────────


def validate_license_plate(plate_str: str) -> bool:
    """
    Validates a Taiwan vehicle license plate number.
    Supports:
    - New Auto: [A-Z]{3}-\\d{4} or [A-Z]{2}-\\d{4}
    - Old Auto: \\d{4}-[A-Z]{2} or \\d{3}-[A-Z]{2}
    - Motorcycle: [A-Z]{3}-\\d{3} or \\d{3}-[A-Z]{3}
    """
    if not isinstance(plate_str, str):
        return False
    clean = plate_str.strip().upper()
    patterns = [
        r"^[A-Z]{2,3}-\d{4}$",  # New Auto
        r"^\d{3,4}-[A-Z]{2}$",  # Old Auto
        r"^[A-Z]{3}-\d{3}$",    # Motorcycle
        r"^\d{3}-[A-Z]{3}$",    # Motorcycle
        r"^[A-Z]{2}-\d{3}$",    # Light scooter
    ]
    return any(re.fullmatch(p, clean) for p in patterns)


def generate_license_plate(
    plate_type: str = "any",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan vehicle license plate.
    
    Args:
        plate_type: 'new_car' (ABC-1234), 'old_car' (1234-AB), 'motorcycle' (ABC-123), or 'any'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # I and O often omitted in vehicle plates

    if plate_type == "any":
        plate_type = r.choice(["new_car", "new_car", "old_car", "motorcycle"])

    if plate_type == "new_car":
        prefix_len = r.choice([2, 3])
        prefix = "".join(r.choice(letters) for _ in range(prefix_len))
        num = f"{r.randint(100, 9999):04d}"
        return f"{prefix}-{num}"
    elif plate_type == "old_car":
        num_len = r.choice([3, 4])
        num = "".join(str(r.randint(0, 9)) for _ in range(num_len))
        suf = "".join(r.choice(letters) for _ in range(2))
        return f"{num}-{suf}"
    else:  # motorcycle
        prefix = "".join(r.choice(letters) for _ in range(3))
        num = f"{r.randint(10, 999):03d}"
        return f"{prefix}-{num}"


# ── Passport Number (護照號碼) ────────────────────────────────────────────────


def validate_passport_number(passport_str: str) -> bool:
    """
    Validates a Taiwan passport number (9 digits, typically starting with 3, or [A-Z]\\d{8}).
    """
    if not isinstance(passport_str, str):
        return False
    clean = passport_str.strip().upper()
    return bool(re.fullmatch(r"3\d{8}|[A-Z]\d{8}|\d{9}", clean))


def generate_passport_number(
    style: str = "electronic",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a Taiwan passport number.
    Electronic biometric passports start with '3' followed by 8 digits (9 digits total).
    """
    r = rng if rng is not None else random
    if style == "electronic":
        return f"3{r.randint(0, 99999999):08d}"
    else:
        letter = r.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
        return f"{letter}{r.randint(0, 99999999):08d}"


# ── Driver's License Number (駕駛執照號碼) ─────────────────────────────────────


def generate_drivers_license_number(
    style: str = "national_id",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a Taiwan driver's license number (usually identical to National ID,
    or formatted with administrative jurisdiction prefix).
    """
    r = rng if rng is not None else random
    if style == "national_id":
        return generate_national_id(rng=r)
    else:
        prefix = r.choice(["北市字第", "高市字第", "新北字第", "中市字第", "南市字第"])
        num = f"{r.randint(100000, 999999)}號"
        return f"{prefix}{num}"


# ── Sensitive Dates & Date of Birth (出生日期與民國紀年) ──────────────────────


def generate_date_of_birth(
    calendar_type: str = "any",
    min_age: int = 18,
    max_age: int = 75,
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic birth date in either Taiwan ROC calendar (民國) or Gregorian calendar.
    
    Args:
        calendar_type: 'roc' (民國xx年x月x日), 'gregorian' (YYYY-MM-DD), or 'any'.
        min_age: Minimum age in years.
        max_age: Maximum age in years.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random
    current_year = 2026
    birth_year = current_year - r.randint(min_age, max_age)
    roc_year = birth_year - 1911
    month = r.randint(1, 12)
    day = r.randint(1, 28)

    if calendar_type == "any":
        calendar_type = "roc" if r.random() < 0.65 else "gregorian"

    if calendar_type == "roc":
        format_variant = r.choice(["standard", "compact_slash", "compact_dash"])
        if format_variant == "standard":
            return f"民國{roc_year}年{month}月{day}日"
        elif format_variant == "compact_slash":
            return f"{roc_year}/{month:02d}/{day:02d}"
        else:
            return f"{roc_year}-{month:02d}-{day:02d}"
    else:
        format_variant = r.choice(["iso", "slash", "zh"])
        if format_variant == "iso":
            return f"{birth_year}-{month:02d}-{day:02d}"
        elif format_variant == "slash":
            return f"{birth_year}/{month:02d}/{day:02d}"
        else:
            return f"{birth_year}年{month}月{day}日"


# ── Social IDs: LINE ID & PTT ID ──────────────────────────────────────────────


def validate_line_id(line_id: str) -> bool:
    """
    Validates a LINE user ID (4 to 20 alphanumeric characters, dots, or underscores).
    """
    if not isinstance(line_id, str):
        return False
    return bool(re.fullmatch(r"[a-zA-Z0-9._]{4,20}", line_id.strip()))


def generate_line_id(rng: Optional[random.Random] = None) -> str:
    """
    Generates a realistic LINE user ID.
    """
    r = rng if rng is not None else random
    words = [
        "kevin", "star", "sweet", "happy", "lucky", "apple", "blue",
        "coffee", "taiwan", "cat", "dog", "angel", "sunny", "music",
        "jacky", "mei", "ting", "hao", "chen", "lin", "huang",
    ]
    w = r.choice(words)
    sep = r.choice(["_", ".", ""])
    suffix = str(r.randint(10, 9999))
    return f"{w}{sep}{suffix}"


def validate_ptt_id(ptt_id: str) -> bool:
    """
    Validates a Taiwan PTT BBS user ID (starts with a letter, 3-15 chars, alphanumeric/underscore).
    """
    if not isinstance(ptt_id, str):
        return False
    return bool(re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{2,14}", ptt_id.strip()))


def generate_ptt_id(rng: Optional[random.Random] = None) -> str:
    """
    Generates an authentic Taiwan PTT BBS user ID.
    """
    r = rng if rng is not None else random
    prefixes = [
        "gossiping", "mayday", "skywalk", "jaychou", "blacktea",
        "baseball", "catlover", "stockking", "techman", "otaku",
        "pttuser", "taiwanese", "foodie", "movie", "gamer",
    ]
    p = r.choice(prefixes)
    suf = r.choice(["5566", "99", "666", "888", "123", "01", "777", "999"])
    return f"{p}{suf}"


# ── Medical License & Military ID (醫事證照與軍人證號) ─────────────────────────


def validate_medical_license(lic: str) -> bool:
    """
    Validates a Taiwan Medical License registration number (e.g. 醫字第012345號).
    """
    if not isinstance(lic, str):
        return False
    return bool(re.fullmatch(r"(?:醫|護理|藥|醫檢|物理治療|齒)字第\d{6}號", lic.strip()))


def generate_medical_license(rng: Optional[random.Random] = None) -> str:
    """
    Generates a Taiwan medical/nursing license registration number.
    """
    r = rng if rng is not None else random
    prefix = r.choice(MEDICAL_PREFIXES)
    num = f"{r.randint(1000, 999999):06d}"
    return f"{prefix}{num}號"


def validate_military_id(mil_id: str) -> bool:
    """
    Validates a Taiwan Armed Forces Military ID number (e.g. 陸字第123456號).
    """
    if not isinstance(mil_id, str):
        return False
    return bool(re.fullmatch(r"(?:陸|海|空|憲|聯)字第\d{6}號", mil_id.strip()))


def generate_military_id(rng: Optional[random.Random] = None) -> str:
    """
    Generates a Taiwan Armed Forces military ID number.
    """
    r = rng if rng is not None else random
    prefix = r.choice(MILITARY_PREFIXES)
    num = f"{r.randint(1000, 999999):06d}"
    return f"{prefix}{num}號"


# ── Email Address ─────────────────────────────────────────────────────────────


def validate_email(email_str: str) -> bool:
    """
    Validates an email address.
    """
    if not isinstance(email_str, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.fullmatch(pattern, email_str.strip()))


def generate_email(
    name_hint: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic email address with Taiwanese or global domain names.
    """
    r = rng if rng is not None else random
    domain = r.choice(TAIWAN_EMAIL_DOMAINS)

    if name_hint and re.match(r"^[a-zA-Z0-9._]+$", name_hint):
        user = name_hint.lower()
    else:
        first_names = ["kevin", "david", "michael", "jessica", "emily", "alex", "eric", "ting", "mei", "lin"]
        surnames = ["chen", "lin", "huang", "chang", "wang", "wu", "liu", "tsai", "yang"]
        f = r.choice(first_names)
        s = r.choice(surnames)
        num = r.randint(1, 999) if r.random() < 0.4 else ""
        sep = r.choice([".", "_", ""])
        user = f"{f}{sep}{s}{num}"

    return f"{user}@{domain}"


# ── Secrets, Passwords, and Tokens ────────────────────────────────────────────


def generate_secret(
    secret_type: str = "any",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates authentication secrets (OTP verification code, password, or API key).
    
    Args:
        secret_type: 'otp' (6 digits), 'password', 'api_key', or 'any'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if secret_type == "any":
        secret_type = r.choice(["otp", "password", "api_key"])

    if secret_type == "otp":
        return f"{r.randint(100000, 999999)}"
    elif secret_type == "api_key":
        hex_token = "".join(r.choice("0123456789abcdef") for _ in range(32))
        return f"sk-tw-{hex_token}"
    else:  # password
        chars = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*"
        length = r.randint(10, 16)
        return "".join(r.choice(chars) for _ in range(length))
