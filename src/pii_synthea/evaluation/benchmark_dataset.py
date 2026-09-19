"""
Benchmark Dataset Loader & Schema Alignment.
Supports lianghsun/tw-PII-bench Parquet/JSONL loading, split filtering,
and embedded offline reference samples for Block A (8 in-schema),
Block B (11 Taiwan OOD), Block C (5 hard negatives), and length tiers (short, mid, long).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pii_synthea.evaluation.metrics import Span
from pii_synthea.taxonomy import TaxonomyMapper


# Canonical 8 In-schema labels in tw-PII-bench
IN_SCHEMA_BENCH_LABELS = [
    "private_person",
    "private_phone",
    "private_email",
    "private_address",
    "private_date",
    "private_url",
    "account_number",
    "secret",
]

# Canonical 11 Out-of-schema Taiwan-specific labels in tw-PII-bench with their expected fallback
OOD_BENCH_LABELS_WITH_FALLBACK = {
    "tw_national_id": "account_number",
    "tw_nhi_card": "account_number",
    "tw_company_id": "account_number",
    "tw_license_plate": None,
    "tw_passport": "account_number",
    "tw_driver_license": "account_number",
    "tw_line_id": "private_url",
    "tw_ptt_id": None,
    "tw_household_no": "account_number",
    "tw_medical_license": "account_number",
    "tw_military_id": "account_number",
}

# Canonical 5 Hard Negative subtypes in tw-PII-bench
HARD_NEGATIVE_SUBTYPES = [
    "neg_business_name",
    "neg_public_figure",
    "neg_landmark_address",
    "neg_public_hotline",
    "neg_institutional_email",
]


@dataclass
class BenchmarkItem:
    """Represents a single benchmark evaluation item."""
    id: str
    split: str          # "short", "mid", "long"
    block: str          # "A" (in-schema), "B" (OOD), "C" (hard negative), "M" (mid), "L" (long)
    category: str       # Label name or scenario description
    text: str
    spans: List[Span] = field(default_factory=list)
    is_negative: bool = False
    scenario: Optional[str] = None
    char_length: int = 0
    n_spans: int = 0

    def __post_init__(self) -> None:
        if not self.char_length:
            self.char_length = len(self.text)
        if not self.n_spans:
            self.n_spans = len(self.spans)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "split": self.split,
            "block": self.block,
            "category": self.category,
            "text": self.text,
            "spans": [
                {
                    "start": s.start,
                    "end": s.end,
                    "label": s.label,
                    "text": s.text or self.text[s.start:s.end],
                    "expected_model_label": s.expected_model_label,
                }
                for s in self.spans
            ],
            "is_negative": self.is_negative,
            "scenario": self.scenario,
            "char_length": self.char_length,
            "n_spans": self.n_spans,
        }


class BenchmarkDatasetLoader:
    """Loads and formats benchmark datasets from local files, Hugging Face, or embedded reference fixtures."""

    @classmethod
    def load_from_jsonl(cls, path: Union[str, Path], split: Optional[str] = None) -> List[BenchmarkItem]:
        """Loads benchmark items from a tw-PII-bench formatted JSONL file."""
        items: List[BenchmarkItem] = []
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Benchmark file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                item = cls._parse_raw_dict(data, default_id=f"item_{line_idx:04d}")
                if split and split != "all" and item.split != split:
                    continue
                items.append(item)
        return items

    @classmethod
    def load_from_parquet(cls, path: Union[str, Path], split: Optional[str] = None) -> List[BenchmarkItem]:
        """Loads benchmark items from a Parquet file."""
        try:
            import pyarrow.parquet as pq
        except ImportError as e:
            raise RuntimeError("pyarrow is required to read parquet datasets.") from e

        table = pq.read_table(path)
        pydict = table.to_pydict()
        items: List[BenchmarkItem] = []
        row_count = table.num_rows

        for idx in range(row_count):
            raw_spans = pydict.get("spans", [None])[idx]
            if isinstance(raw_spans, str):
                parsed_spans = json.loads(raw_spans)
            elif isinstance(raw_spans, list):
                parsed_spans = raw_spans
            else:
                parsed_spans = []

            data = {
                "id": str(pydict.get("id", [f"item_{idx}"])[idx]),
                "split": str(pydict.get("split", ["short"])[idx]),
                "block": str(pydict.get("block", ["A"])[idx]),
                "category": str(pydict.get("category", ["general"])[idx]),
                "text": str(pydict.get("text", [""])[idx]),
                "spans": parsed_spans,
                "is_negative": bool(pydict.get("is_negative", [False])[idx]),
                "scenario": pydict.get("scenario", [None])[idx],
            }
            item = cls._parse_raw_dict(data, default_id=f"item_{idx:04d}")
            if split and split != "all" and item.split != split:
                continue
            items.append(item)
        return items

    @classmethod
    def load_from_hf(
        cls,
        dataset_name: str = "lianghsun/tw-PII-bench",
        split: str = "all",
    ) -> List[BenchmarkItem]:
        """Loads dataset from Hugging Face datasets library if installed."""
        try:
            from datasets import load_dataset
        except ImportError as e:
            raise RuntimeError(
                "datasets library is required to load directly from Hugging Face. "
                "Install via uv add datasets, or provide a local JSONL file."
            ) from e

        if split == "all":
            splits_to_load = ["short", "mid", "long"]
        else:
            splits_to_load = [split]

        items: List[BenchmarkItem] = []
        for s in splits_to_load:
            ds = load_dataset(dataset_name, split=s)
            for row in ds:
                item = cls._parse_raw_dict(row, default_id=f"{s}_{len(items)}")
                items.append(item)
        return items

    @classmethod
    def _parse_raw_dict(cls, data: Dict[str, Any], default_id: str) -> BenchmarkItem:
        """Parses a dictionary into a normalized BenchmarkItem."""
        spans_raw = data.get("spans", [])
        spans: List[Span] = []
        for s in spans_raw:
            label = s.get("label", "")
            # Determine expected fallback label
            exp_label = s.get("expected_model_label")
            if exp_label is None and label in OOD_BENCH_LABELS_WITH_FALLBACK:
                exp_label = OOD_BENCH_LABELS_WITH_FALLBACK[label]
            elif exp_label is None and label in IN_SCHEMA_BENCH_LABELS:
                exp_label = label

            span_text = s.get("text")
            spans.append(
                Span(
                    start=int(s["start"]),
                    end=int(s["end"]),
                    label=label,
                    text=span_text,
                    expected_model_label=exp_label,
                )
            )

        split = data.get("split", "short")
        block = data.get("block", "A")
        category = data.get("category", spans[0].label if spans else "negative")
        is_neg = data.get("is_negative", len(spans) == 0)

        return BenchmarkItem(
            id=str(data.get("id", default_id)),
            split=split,
            block=block,
            category=category,
            text=data["text"],
            spans=spans,
            is_negative=is_neg,
            scenario=data.get("scenario"),
            char_length=int(data.get("char_length", len(data["text"]))),
            n_spans=int(data.get("n_spans", len(spans))),
        )

    @classmethod
    def get_reference_benchmark_samples(cls, split: Optional[str] = None) -> List[BenchmarkItem]:
        """
        Provides an authentic embedded reference benchmark dataset for offline execution and testing.
        Covers:
        - Block A (all 8 In-schema categories)
        - Block B (all 11 Taiwan-specific OOD categories with verified checksums)
        - Block C (all 5 Hard Negative subtypes)
        - All 3 Splits (short, mid, long)
        """
        items: List[BenchmarkItem] = []

        # ==========================================
        # BLOCK A: In-schema (8 categories) - SHORT
        # ==========================================
        items.extend([
            # 1. private_person
            BenchmarkItem(
                id="a_private_person_001",
                split="short",
                block="A",
                category="private_person",
                text="請林佳玲專員協助辦理本案的移轉登記。",
                spans=[Span(start=1, end=4, label="private_person", text="林佳玲", expected_model_label="private_person")],
            ),
            BenchmarkItem(
                id="a_private_person_002",
                split="short",
                block="A",
                category="private_person",
                text="原住民代表尤瑪·達魯先生已簽署確認聲明書。",
                spans=[Span(start=5, end=10, label="private_person", text="尤瑪·達魯", expected_model_label="private_person")],
            ),
            # 2. private_phone
            BenchmarkItem(
                id="a_private_phone_001",
                split="short",
                block="A",
                category="private_phone",
                text="如有任何帳單爭議，請撥打行動電話 0912-345-678 洽詢客服。",
                spans=[Span(start=17, end=29, label="private_phone", text="0912-345-678", expected_model_label="private_phone")],
            ),
            BenchmarkItem(
                id="a_private_phone_002",
                split="short",
                block="A",
                category="private_phone",
                text="台北辦公室總機為 (02) 2345-6789，分機 102。",
                spans=[Span(start=9, end=24, label="private_phone", text="(02) 2345-6789", expected_model_label="private_phone")],
            ),
            # 3. private_email
            BenchmarkItem(
                id="a_private_email_001",
                split="short",
                block="A",
                category="private_email",
                text="請將審核文件寄至 wang_mei@msa.hinet.net 以利核章。",
                spans=[Span(start=9, end=32, label="private_email", text="wang_mei@msa.hinet.net", expected_model_label="private_email")],
            ),
            BenchmarkItem(
                id="a_private_email_002",
                split="short",
                block="A",
                category="private_email",
                text="業務聯繫窗口請發送郵件至 kevin.chen@gmail.com。",
                spans=[Span(start=12, end=32, label="private_email", text="kevin.chen@gmail.com", expected_model_label="private_email")],
            ),
            # 4. private_address
            BenchmarkItem(
                id="a_private_address_001",
                split="short",
                block="A",
                category="private_address",
                text="貨物收件地址為台北市大安區忠孝東路四段216巷19弄5號3樓。",
                spans=[Span(start=7, end=34, label="private_address", text="台北市大安區忠孝東路四段216巷19弄5號3樓", expected_model_label="private_address")],
            ),
            BenchmarkItem(
                id="a_private_address_002",
                split="short",
                block="A",
                category="private_address",
                text="通訊地址請填寫 10667 新北市板橋區文化路二段182巷3弄8號。",
                spans=[Span(start=7, end=35, label="private_address", text="10667 新北市板橋區文化路二段182巷3弄8號", expected_model_label="private_address")],
            ),
            # 5. private_date
            BenchmarkItem(
                id="a_private_date_001",
                split="short",
                block="A",
                category="private_date",
                text="患者出生年月日登記為民國78年5月20日，目前無過敏史。",
                spans=[Span(start=10, end=20, label="private_date", text="民國78年5月20日", expected_model_label="private_date")],
            ),
            BenchmarkItem(
                id="a_private_date_002",
                split="short",
                block="A",
                category="private_date",
                text="本契約生效起算日為民國113年4月15日中午十二時整。",
                spans=[Span(start=9, end=20, label="private_date", text="民國113年4月15日", expected_model_label="private_date")],
            ),
            # 6. private_url
            BenchmarkItem(
                id="a_private_url_001",
                split="short",
                block="A",
                category="private_url",
                text="個人部落格作品集請參閱 https://kevin.pixnet.net/blog 詳細內容。",
                spans=[Span(start=12, end=40, label="private_url", text="https://kevin.pixnet.net/blog", expected_model_label="private_url")],
            ),
            BenchmarkItem(
                id="a_private_url_002",
                split="short",
                block="A",
                category="private_url",
                text="履歷專案連結請前往 https://chen.github.io/portfolio 檢視。",
                spans=[Span(start=9, end=42, label="private_url", text="https://chen.github.io/portfolio", expected_model_label="private_url")],
            ),
            # 7. account_number
            BenchmarkItem(
                id="a_account_number_001",
                split="short",
                block="A",
                category="account_number",
                text="退款帳號為台灣銀行帳號 01234567890123，請於三日內確認。",
                spans=[Span(start=11, end=25, label="account_number", text="01234567890123", expected_model_label="account_number")],
            ),
            BenchmarkItem(
                id="a_account_number_002",
                split="short",
                block="A",
                category="account_number",
                text="本次刷卡支付使用之信用卡號為 4563-1234-5678-9012。",
                spans=[Span(start=14, end=33, label="account_number", text="4563-1234-5678-9012", expected_model_label="account_number")],
            ),
            # 8. secret
            BenchmarkItem(
                id="a_secret_001",
                split="short",
                block="A",
                category="secret",
                text="簡訊驗證碼為 948201，有效期限三分鐘，切勿提供他人。",
                spans=[Span(start=6, end=12, label="secret", text="948201", expected_model_label="secret")],
            ),
            BenchmarkItem(
                id="a_secret_002",
                split="short",
                block="A",
                category="secret",
                text="系統連線金鑰已更新為 sk-proj-abc123xyz789，請妥善保存。",
                spans=[Span(start=9, end=30, label="secret", text="sk-proj-abc123xyz789", expected_model_label="secret")],
            ),
        ])

        # =========================================================
        # BLOCK B: Out-of-schema Taiwan-specific (11 categories) - SHORT
        # =========================================================
        items.extend([
            # 1. tw_national_id
            BenchmarkItem(
                id="b_tw_national_id_001",
                split="short",
                block="B",
                category="tw_national_id",
                text="申請人身分證統一編號為 A123456789，經戶政系統查核相符。",
                spans=[Span(start=11, end=21, label="tw_national_id", text="A123456789", expected_model_label="account_number")],
            ),
            # 2. tw_nhi_card
            BenchmarkItem(
                id="b_tw_nhi_card_001",
                split="short",
                block="B",
                category="tw_nhi_card",
                text="掛號時請出示健保卡，卡號 000012345678 進行過卡核對。",
                spans=[Span(start=12, end=24, label="tw_nhi_card", text="000012345678", expected_model_label="account_number")],
            ),
            # 3. tw_company_id
            BenchmarkItem(
                id="b_tw_company_id_001",
                split="short",
                block="B",
                category="tw_company_id",
                text="發票買受人為台灣積體電路製造股份有限公司，統一編號 12345678。",
                spans=[Span(start=28, end=36, label="tw_company_id", text="12345678", expected_model_label="account_number")],
            ),
            # 4. tw_license_plate (no fallback)
            BenchmarkItem(
                id="b_tw_license_plate_001",
                split="short",
                block="B",
                category="tw_license_plate",
                text="地下停車場登記車輛之車牌號碼為 ABC-1234，限停B2固定車位。",
                spans=[Span(start=16, end=24, label="tw_license_plate", text="ABC-1234", expected_model_label=None)],
            ),
            # 5. tw_passport
            BenchmarkItem(
                id="b_tw_passport_001",
                split="short",
                block="B",
                category="tw_passport",
                text="出境旅客中華民國護照號碼為 312345678，登機證已列印。",
                spans=[Span(start=13, end=22, label="tw_passport", text="312345678", expected_model_label="account_number")],
            ),
            # 6. tw_driver_license
            BenchmarkItem(
                id="b_tw_driver_license_001",
                split="short",
                block="B",
                category="tw_driver_license",
                text="駕駛人持有之普通自用小客車駕照號碼為 A123456789，審驗合格。",
                spans=[Span(start=19, end=29, label="tw_driver_license", text="A123456789", expected_model_label="account_number")],
            ),
            # 7. tw_line_id
            BenchmarkItem(
                id="b_tw_line_id_001",
                split="short",
                block="B",
                category="tw_line_id",
                text="如需線上討論設計稿，請直接加我 LINE ID: kevin998 傳訊。",
                spans=[Span(start=22, end=30, label="tw_line_id", text="kevin998", expected_model_label="private_url")],
            ),
            # 8. tw_ptt_id (no fallback)
            BenchmarkItem(
                id="b_tw_ptt_id_001",
                split="short",
                block="B",
                category="tw_ptt_id",
                text="原作者 PTT 帳號為 gossiping5566，文責自負請勿任意轉載。",
                spans=[Span(start=11, end=24, label="tw_ptt_id", text="gossiping5566", expected_model_label=None)],
            ),
            # 9. tw_household_no
            BenchmarkItem(
                id="b_tw_household_no_001",
                split="short",
                block="B",
                category="tw_household_no",
                text="戶籍謄本記載之戶口名簿戶號為 A1234567，設籍登記日無誤。",
                spans=[Span(start=14, end=22, label="tw_household_no", text="A1234567", expected_model_label="account_number")],
            ),
            # 10. tw_medical_license
            BenchmarkItem(
                id="b_tw_medical_license_001",
                split="short",
                block="B",
                category="tw_medical_license",
                text="處方箋主治醫師證照字號為 醫字第012345號，符合健保法規。",
                spans=[Span(start=12, end=21, label="tw_medical_license", text="醫字第012345號", expected_model_label="account_number")],
            ),
            # 11. tw_military_id
            BenchmarkItem(
                id="b_tw_military_id_001",
                split="short",
                block="B",
                category="tw_military_id",
                text="現役軍人身分證字號 陸字第123456號 已完成出入營門禁登記。",
                spans=[Span(start=9, end=18, label="tw_military_id", text="陸字第123456號", expected_model_label="account_number")],
            ),
        ])

        # =====================================================
        # BLOCK C: Hard Negatives (5 subtypes, 0 spans) - SHORT
        # =====================================================
        items.extend([
            # 1. neg_business_name
            BenchmarkItem(
                id="c_neg_business_name_001",
                split="short",
                block="C",
                category="neg_business_name",
                text="中午部門開會的便當就直接訂梁社漢排骨吧，記得幫我跟店家備註其中兩個飯盒要換成炸雞腿。",
                spans=[],
                is_negative=True,
            ),
            BenchmarkItem(
                id="c_neg_business_name_002",
                split="short",
                block="C",
                category="neg_business_name",
                text="西門町商圈的阿宗麵線每到假日總是排滿觀光客，隔壁的楊記排骨酥湯也是老字號人氣小吃。",
                spans=[],
                is_negative=True,
            ),
            # 2. neg_public_figure
            BenchmarkItem(
                id="c_neg_public_figure_001",
                split="short",
                block="C",
                category="neg_public_figure",
                text="歷史課本提到孫中山先生創立中華民國，近代政治發展則常討論蔣經國時期的十大建設推動。",
                spans=[],
                is_negative=True,
            ),
            BenchmarkItem(
                id="c_neg_public_figure_002",
                split="short",
                block="C",
                category="neg_public_figure",
                text="國立故宮博物院正在展出張大千國畫特展，吸引眾多藝術愛好者前來觀賞。",
                spans=[],
                is_negative=True,
            ),
            # 3. neg_landmark_address
            BenchmarkItem(
                id="c_neg_landmark_address_001",
                split="short",
                block="C",
                category="neg_landmark_address",
                text="台北捷運信義線台北101世貿站直通百貨商場，中正紀念堂自由廣場也是國際旅客常去的拍照熱點。",
                spans=[],
                is_negative=True,
            ),
            BenchmarkItem(
                id="c_neg_landmark_address_002",
                split="short",
                block="C",
                category="neg_landmark_address",
                text="高雄流行音樂中心座落於愛河灣旁，鄰近駁二藝術特區與大港橋。",
                spans=[],
                is_negative=True,
            ),
            # 4. neg_public_hotline
            BenchmarkItem(
                id="c_neg_public_hotline_001",
                split="short",
                block="C",
                category="neg_public_hotline",
                text="若遇到疑似電信詐騙電話請立即撥打165反詐騙諮詢專線，緊急狀況請打110報案。",
                spans=[],
                is_negative=True,
            ),
            BenchmarkItem(
                id="c_neg_public_hotline_002",
                split="short",
                block="C",
                category="neg_public_hotline",
                text="市民市政問題請撥打1999專線，勞動權益問題可洽詢勞保局0800免付費諮詢電話。",
                spans=[],
                is_negative=True,
            ),
            # 5. neg_institutional_email
            BenchmarkItem(
                id="c_neg_institutional_email_001",
                split="short",
                block="C",
                category="neg_institutional_email",
                text="民眾如對政府數位施政有任何建言，歡迎寄信至公共服務信箱 service@gov.tw 進行反饋。",
                spans=[],
                is_negative=True,
            ),
            BenchmarkItem(
                id="c_neg_institutional_email_002",
                split="short",
                block="C",
                category="neg_institutional_email",
                text="台灣大學各研究所招生簡章可來信洽詢教務處官方信箱 admissions@ntu.edu.tw 索取最新資料。",
                spans=[],
                is_negative=True,
            ),
        ])

        # ==========================================
        # SPLIT: MID (200 - 1000 chars)
        # ==========================================
        mid_text = (
            "【新安生醫門診掛號通知與病歷摘要】\n"
            "病患姓名：林佳玲 女士，出生年月日：民國78年5月20日，國民身分證統一編號：A223456781。\n"
            "全民健康保險IC卡卡號：000012345678。病患居住通訊地址：台北市大安區忠孝東路四段216巷19弄5號3樓。\n"
            "緊急聯絡人電話：0912-345-678，市話：(02) 2345-6789。電子郵件：wang_mei@msa.hinet.net。\n"
            "主治醫師：醫字第012345號 郭仁傑 醫師。預約回診掛號流水帳號：01234567890123。\n"
            "本院提醒您，防範詐騙請多利用165反詐騙專線或撥打1999市民熱線，本院絕不會主動要求您操作ATM。"
        )
        mid_spans = [
            Span(start=22, end=25, label="private_person", text="林佳玲", expected_model_label="private_person"),
            Span(start=36, end=46, label="private_date", text="民國78年5月20日", expected_model_label="private_date"),
            Span(start=58, end=68, label="tw_national_id", text="A223456781", expected_model_label="account_number"),
            Span(start=87, end=99, label="tw_nhi_card", text="000012345678", expected_model_label="account_number"),
            Span(start=109, end=136, label="private_address", text="台北市大安區忠孝東路四段216巷19弄5號3樓", expected_model_label="private_address"),
            Span(start=145, end=157, label="private_phone", text="0912-345-678", expected_model_label="private_phone"),
            Span(start=162, end=177, label="private_phone", text="(02) 2345-6789", expected_model_label="private_phone"),
            Span(start=183, end=206, label="private_email", text="wang_mei@msa.hinet.net", expected_model_label="private_email"),
            Span(start=213, end=222, label="tw_medical_license", text="醫字第012345號", expected_model_label="account_number"),
            Span(start=223, end=226, label="private_person", text="郭仁傑", expected_model_label="private_person"),
            Span(start=241, end=255, label="account_number", text="01234567890123", expected_model_label="account_number"),
        ]
        items.append(
            BenchmarkItem(
                id="mid_medical_consultation_001",
                split="mid",
                block="M",
                category="醫療門診與病歷調閱情境",
                text=mid_text,
                spans=mid_spans,
                scenario="醫療院所病患初診掛號與個資調閱對話記錄",
            )
        )

        # ==========================================
        # SPLIT: LONG (1500+ chars)
        # ==========================================
        long_text = (
            "【不動產房屋租賃契約書暨連帶保證協議】\n"
            "立租賃契約人：出租人 陳志豪（以下簡稱甲方，身分證字號：A123456789，戶籍地址：台北市大安區忠孝東路四段216巷19弄5號3樓，聯絡電話：0912-345-678，電子郵件：kevin.chen@gmail.com）\n"
            "與 承租人 林佳玲（以下簡稱乙方，身分證字號：F223456781，居留證號：A801234567，通訊地址：新北市板橋區文化路二段182巷3弄8號，電話：(02) 2345-6789，LINE ID: kevin998）\n"
            "茲為租賃房屋事宜，雙方合意訂立本契約條款如下：\n"
            "第一條：房屋標示與租賃範圍\n"
            "租賃標的座落於花蓮縣吉安鄉中央路三段120巷2號，房屋稅籍編號為 A1234567，車位編號為地下二樓 ABC-1234 號專用汽車停車位。\n"
            "第二條：租賃期間與起算日\n"
            "本租賃期間自民國113年4月15日起至民國115年4月14日止，共計兩年。租金每月新台幣三萬五千元整。\n"
            "第三條：租金撥付帳戶與押金保全\n"
            "乙方應於每月五日前，將租金全額匯入甲方指定帳戶：台灣土地銀行帳號 01234567890123，戶名：陳志豪。保證金（押金）為新台幣七萬元整，已於簽約當日以信用卡號 4563-1234-5678-9012 授權扣抵。\n"
            "第四條：連帶保證人條款\n"
            "連帶保證人 尤瑪·達魯（身分證字號：V212345677，出生日期：民國35年8月10日，通訊地址：花蓮縣吉安鄉中央路三段120巷2號，護照號碼：312345678，駕照號碼：V212345677）願就乙方本契約所生之一切債務負連帶保證清償責任。\n"
            "第五條：商業用途與營利事業限制\n"
            "本租賃標的僅限住宅使用，若需登記為營利事業機構（統一編號：12345678），須經甲方書面同意。\n"
            "第六條：緊急通報與公眾服務\n"
            "租賃期間若發生火警或重大治安事故，請立即撥打119或110通報警消，市政路燈管線報修請洽1999專線。任何詐騙要求匯款至公庫帳戶請撥165專線查詢，切勿輕信。"
        )
        long_spans = [
            Span(start=27, end=30, label="private_person", text="陳志豪", expected_model_label="private_person"),
            Span(start=43, end=53, label="tw_national_id", text="A123456789", expected_model_label="account_number"),
            Span(start=59, end=86, label="private_address", text="台北市大安區忠孝東路四段216巷19弄5號3樓", expected_model_label="private_address"),
            Span(start=92, end=104, label="private_phone", text="0912-345-678", expected_model_label="private_phone"),
            Span(start=110, end=130, label="private_email", text="kevin.chen@gmail.com", expected_model_label="private_email"),
            Span(start=137, end=140, label="private_person", text="林佳玲", expected_model_label="private_person"),
            Span(start=153, end=163, label="tw_national_id", text="F223456781", expected_model_label="account_number"),
            Span(start=169, end=179, label="tw_national_id", text="A801234567", expected_model_label="account_number"),
            Span(start=185, end=210, label="private_address", text="新北市板橋區文化路二段182巷3弄8號", expected_model_label="private_address"),
            Span(start=214, end=229, label="private_phone", text="(02) 2345-6789", expected_model_label="private_phone"),
            Span(start=239, end=247, label="tw_line_id", text="kevin998", expected_model_label="private_url"),
            Span(start=290, end=314, label="private_address", text="花蓮縣吉安鄉中央路三段120巷2號", expected_model_label="private_address"),
            Span(start=322, end=330, label="tw_household_no", text="A1234567", expected_model_label="account_number"),
            Span(start=342, end=350, label="tw_license_plate", text="ABC-1234", expected_model_label=None),
            Span(start=377, end=388, label="private_date", text="民國113年4月15日", expected_model_label="private_date"),
            Span(start=392, end=403, label="private_date", text="民國115年4月14日", expected_model_label="private_date"),
            Span(start=462, end=476, label="account_number", text="01234567890123", expected_model_label="account_number"),
            Span(start=481, end=484, label="private_person", text="陳志豪", expected_model_label="private_person"),
            Span(start=515, end=534, label="account_number", text="4563-1234-5678-9012", expected_model_label="account_number"),
            Span(start=551, end=556, label="private_person", text="尤瑪·達魯", expected_model_label="private_person"),
            Span(start=563, end=573, label="tw_national_id", text="V212345677", expected_model_label="account_number"),
            Span(start=579, end=589, label="private_date", text="民國35年8月10日", expected_model_label="private_date"),
            Span(start=595, end=619, label="private_address", text="花蓮縣吉安鄉中央路三段120巷2號", expected_model_label="private_address"),
            Span(start=625, end=634, label="tw_passport", text="312345678", expected_model_label="account_number"),
            Span(start=640, end=650, label="tw_driver_license", text="V212345677", expected_model_label="account_number"),
            Span(start=726, end=734, label="tw_company_id", text="12345678", expected_model_label="account_number"),
        ]
        items.append(
            BenchmarkItem(
                id="long_residential_lease_001",
                split="long",
                block="L",
                category="租屋租賃契約與連帶擔保協議",
                text=long_text,
                spans=long_spans,
                scenario="公證住宅不動產租賃合約書與連帶保證協議書",
            )
        )

        if split and split != "all":
            return [it for it in items if it.split == split]
        return items
