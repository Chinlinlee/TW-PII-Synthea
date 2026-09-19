"""
Taiwan Hard Negatives Entity Catalog & Taxonomy (Ticket 05).
Curates realistic Taiwanese entities that are lexically or structurally similar to PII
(such as brand names containing person names, public political/historical figures,
public landmarks, emergency hotlines, public government emails, and invoice/code numbers)
that must NOT be labeled as private individual PII.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence


class HardNegativeCategory(str, Enum):
    """Categories of hard negative entities in Taiwan localized contexts."""
    BRAND_PERSON_NAME = "brand_person_name"
    PUBLIC_HISTORICAL_FIGURE = "public_historical_figure"
    PUBLIC_LANDMARK_ADDRESS = "public_landmark_address"
    PUBLIC_HOTLINE = "public_hotline"
    PUBLIC_EMAIL = "public_email"
    OFFICIAL_CODE_NUMBER = "official_code_number"


@dataclass(frozen=True)
class HardNegativeItem:
    """Individual entity entry in the hard negative catalog."""
    text: str
    category: HardNegativeCategory
    confusable_with: str  # e.g., 'person', 'address', 'phone_number', 'email', 'tax_id'
    description: str
    context_hint: str = ""


class HardNegativeCatalog:
    """Repository and query interface for curated Taiwan hard negatives."""

    # 1. 商家與品牌含人名 (Confusable with: person)
    _BRAND_PERSON_NAMES: List[HardNegativeItem] = [
        HardNegativeItem(
            text="梁社漢排骨",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="連鎖便當品牌，包含完整人名結構",
            context_hint="便當餐飲",
        ),
        HardNegativeItem(
            text="鬍鬚張魯肉飯",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台灣傳統知名魯肉飯連鎖品牌",
            context_hint="台菜餐飲",
        ),
        HardNegativeItem(
            text="阿宗麵線",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="西門町知名傳統小吃老店",
            context_hint="街頭小吃",
        ),
        HardNegativeItem(
            text="林東芳牛肉麵",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台北知名老字號牛肉麵店",
            context_hint="牛肉麵店",
        ),
        HardNegativeItem(
            text="劉山東牛肉麵",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台北車站開封街米其林必比登推薦牛肉麵",
            context_hint="牛肉麵店",
        ),
        HardNegativeItem(
            text="林銀杏",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台灣百貨知名杏仁粉養生食品品牌",
            context_hint="生技養生",
        ),
        HardNegativeItem(
            text="吳寶春麥方店",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="世界麵包冠軍師傅創立之烘焙品牌",
            context_hint="烘焙甜點",
        ),
        HardNegativeItem(
            text="郭元益",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台灣百年喜餅與傳統糕餅品牌",
            context_hint="糕餅名店",
        ),
        HardNegativeItem(
            text="鼎泰豐",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="國際知名小籠包連鎖餐廳",
            context_hint="點心餐飲",
        ),
        HardNegativeItem(
            text="王品牛排",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="知名連鎖餐飲集團牛排品牌",
            context_hint="西式餐飲",
        ),
        HardNegativeItem(
            text="洪瑞珍三明治",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="彰化北斗起源之老牌三明治連鎖名店",
            context_hint="點心輕食",
        ),
        HardNegativeItem(
            text="金峰魯肉飯",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台北南門市場傳統小吃名店",
            context_hint="街頭小吃",
        ),
        HardNegativeItem(
            text="施家麻油腰花",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="信義區松山路台菜食補名店",
            context_hint="台菜餐飲",
        ),
        HardNegativeItem(
            text="廖家牛肉麵",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台北金華街米其林清燉牛肉麵",
            context_hint="牛肉麵店",
        ),
        HardNegativeItem(
            text="周氏蝦捲",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台南安平國宴指定小吃名店",
            context_hint="台南小吃",
        ),
        HardNegativeItem(
            text="萬巒海鴻豬腳",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="屏東萬巒客家知名傳統名店",
            context_hint="客家美食",
        ),
        HardNegativeItem(
            text="莊家火雞肉飯",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="嘉義在地傳統雞肉飯品牌",
            context_hint="傳統小吃",
        ),
        HardNegativeItem(
            text="曾記麻糬",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="花蓮名產手工麻糬名店",
            context_hint="東部名產",
        ),
        HardNegativeItem(
            text="薛家排骨飯",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="高雄傳統排骨飯便當名店",
            context_hint="便當餐飲",
        ),
        HardNegativeItem(
            text="彭園會館",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台灣湘菜名店與婚宴會館集團",
            context_hint="湘菜婚宴",
        ),
        HardNegativeItem(
            text="杜老爺冰淇淋",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台灣老牌冰淇淋與甜筒品牌",
            context_hint="冷凍食品",
        ),
        HardNegativeItem(
            text="陳允寶泉",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            confusable_with="person",
            description="台中百年太陽餅與日式和菓子名店",
            context_hint="糕餅名產",
        ),
    ]

    # 2. 公眾人物與歷史政治名詞、道路名 (Confusable with: person / address)
    _PUBLIC_HISTORICAL_FIGURES: List[HardNegativeItem] = [
        HardNegativeItem(
            text="孫中山",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="中華民國國父，歷史教科書與公開新聞人物",
            context_hint="歷史人物",
        ),
        HardNegativeItem(
            text="蔣中正",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="中華民國前總統，歷史建築與路名常用詞",
            context_hint="歷史人物",
        ),
        HardNegativeItem(
            text="蔣經國",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="中華民國前總統，歷史紀念館所涉人物",
            context_hint="歷史人物",
        ),
        HardNegativeItem(
            text="李登輝",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="中華民國前總統，公開歷史政論常見姓名",
            context_hint="歷史人物",
        ),
        HardNegativeItem(
            text="賴清德",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="現任中華民國總統，公開新聞常駐公眾人物",
            context_hint="現任政要",
        ),
        HardNegativeItem(
            text="忠孝東路",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="address",
            description="台北市最知名幹道，常單獨出現於流行文化或新聞",
            context_hint="都會幹道",
        ),
        HardNegativeItem(
            text="中山北路",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="address",
            description="台北市南北幹道，以偉人名命名，易被誤認為人名",
            context_hint="都會幹道",
        ),
        HardNegativeItem(
            text="中正路",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="address",
            description="全台灣各縣市最普遍幹道名稱，易被誤切為人名",
            context_hint="全台路名",
        ),
        HardNegativeItem(
            text="中山高速公路",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="address",
            description="國道一號，包含偉人名之國家交通主動脈",
            context_hint="國道公程",
        ),
        HardNegativeItem(
            text="中正紀念堂",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="國家級古蹟建築與地標，字首為政治人物名",
            context_hint="歷史古蹟",
        ),
        HardNegativeItem(
            text="國父紀念館",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="台北市信義區國家級展覽表演場館與紀念設施",
            context_hint="文教園區",
        ),
        HardNegativeItem(
            text="經國七海文化園區",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="台北市大直歷史文化建築園區",
            context_hint="文化園區",
        ),
        HardNegativeItem(
            text="八田與一紀念園區",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="台南烏山頭水庫紀念嘉南大圳建設工程師園區",
            context_hint="歷史園區",
        ),
        HardNegativeItem(
            text="延平北路",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="address",
            description="以延平郡王命名之台北老城區幹道",
            context_hint="歷史路名",
        ),
        HardNegativeItem(
            text="莫那魯道紀念碑",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            confusable_with="person",
            description="南投仁愛鄉霧社事件原住民英雄紀念碑",
            context_hint="紀念古蹟",
        ),
    ]

    # 3. 知名地標與公共建築地址 (Confusable with: address)
    _PUBLIC_LANDMARKS: List[HardNegativeItem] = [
        HardNegativeItem(
            text="台北101大樓（台北市信義區信義路五段7號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="台北市代表性國際知名超高摩天樓公有地標",
            context_hint="公共地標",
        ),
        HardNegativeItem(
            text="總統府（台北市中正區重慶南路一段122號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="中華民國中央政府最高元首辦公歷史建築",
            context_hint="政府中央機關",
        ),
        HardNegativeItem(
            text="行政院（台北市中正區忠孝東路一段1號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="最高行政機關所在公開政經公署",
            context_hint="政府中央機關",
        ),
        HardNegativeItem(
            text="國立故宮博物院（台北市士林區至善路二段221號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="享譽世界之國立文物展覽與典藏博物館",
            context_hint="國家博物館",
        ),
        HardNegativeItem(
            text="台北車站（台北市中正區北平西路3號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="三鐵共構核心交通中樞公開地址",
            context_hint="大眾運輸樞紐",
        ),
        HardNegativeItem(
            text="桃園國際機場（桃園市大園區航站南路9號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="台灣主要國際對外空運客貨門戶航廈",
            context_hint="國際機場",
        ),
        HardNegativeItem(
            text="台中國家歌劇院（台中市西屯區惠來路二段101號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="伊東豊雄設計之國家級表演藝術中心",
            context_hint="藝文場館",
        ),
        HardNegativeItem(
            text="高雄流行音樂中心（高雄市鹽埕區真愛路1號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="高雄港亞洲新灣區音樂文化指標公有場館",
            context_hint="藝文場館",
        ),
        HardNegativeItem(
            text="台南孔子廟（台南市中西區南門路2號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="全台首學國定古蹟公開文化園區",
            context_hint="國定古蹟",
        ),
        HardNegativeItem(
            text="國立臺灣大學（台北市大安區羅斯福路四段1號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="國立公立大學總校區代表地標",
            context_hint="公立大學校園",
        ),
        HardNegativeItem(
            text="花蓮火車站（花蓮縣花蓮市國聯一路100號）",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            confusable_with="address",
            description="東部幹線最大鐵路轉運站點",
            context_hint="公共運輸樞紐",
        ),
    ]

    # 4. 公共緊急與諮詢專線 (Confusable with: phone_number)
    _PUBLIC_HOTLINES: List[HardNegativeItem] = [
        HardNegativeItem(
            text="1999",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="各縣市政府市民當家熱線與市政服務專線",
            context_hint="市政諮詢",
        ),
        HardNegativeItem(
            text="165",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="內政部警政署反詐騙諮詢求助專線",
            context_hint="反詐騙專線",
        ),
        HardNegativeItem(
            text="110",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="警政署報案求救報警專線",
            context_hint="緊急報案",
        ),
        HardNegativeItem(
            text="119",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="消防局火警滅火與緊急救護通報專線",
            context_hint="緊急救護",
        ),
        HardNegativeItem(
            text="1922",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="衛福部疾病管制署防疫求助與疫情通報專線",
            context_hint="防疫專線",
        ),
        HardNegativeItem(
            text="1980",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="張老師青少年與心理輔導諮商專線",
            context_hint="心理諮商",
        ),
        HardNegativeItem(
            text="1925",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="衛福部24小時免付費安心諮詢求助專線",
            context_hint="生命教育",
        ),
        HardNegativeItem(
            text="113",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="家庭暴力及性侵害保護防治求助專線",
            context_hint="婦幼保護",
        ),
        HardNegativeItem(
            text="1950",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="全國消費者保護服務與申訴諮詢專線",
            context_hint="消保申訴",
        ),
        HardNegativeItem(
            text="168",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="交通部公路總局路況語音查詢專線",
            context_hint="交通路況",
        ),
        HardNegativeItem(
            text="1968",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="高公局高速公路即時路況查詢客服專線",
            context_hint="國道客服",
        ),
        HardNegativeItem(
            text="0800-000-123",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="公共事業企業公開免付費客服號碼",
            context_hint="免付費客服",
        ),
        HardNegativeItem(
            text="0800-080-412",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="電信公司障礙申告與客服專線",
            context_hint="電信服務",
        ),
        HardNegativeItem(
            text="0800-030-598",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            confusable_with="phone_number",
            description="中央健康保險署全民諮詢專線",
            context_hint="健保諮詢",
        ),
    ]

    # 5. 公開機關/學校/通用服務信箱 (Confusable with: email)
    _PUBLIC_EMAILS: List[HardNegativeItem] = [
        HardNegativeItem(
            text="service@gov.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="國家發展委員會政府數位公開服務通用信箱",
            context_hint="政府入口網",
        ),
        HardNegativeItem(
            text="admissions@ntu.edu.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="國立臺灣大學教務處公開招生組諮詢信箱",
            context_hint="大學招生",
        ),
        HardNegativeItem(
            text="mayor@gov.taipei",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="台北市政府市長與市民信箱公開民意管道",
            context_hint="市政信箱",
        ),
        HardNegativeItem(
            text="contact@president.gov.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="總統府全球資訊網公開公共聯絡電郵",
            context_hint="公署信箱",
        ),
        HardNegativeItem(
            text="info@itri.org.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="工業技術研究院公開諮詢與公關信箱",
            context_hint="公營研發",
        ),
        HardNegativeItem(
            text="service@cht.com.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="中華電信公開服務專用客戶支援信箱",
            context_hint="公開客服",
        ),
        HardNegativeItem(
            text="press@mfa.gov.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="外交部公眾外交協調會公開新聞聯絡信箱",
            context_hint="新聞公關",
        ),
        HardNegativeItem(
            text="cs@post.gov.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="中華郵政公開業務諮詢與服務電子郵件",
            context_hint="郵政服務",
        ),
        HardNegativeItem(
            text="privacy@twcert.org.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="台灣電腦網路危機處理暨協調中心通報信箱",
            context_hint="資安通報",
        ),
        HardNegativeItem(
            text="consumer@ey.gov.tw",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            confusable_with="email",
            description="行政院消費者保護處公開申訴信箱",
            context_hint="消保申訴",
        ),
    ]

    # 6. 發票號碼、物流單號、公文字號與代碼 (Confusable with: tax_id, national_id_number, etc.)
    _OFFICIAL_CODE_NUMBERS: List[HardNegativeItem] = [
        HardNegativeItem(
            text="AB-12345678",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tax_id",
            description="財政部統一發票兩碼英文八碼數字之營業稅票號",
            context_hint="統一發票",
        ),
        HardNegativeItem(
            text="QP-98765432",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tax_id",
            description="財政部雲端電子發票字軌與開立號碼",
            context_hint="電子發票",
        ),
        HardNegativeItem(
            text="TW9876543210123",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="bank_account",
            description="台灣跨境海關與黑貓宅急便物流追蹤貨態單號",
            context_hint="物流單號",
        ),
        HardNegativeItem(
            text="711-89230194",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tw_nhi_card",
            description="統一超商交貨便取貨驗證與寄件服務代碼",
            context_hint="超商物流",
        ),
        HardNegativeItem(
            text="府工建字第1120123456號",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tw_household_no",
            description="直轄市政府工務局建築執照核發公文字號",
            context_hint="公文字號",
        ),
        HardNegativeItem(
            text="衛部醫字第1131660123號",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tw_medical_license",
            description="衛生福利部醫事人員法規核定與函釋公文字號",
            context_hint="部頒字號",
        ),
        HardNegativeItem(
            text="診號：035號",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="tw_nhi_card",
            description="醫院各專科門診看診即時叫號流水號",
            context_hint="門診序號",
        ),
        HardNegativeItem(
            text="檢驗單號：LAB-2024-99881",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            confusable_with="national_id_number",
            description="大型醫學中心臨床抽血檢驗內部工作單號",
            context_hint="醫檢序號",
        ),
    ]

    _ALL_ITEMS_BY_CAT: Dict[HardNegativeCategory, List[HardNegativeItem]] = {
        HardNegativeCategory.BRAND_PERSON_NAME: _BRAND_PERSON_NAMES,
        HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE: _PUBLIC_HISTORICAL_FIGURES,
        HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS: _PUBLIC_LANDMARKS,
        HardNegativeCategory.PUBLIC_HOTLINE: _PUBLIC_HOTLINES,
        HardNegativeCategory.PUBLIC_EMAIL: _PUBLIC_EMAILS,
        HardNegativeCategory.OFFICIAL_CODE_NUMBER: _OFFICIAL_CODE_NUMBERS,
    }

    @classmethod
    def get_items(cls, category: HardNegativeCategory) -> List[HardNegativeItem]:
        """Returns all items in a given category."""
        return cls._ALL_ITEMS_BY_CAT.get(category, [])

    @classmethod
    def all_items(cls) -> List[HardNegativeItem]:
        """Returns all items across all categories."""
        res: List[HardNegativeItem] = []
        for items in cls._ALL_ITEMS_BY_CAT.values():
            res.extend(items)
        return res

    @classmethod
    def sample(
        cls,
        category: HardNegativeCategory,
        seed: Optional[int] = None,
    ) -> HardNegativeItem:
        """Samples a random item from a given category."""
        items = cls.get_items(category)
        if not items:
            raise ValueError(f"No items available for category: {category}")
        rng = random.Random(seed) if seed is not None else random.Random()
        return rng.choice(items)

    @classmethod
    def sample_any(cls, seed: Optional[int] = None) -> HardNegativeItem:
        """Samples a random item across all categories."""
        all_items = cls.all_items()
        rng = random.Random(seed) if seed is not None else random.Random()
        return rng.choice(all_items)
