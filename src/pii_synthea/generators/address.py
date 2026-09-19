"""
Taiwan Address & Postal Code Generator and Validator.
Covers:
- All 22 administrative divisions (直轄市、縣、市)
- 368 districts (鄉鎮市區) mapped to official 3-digit postal codes
- Authentic Taiwanese roads, streets, boulevards, sections, lanes, alleys, numbers, floors
- 3-digit, 3+2 digit, and 3+3 digit postal code formats
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Optional

# Complete mapping of Taiwan 22 Counties/Cities -> Districts -> 3-digit Postal Codes
TAIWAN_ADMIN_DIVISIONS: dict[str, dict[str, str]] = {
    "台北市": {
        "中正區": "100", "大同區": "103", "中山區": "104", "松山區": "105",
        "大安區": "106", "萬華區": "108", "信義區": "110", "士林區": "111",
        "北投區": "112", "內湖區": "114", "南港區": "115", "文山區": "116",
    },
    "基隆市": {
        "仁愛區": "200", "信義區": "201", "中正區": "202", "中山區": "203",
        "安樂區": "204", "暖暖區": "205", "七堵區": "206",
    },
    "新北市": {
        "萬里區": "207", "金山區": "208", "板橋區": "220", "汐止區": "221",
        "深坑區": "222", "石碇區": "223", "瑞芳區": "224", "平溪區": "226",
        "雙溪區": "227", "貢寮區": "228", "新店區": "231", "坪林區": "232",
        "烏來區": "233", "永和區": "234", "中和區": "235", "土城區": "236",
        "三峽區": "237", "樹林區": "238", "鶯歌區": "239", "三重區": "241",
        "新莊區": "242", "泰山區": "243", "林口區": "244", "蘆洲區": "247",
        "五股區": "248", "八里區": "249", "淡水區": "251", "三芝區": "252",
        "石門區": "253",
    },
    "宜蘭縣": {
        "宜蘭市": "260", "頭城鎮": "261", "礁溪鄉": "262", "壯圍鄉": "263",
        "員山鄉": "264", "羅東鎮": "265", "三星鄉": "266", "大同鄉": "267",
        "五結鄉": "268", "冬山鄉": "269", "蘇澳鎮": "270", "南澳鄉": "272",
    },
    "新竹市": {
        "東區": "300", "北區": "300", "香山區": "300",
    },
    "新竹縣": {
        "竹北市": "302", "湖口鄉": "303", "新豐鄉": "304", "新埔鎮": "305",
        "關西鎮": "306", "芎林鄉": "307", "寶山鄉": "308", "竹東鎮": "310",
        "五峰鄉": "311", "橫山鄉": "312", "尖石鄉": "313", "北埔鄉": "314",
        "峨眉鄉": "315",
    },
    "桃園市": {
        "中壢區": "320", "平鎮區": "324", "龍潭區": "325", "楊梅區": "326",
        "新屋區": "327", "觀音區": "328", "桃園區": "330", "龜山區": "333",
        "八德區": "334", "大溪區": "335", "復興區": "336", "大園區": "337",
        "蘆竹區": "338",
    },
    "苗栗縣": {
        "竹南鎮": "350", "頭份市": "351", "三灣鄉": "352", "南庄鄉": "353",
        "獅潭鄉": "354", "後龍鎮": "356", "通霄鎮": "357", "苑裡鎮": "358",
        "苗栗市": "360", "造橋鄉": "361", "頭屋鄉": "362", "公館鄉": "363",
        "大湖鄉": "364", "泰安鄉": "365", "銅鑼鄉": "366", "三義鄉": "367",
        "西湖鄉": "368", "卓蘭鎮": "369",
    },
    "台中市": {
        "中區": "400", "東區": "401", "南區": "402", "西區": "403",
        "北區": "404", "北屯區": "406", "西屯區": "407", "南屯區": "408",
        "太平區": "411", "大里區": "412", "霧峰區": "413", "烏日區": "414",
        "豐原區": "420", "后里區": "421", "石岡區": "422", "東勢區": "423",
        "和平區": "424", "新社區": "426", "潭子區": "427", "大雅區": "428",
        "神岡區": "429", "大肚區": "432", "沙鹿區": "433", "龍井區": "434",
        "梧棲區": "435", "清水區": "436", "大甲區": "437", "外埔區": "438",
        "大安區": "439",
    },
    "彰化縣": {
        "彰化市": "500", "芬園鄉": "502", "花壇鄉": "503", "秀水鄉": "504",
        "鹿港鎮": "505", "福興鄉": "506", "線西鄉": "507", "和美鎮": "508",
        "伸港鄉": "509", "員林市": "510", "社頭鄉": "511", "永靖鄉": "512",
        "埔心鄉": "513", "溪湖鎮": "514", "大村鄉": "515", "埔鹽鄉": "516",
        "田中鎮": "520", "北斗鎮": "521", "田尾鄉": "522", "埤頭鄉": "523",
        "溪州鄉": "524", "竹塘鄉": "525", "二林鎮": "526", "大城鄉": "527",
        "芳苑鄉": "528", "二水鄉": "530",
    },
    "南投縣": {
        "南投市": "540", "中寮鄉": "541", "草屯鎮": "542", "國姓鄉": "544",
        "埔里鎮": "545", "仁愛鄉": "546", "名間鄉": "551", "集集鎮": "552",
        "水里鄉": "553", "魚池鄉": "555", "信義鄉": "556", "竹山鎮": "557",
        "鹿谷鄉": "558",
    },
    "嘉義市": {
        "東區": "600", "西區": "600",
    },
    "嘉義縣": {
        "番路鄉": "602", "梅山鄉": "603", "竹崎鄉": "604", "阿里山鄉": "605",
        "中埔鄉": "606", "大埔鄉": "607", "水上鄉": "608", "鹿草鄉": "611",
        "太保市": "612", "朴子市": "613", "東石鄉": "614", "六腳鄉": "615",
        "新港鄉": "616", "民雄鄉": "621", "大林鎮": "622", "溪口鄉": "623",
        "義竹鄉": "624", "布袋鎮": "625",
    },
    "雲林縣": {
        "斗南鎮": "630", "大埤鄉": "631", "虎尾鎮": "632", "土庫鎮": "633",
        "褒忠鄉": "634", "東勢鄉": "635", "台西鄉": "636", "崙背鄉": "637",
        "麥寮鄉": "638", "斗六市": "640", "林內鄉": "643", "古坑鄉": "646",
        "莿桐鄉": "647", "西螺鎮": "648", "二崙鄉": "649", "北港鎮": "651",
        "水林鄉": "652", "口湖鄉": "653", "四湖鄉": "654", "元長鄉": "655",
    },
    "台南市": {
        "中西區": "700", "東區": "701", "南區": "702", "北區": "704",
        "安平區": "708", "安南區": "709", "永康區": "710", "歸仁區": "711",
        "新化區": "712", "左鎮區": "713", "玉井區": "714", "楠西區": "715",
        "南化區": "716", "仁德區": "717", "關廟區": "718", "龍崎區": "719",
        "官田區": "720", "麻豆區": "721", "佳里區": "722", "西港區": "723",
        "七股區": "724", "將軍區": "725", "學甲區": "726", "北門區": "727",
        "新營區": "730", "後壁區": "731", "白河區": "732", "東山區": "733",
        "六甲區": "734", "下營區": "735", "柳營區": "736", "鹽水區": "737",
        "善化區": "741", "大內區": "742", "山上區": "743", "新市區": "744",
        "安定區": "745",
    },
    "高雄市": {
        "新興區": "800", "前金區": "801", "苓雅區": "802", "鹽埕區": "803",
        "鼓山區": "804", "旗津區": "805", "前鎮區": "806", "三民區": "807",
        "楠梓區": "811", "小港區": "812", "左營區": "813", "仁武區": "814",
        "大社區": "815", "岡山區": "820", "路竹區": "821", "阿蓮區": "822",
        "田寮區": "823", "燕巢區": "824", "橋頭區": "825", "梓官區": "826",
        "彌陀區": "827", "永安區": "828", "湖內區": "829", "鳳山區": "830",
        "大寮區": "831", "林園區": "832", "鳥松區": "833", "大樹區": "840",
        "旗山區": "842", "美濃區": "843", "六龜區": "844", "內門區": "845",
        "杉林區": "846", "甲仙區": "847", "桃源區": "848", "那瑪夏區": "849",
        "茂林區": "851", "茄萣區": "852",
    },
    "澎湖縣": {
        "馬公市": "880", "西嶼鄉": "881", "望安鄉": "882", "七美鄉": "883",
        "白沙鄉": "884", "湖西鄉": "885",
    },
    "金門縣": {
        "金沙鎮": "890", "金湖鎮": "891", "金寧鄉": "892", "金城鎮": "893",
        "烈嶼鄉": "894", "烏坵鄉": "896",
    },
    "連江縣": {
        "南竿鄉": "209", "北竿鄉": "210", "莒光鄉": "211", "東引鄉": "212",
    },
    "屏東縣": {
        "屏東市": "900", "三地門鄉": "901", "霧台鄉": "902", "瑪家鄉": "903",
        "九如鄉": "904", "里港鄉": "905", "高樹鄉": "906", "鹽埔鄉": "907",
        "長治鄉": "908", "麟洛鄉": "909", "竹田鄉": "911", "內埔鄉": "912",
        "萬丹鄉": "913", "潮州鎮": "920", "泰武鄉": "921", "來義鄉": "922",
        "萬巒鄉": "923", "崁頂鄉": "924", "新埤鄉": "925", "南州鄉": "926",
        "林邊鄉": "927", "東港鎮": "928", "琉球鄉": "929", "佳冬鄉": "931",
        "新園鄉": "932", "枋寮鄉": "940", "枋山鄉": "941", "春日鄉": "942",
        "獅子鄉": "943", "車城鄉": "944", "牡丹鄉": "945", "恆春鎮": "946",
        "滿州鄉": "947",
    },
    "台東縣": {
        "台東市": "950", "綠島鄉": "951", "蘭嶼鄉": "952", "延平鄉": "953",
        "卑南鄉": "954", "鹿野鄉": "955", "關山鎮": "956", "海端鄉": "957",
        "池上鄉": "958", "東河鄉": "959", "成功鎮": "961", "長濱鄉": "962",
        "太麻里鄉": "963", "金峰鄉": "964", "大武鄉": "965", "達仁鄉": "966",
    },
    "花蓮縣": {
        "花蓮市": "970", "新城鄉": "971", "秀林鄉": "972", "吉安鄉": "973",
        "壽豐鄉": "974", "鳳林鎮": "975", "光復鄉": "976", "豐濱鄉": "977",
        "瑞穗鄉": "978", "萬榮鄉": "979", "玉里鎮": "981", "卓溪鄉": "982",
        "富里鄉": "983",
    },
}

# Real Taiwanese Roads by Region
METROPOLITAN_ROADS: dict[str, list[str]] = {
    "台北市": [
        "忠孝東路", "忠孝西路", "仁愛路", "信義路", "和平東路", "和平西路",
        "南京東路", "南京西路", "民生東路", "民生西路", "敦化南路", "敦化北路",
        "復興南路", "復興北路", "光復南路", "光復北路", "建國南路", "建國北路",
        "新生南路", "新生北路", "八德路", "重慶南路", "重慶北路", "羅斯福路",
        "基隆路", "承德路", "延平北路", "中山北路", "中山南路",
    ],
    "新北市": [
        "文化路", "民生路", "中正路", "中山路", "新北大道", "重陽路",
        "三民路", "自強路", "中央路", "環河西路", "景平路", "中正南路",
        "幸福路", "思源路", "中正路", "介壽路",
    ],
    "台中市": [
        "台灣大道", "文心路", "公益路", "逢甲路", "中清路", "崇德路",
        "美村路", "西屯路", "向上路", "五權西路", "復興路", "進化路",
    ],
    "高雄市": [
        "一心路", "二聖路", "三多路", "四維路", "五福路", "六合路",
        "七賢路", "八德路", "九如路", "十全路", "博愛路", "中山路",
        "民族路", "中華路", "建國路", "青年路",
    ],
}

COMMON_TAIWAN_ROADS: list[str] = [
    "中正路", "中山路", "中華路", "民生路", "民族路", "民權路",
    "光華路", "文化路", "成功路", "自由路", "自強路", "和平路",
    "復興路", "新興路", "勝利路", "大同路", "延平路", "光明路",
    "公園路", "南門路", "北門路", "博愛街", "中央路", "市場街",
]

SECTIONS: list[str] = ["一段", "二段", "三段", "四段", "五段", "六段"]


@dataclass
class GeneratedAddress:
    full_address: str
    postal_code: str
    city: str
    district: str
    road: str
    detail: str


def generate_postal_code(
    city: Optional[str] = None,
    district: Optional[str] = None,
    format_type: str = "3+3",
    rng: Optional[random.Random] = None,
) -> str:
    """
    Generates a realistic Taiwan postal code.
    
    Args:
        city: Optional city name (e.g. '台北市')
        district: Optional district name (e.g. '大安區')
        format_type: '3' (e.g. 106), '3+2' (e.g. 10667 or 106-67), or '3+3' (e.g. 106456 or 106-456).
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    if city and city in TAIWAN_ADMIN_DIVISIONS:
        city_districts = TAIWAN_ADMIN_DIVISIONS[city]
        if district and district in city_districts:
            base_code = city_districts[district]
        else:
            base_code = r.choice(list(city_districts.values()))
    else:
        all_codes = [
            code
            for c_dict in TAIWAN_ADMIN_DIVISIONS.values()
            for code in c_dict.values()
        ]
        base_code = r.choice(all_codes)

    if format_type == "3":
        return base_code
    elif format_type == "3+2":
        sub = f"{r.randint(10, 99)}"
        sep = r.choice(["", "-", " "])
        return f"{base_code}{sep}{sub}"
    elif format_type == "3+3":
        sub = f"{r.randint(100, 999)}"
        sep = r.choice(["", "-", " "])
        return f"{base_code}{sep}{sub}"
    else:
        return base_code


