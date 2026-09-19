"""
Taiwan Person Name Generator.
Covers:
- Standard Traditional Chinese names with weighted Top Taiwan Surnames (百家姓)
- Compound surnames (複姓, e.g. 歐陽, 司徒)
- Authentic Taiwanese male, female, and single-character given names
- Taiwan Indigenous names (原住民族傳統名字，漢字音譯與羅馬拼音)
- Common Western/Romanized names used by Taiwanese individuals (e.g. Kevin Chen)
"""

from __future__ import annotations

import random
from typing import Optional

# Top Taiwan Surnames (Over 85% of population coverage)
TAIWAN_TOP_SURNAMES: list[str] = [
    "陳", "林", "黃", "張", "李", "王", "吳", "劉", "蔡", "楊",
    "許", "鄭", "謝", "洪", "郭", "邱", "曾", "廖", "賴", "徐",
    "周", "葉", "蘇", "莊", "呂", "江", "何", "蕭", "羅", "高",
    "潘", "簡", "朱", "鍾", "彭", "游", "詹", "胡", "施", "沈",
    "柯", "盧", "梁", "顏", "翁", "魏", "孫", "范", "方", "鄧",
    "杜", "傅", "侯", "薛", "丁", "溫", "阮", "紀", "蔣", "歐",
    "藍", "董", "戴", "尤", "程", "康", "湯", "田", "鄒", "涂",
]

# Compound Surnames (複姓)
COMPOUND_SURNAMES: list[str] = [
    "歐陽", "司徒", "上官", "諸葛", "司馬", "皇甫",
    "尉遲", "公孫", "令狐", "范姜", "申屠", "夏侯",
]

# Male Given Names (Taiwan common and demographic clusters)
MALE_GIVEN_NAMES: list[str] = [
    "志豪", "家豪", "冠宇", "俊傑", "冠廷", "承翰", "柏翰", "宗翰",
    "宇軒", "柏宇", "哲瑋", "俊宏", "志偉", "彥廷", "威廷", "廷宇",
    "建宏", "宇翔", "翔宇", "奕廷", "宏偉", "冠霖", "志明", "建良",
    "宗祐", "柏均", "志遠", "承軒", "宇恩", "俊成", "家榮", "義雄",
    "正雄", "添財", "文雄", "金龍", "宏儒", "育誠", "俊毅", "浩然",
    "天賜", "建華", "明德", "信宏", "俊達", "建銘", "世豪", "子敬",
]

# Female Given Names (Taiwan common and demographic clusters)
FEMALE_GIVEN_NAMES: list[str] = [
    "佳玲", "雅婷", "怡萱", "婷婷", "淑芬", "雅惠", "欣儀", "詩涵",
    "佩君", "雅雯", "淑婷", "怡婷", "冠妤", "宜蓁", "詠晴", "怡君",
    "美玲", "秀英", "麗華", "雅芳", "玉蘭", "淑珍", "秀琴", "秀娟",
    "婉婷", "雅萍", "靜怡", "佳穎", "佩蓉", "筱涵", "依婷", "詠涵",
    "語彤", "欣妤", "慧玲", "巧柔", "玟靜", "詩婷", "芷瑄", "思妤",
    "秋月", "雅晴", "佩珊", "雅筑", "佩璇", "芸萱", "若涵", "紫涵",
]

# Single-character Given Names
SINGLE_CHAR_GIVEN_NAMES: list[str] = [
    "明", "華", "翔", "豪", "傑", "廷", "宇", "偉", "銘", "宏",
    "玲", "婷", "萱", "惠", "雯", "芳", "珍", "欣", "涵", "晴",
]

# Taiwan Indigenous Names (Traditional Names & Romanized forms)
INDIGENOUS_NAMES_ZH: list[str] = [
    "尤瑪·達魯", "瓦歷斯·諾幹", "莫那·魯道", "舒米恩·魯碧", "撒可努",
    "瑪勒勒佛勒", "巴奈·庫穗", "里慕伊·阿紀", "伐利斯·貝林", "嘎造·吉盧",
    "達利·夫第", "督麥·阿韻", "伍瑪斯·布農", "達努巴克·理阿", "高金素梅",
    "舞鶴·達魯", "阿布斯", "拉娃·谷幸", "阿基師", "依拜·維吉",
]

INDIGENOUS_NAMES_ROMANIZED: list[str] = [
    "Yuma Taru", "Walis Nokan", "Mona Rudo", "Suming Rupi", "Sakinu",
    "Panai Kusui", "Rimuy Aki", "Kacao Cilu", "Ciwas Ali", "Ipay Buyi",
    "Mayaw Biho", "Umas Bunun", "Danubak Leah",
]

# Western First Names paired with Taiwan Surnames
WESTERN_FIRST_NAMES: list[str] = [
    "David", "Kevin", "Michael", "Eric", "Alex", "Jason", "Brian", "Chris",
    "Jessica", "Emily", "Sarah", "Amy", "Grace", "Joyce", "Kelly", "Jenny",
]


def generate_person_name(
    gender: Optional[str] = None,
    style: str = "any",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic personal name in the Taiwan cultural context.
    
    Args:
        gender: 'male', 'female', or None (random).
        style: 'zh' (standard 3 or 2 char), 'compound' (複姓), 'indigenous' (原住民),
               'romanized' (English name), or 'any' (weighted realistic distribution).
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if style == "any":
        # 85% standard Chinese, 5% compound, 5% indigenous, 5% romanized
        choice_val = r.random()
        if choice_val < 0.85:
            style = "zh"
        elif choice_val < 0.90:
            style = "compound"
        elif choice_val < 0.95:
            style = "indigenous"
        else:
            style = "romanized"

    if style == "indigenous":
        if r.random() < 0.8:
            return r.choice(INDIGENOUS_NAMES_ZH)
        return r.choice(INDIGENOUS_NAMES_ROMANIZED)

    if style == "romanized":
        first = r.choice(WESTERN_FIRST_NAMES)
        surname = r.choice(TAIWAN_TOP_SURNAMES)
        # Romanize the surname or keep English
        surname_romanized_map = {
            "陳": "Chen", "林": "Lin", "黃": "Huang", "張": "Chang", "李": "Lee",
            "王": "Wang", "吳": "Wu", "劉": "Liu", "蔡": "Tsai", "楊": "Yang",
            "許": "Hsu", "鄭": "Cheng", "謝": "Hsieh", "洪": "Hung", "郭": "Kuo",
        }
        rom_sur = surname_romanized_map.get(surname, "Chen")
        return f"{first} {rom_sur}"

    # Determine gender
    if gender not in ("male", "female"):
        gender = r.choice(["male", "female"])

    # Determine surname
    if style == "compound":
        surname = r.choice(COMPOUND_SURNAMES)
    else:
        surname = r.choice(TAIWAN_TOP_SURNAMES)

    # Determine given name
    use_single_char = r.random() < 0.08  # 8% of Taiwanese have single char given name
    if use_single_char:
        given = r.choice(SINGLE_CHAR_GIVEN_NAMES)
    elif gender == "male":
        given = r.choice(MALE_GIVEN_NAMES)
    else:
        given = r.choice(FEMALE_GIVEN_NAMES)

    return f"{surname}{given}"
