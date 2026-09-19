"""
Taiwan National Identification & Resident Certificate Generators and Validators.
Covers:
- Republic of China (Taiwan) Citizen National ID ([A-Z][12]\\d{8})
- New Alien Resident Certificate (ARC / 外來人口統一證號 [A-Z][89]\\d{8})
- Old Alien Resident Certificate (ARC [A-Z][A-D]\\d{8})
- Household Registration Number (戶號 [A-Z]\\d{7})
"""

from __future__ import annotations

import random
import re
from typing import Optional

# County / City Letter Codes for Taiwan National ID
COUNTY_LETTER_CODES: dict[str, int] = {
    "A": 10,  # 台北市 (Taipei City)
    "B": 11,  # 台中市 (Taichung City)
    "C": 12,  # 基隆市 (Keelung City)
    "D": 13,  # 台南市 (Tainan City)
    "E": 14,  # 高雄市 (Kaohsiung City)
    "F": 15,  # 新北市 (New Taipei City)
    "G": 16,  # 宜蘭縣 (Yilan County)
    "H": 17,  # 桃園市 (Taoyuan City)
    "I": 34,  # 嘉義市 (Chiayi City)
    "J": 18,  # 新竹縣 (Hsinchu County)
    "K": 19,  # 苗栗縣 (Miaoli County)
    "L": 20,  # 台中縣 (Former Taichung County)
    "M": 21,  # 南投縣 (Nantou County)
    "N": 22,  # 彰化縣 (Changhua County)
    "O": 35,  # 新竹市 (Hsinchu City)
    "P": 23,  # 雲林縣 (Yunlin County)
    "Q": 24,  # 嘉義縣 (Chiayi County)
    "R": 25,  # 台南縣 (Former Tainan County)
    "S": 26,  # 高雄縣 (Former Kaohsiung County)
    "T": 27,  # 屏東縣 (Pingtung County)
    "U": 28,  # 花蓮縣 (Hualien County)
    "V": 29,  # 台東縣 (Taitung County)
    "W": 32,  # 金門縣 (Kinmen County)
    "X": 30,  # 澎湖縣 (Penghu County)
    "Y": 31,  # 陽明山管理局 (Former Yangmingshan)
    "Z": 33,  # 連江縣 (Lienchiang County / Matsu)
}

_DIGIT_WEIGHTS: list[int] = [8, 7, 6, 5, 4, 3, 2, 1]


def calculate_id_check_digit(letter: str, digits_8: list[int]) -> int:
    """
    Calculates the 10th check digit for a 9-char prefix (letter + 8 digits).
    Weights: Letter code d0*1 + d1*9, followed by digits with weights 8 down to 1.
    """
    code = COUNTY_LETTER_CODES[letter.upper()]
    n1 = code // 10
    n2 = code % 10
    total = n1 * 1 + n2 * 9

    for d, w in zip(digits_8, _DIGIT_WEIGHTS):
        total += d * w

    check_digit = (10 - (total % 10)) % 10
    return check_digit


def validate_national_id(id_str: str) -> bool:
    """
    Validates a Taiwan National ID or Alien Resident Certificate (ARC) number.
    Supports:
    - Citizen ID: [A-Z][12]\\d{8}
    - New ARC: [A-Z][89]\\d{8}
    - Old ARC: [A-Z][A-D]\\d{8}
    """
    if not isinstance(id_str, str):
        return False

    id_clean = id_str.strip().upper()
    if len(id_clean) != 10:
        return False

    letter = id_clean[0]
    if letter not in COUNTY_LETTER_CODES:
        return False

    second_char = id_clean[1]

    # Case 1: Standard Citizen ID ([12]) or New ARC ([89])
    if second_char in ("1", "2", "8", "9"):
        if not id_clean[1:].isdigit():
            return False
        digits = [int(ch) for ch in id_clean[1:9]]
        expected_check = calculate_id_check_digit(letter, digits)
        return int(id_clean[9]) == expected_check

    # Case 2: Old ARC ([A-D])
    if second_char in ("A", "B", "C", "D"):
        rest = id_clean[2:]
        if not rest.isdigit() or len(rest) != 8:
            return False

        code1 = COUNTY_LETTER_CODES[letter]
        n1 = code1 // 10
        n2 = code1 % 10

        # Letter 2 numeric value: A=10, B=11, C=12, D=13. Mod 10 => 0, 1, 2, 3.
        code2_mod10 = COUNTY_LETTER_CODES[second_char] % 10

        total = n1 * 1 + n2 * 9 + code2_mod10 * 8
        digits = [int(ch) for ch in rest[:7]]
        weights_old = [7, 6, 5, 4, 3, 2, 1]

        for d, w in zip(digits, weights_old):
            total += d * w

        expected_check = (10 - (total % 10)) % 10
        return int(rest[7]) == expected_check

    return False