def validate_postal_code(code: str) -> bool:
    """
    Validates a Taiwan postal code.
    Supports 3-digit, 3+2 digit, or 3+3 digit formats with optional hyphen/space.
    """
    if not isinstance(code, str):
        return False
    c = code.strip()
    return bool(re.fullmatch(r"\d{3}(?:[-\s]?\d{2,3})?", c))


def generate_address(
    city: Optional[str] = None,
    district: Optional[str] = None,
    include_postal_code: bool = False,
    detail_level: str = "full",
    rng: Optional[random.Random] = None,
) -> GeneratedAddress:
    """
    Generates an authentic Taiwan residential or business address.
    
    Args:
        city: Optional county/city.
        district: Optional district.
        include_postal_code: Whether to prepend the postal code.
        detail_level: 'full' (with lane/number/floor), 'simple' (up to number), or 'building'.
        rng: Optional random.Random instance.
    """
    r = rng if rng is not None else random

    # 1. Select City & District
    if not city or city not in TAIWAN_ADMIN_DIVISIONS:
        city = r.choice(list(TAIWAN_ADMIN_DIVISIONS.keys()))
    districts = TAIWAN_ADMIN_DIVISIONS[city]

    if not district or district not in districts:
        district = r.choice(list(districts.keys()))
    postal_code = districts[district]

    # 2. Select Road
    if city in METROPOLITAN_ROADS and r.random() < 0.7:
        road = r.choice(METROPOLITAN_ROADS[city])
    else:
        road = r.choice(COMMON_TAIWAN_ROADS)

    # 3. Add Section if appropriate
    if any(k in road for k in ["東路", "西路", "南路", "北路", "大道"]) or r.random() < 0.35:
        road = f"{road}{r.choice(SECTIONS)}"

    # 4. Synthesize detail components
    house_num = r.randint(1, 450)
    if r.random() < 0.15:
        house_num_str = f"{house_num}之{r.randint(1, 8)}號"
    else:
        house_num_str = f"{house_num}號"

    detail_parts = []

    # Lane & Alley
    has_lane = r.random() < 0.55
    if has_lane:
        lane_num = r.randint(1, 350)
        detail_parts.append(f"{lane_num}巷")
        if r.random() < 0.4:
            alley_num = r.randint(1, 50)
            detail_parts.append(f"{alley_num}弄")

    detail_parts.append(house_num_str)

    # Floor & Unit
    if detail_level == "full":
        if r.random() < 0.65:
            fl = r.randint(2, 25)
            if r.random() < 0.25:
                floor_str = f"{fl}樓之{r.randint(1, 5)}"
            elif r.random() < 0.1:
                floor_str = f"{fl}樓-{r.randint(1, 4)}"
            else:
                floor_str = f"{fl}樓"
            detail_parts.append(floor_str)

        if r.random() < 0.15:
            room = r.choice(["A室", "B室", "101室", "203室"])
            detail_parts.append(room)

    detail_str = "".join(detail_parts)
    addr_body = f"{city}{district}{road}{detail_str}"

    if include_postal_code:
        pcode = generate_postal_code(city=city, district=district, format_type=r.choice(["3", "3+3"]), rng=r)
        full_addr = f"{pcode} {addr_body}"
    else:
        full_addr = addr_body

    return GeneratedAddress(
        full_address=full_addr,
        postal_code=postal_code,
        city=city,
        district=district,
        road=road,
        detail=detail_str,
    )