def generate_national_id(
    gender: Optional[int] = None,
    city_code: Optional[str] = None,
    id_type: str = "citizen",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates an algorithmically valid Taiwan National ID or ARC.
    
    Args:
        gender: 1 for male citizen, 2 for female citizen; 8 for male ARC, 9 for female ARC.
        city_code: A letter 'A'..'Z' to specify the issuing county/city.
        id_type: 'citizen' (default), 'new_arc', or 'old_arc'.
        rng: Optional random.Random instance for seeded reproducibility.
    """
    r = rng if rng is not None else random

    if city_code and city_code.upper() in COUNTY_LETTER_CODES:
        letter = city_code.upper()
    else:
        # Default distribution: common metropolitan areas have higher weight
        letter = r.choice(list(COUNTY_LETTER_CODES.keys()))

    if id_type == "citizen":
        if gender not in (1, 2):
            gender = r.choice([1, 2])
        d1 = gender
        d2_8 = [r.randint(0, 9) for _ in range(7)]
        digits_8 = [d1] + d2_8
        check_digit = calculate_id_check_digit(letter, digits_8)
        return f"{letter}{''.join(str(d) for d in digits_8)}{check_digit}"

    elif id_type == "new_arc":
        if gender not in (8, 9):
            gender = r.choice([8, 9])
        d1 = gender
        d2_8 = [r.randint(0, 9) for _ in range(7)]
        digits_8 = [d1] + d2_8
        check_digit = calculate_id_check_digit(letter, digits_8)
        return f"{letter}{''.join(str(d) for d in digits_8)}{check_digit}"

    elif id_type == "old_arc":
        second_letter = r.choice(["A", "B", "C", "D"])
        code1 = COUNTY_LETTER_CODES[letter]
        n1 = code1 // 10
        n2 = code1 % 10
        code2_mod10 = COUNTY_LETTER_CODES[second_letter] % 10

        total = n1 * 1 + n2 * 9 + code2_mod10 * 8
        d1_7 = [r.randint(0, 9) for _ in range(7)]
        weights_old = [7, 6, 5, 4, 3, 2, 1]
        for d, w in zip(d1_7, weights_old):
            total += d * w

        check_digit = (10 - (total % 10)) % 10
        return f"{letter}{second_letter}{''.join(str(d) for d in d1_7)}{check_digit}"

    else:
        raise ValueError(f"Unknown id_type: {id_type}. Must be 'citizen', 'new_arc', or 'old_arc'.")


def validate_household_no(household_no: str) -> bool:
    """
    Validates a Taiwan Household Registration Number (戶口名簿戶號).
    Format: 1 uppercase letter + 7 digits (e.g. A1234567).
    """
    if not isinstance(household_no, str):
        return False
    return bool(re.fullmatch(r"[A-Z]\d{7}", household_no.strip().upper()))


def generate_household_no(
    city_code: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan Household Registration Number (戶口名簿戶號).
    """
    r = rng if rng is not None else random
    if city_code and city_code.upper() in COUNTY_LETTER_CODES:
        letter = city_code.upper()
    else:
        letter = r.choice(list(COUNTY_LETTER_CODES.keys()))

    digits = "".join(str(r.randint(0, 9)) for _ in range(7))
    return f"{letter}{digits}"
