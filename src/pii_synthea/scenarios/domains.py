"""
Domain categories, length distributions, and scenario definitions
for Taiwan PII synthetic data generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class DomainCategory(str, Enum):
    """Primary industry and situational domains for Taiwan PII synthesis."""
    HEALTHCARE = "healthcare"
    BANKING_FINANCE = "banking_finance"
    TELECOM = "telecom"
    ECOMMERCE_LOGISTICS = "ecommerce_logistics"
    REAL_ESTATE = "real_estate"
    LEGAL_CONSULTATION = "legal_consultation"

    @property
    def display_name_zh(self) -> str:
        names = {
            DomainCategory.HEALTHCARE: "醫療院所與公衛",
            DomainCategory.BANKING_FINANCE: "金融銀行與支付",
            DomainCategory.TELECOM: "電信通訊與資費",
            DomainCategory.ECOMMERCE_LOGISTICS: "網購電商與物流配送",
            DomainCategory.REAL_ESTATE: "租屋不動產與物業",
            DomainCategory.LEGAL_CONSULTATION: "法律諮詢與民事調解",
        }
        return names.get(self, self.value)

    @property
    def description_zh(self) -> str:
        descs = {
            DomainCategory.HEALTHCARE: "醫院門診掛號、病歷摘要、診斷證明書、用藥紀錄、健保卡申報與衛教照會。",
            DomainCategory.BANKING_FINANCE: "銀行開戶徵信、信用卡爭議款、跨行匯款照會、房貸信貸申請、網銀登入與 OTP 驗證通知。",
            DomainCategory.TELECOM: "5G 門號攜碼續約、SIM 卡遺失補發、光纖寬頻預約裝機、紙本電子資費明細與過戶異動。",
            DomainCategory.ECOMMERCE_LOGISTICS: "蝦皮超商取貨、黑貓宅急便配送、退換貨退款爭議、EZ WAY 實名認證與買賣家私訊溝通。",
            DomainCategory.REAL_ESTATE: "房屋租賃契約、帶看定金收據、房東租客點交清冊、修繕通知與內政部租金補貼申請。",
            DomainCategory.LEGAL_CONSULTATION: "車禍民事賠償和解書、勞資爭議調解聲請、律師委任契約、當事人陳述與郵局存證信函草稿。",
        }
        return descs.get(self, "")


class TextLengthCategory(str, Enum):
    """Text length distribution categories matching real-world and benchmark scales."""
    SHORT = "short"
    MID = "mid"
    LONG = "long"

    @property
    def min_chars(self) -> int:
        ranges = {
            TextLengthCategory.SHORT: 15,
            TextLengthCategory.MID: 200,
            TextLengthCategory.LONG: 1500,
        }
        return ranges[self]

    @property
    def max_chars(self) -> int:
        ranges = {
            TextLengthCategory.SHORT: 120,
            TextLengthCategory.MID: 1000,
            TextLengthCategory.LONG: 5000,
        }
        return ranges[self]

    @property
    def label_zh(self) -> str:
        labels = {
            TextLengthCategory.SHORT: "短句 (15-120 字)：單輪客服、簡訊驗證、交易推播、到貨通知",
            TextLengthCategory.MID: "中篇 (200-1000 字)：LINE 對話、客訴電郵、申辦表單、問答紀錄",
            TextLengthCategory.LONG: "長篇 (1500-5000 字)：正式病歷、租賃/勞動合約、會議紀錄、和解協議書",
        }
        return labels[self]

    @classmethod
    def categorize(cls, length: int) -> TextLengthCategory:
        """Categorizes a character length into SHORT, MID, or LONG."""
        if length < 150:
            return cls.SHORT
        elif length < 1200:
            return cls.MID
        else:
            return cls.LONG


@dataclass(frozen=True)
class ScenarioDefinition:
    """Metadata specification for an authentic Taiwan contextual scenario."""
    scenario_id: str
    domain: DomainCategory
    name_zh: str
    description_zh: str
    length_category: TextLengthCategory
    typical_pii_labels: List[str]
    context_keywords: List[str] = field(default_factory=list)
    persona_zh: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "domain": self.domain.value,
            "domain_zh": self.domain.display_name_zh,
            "name_zh": self.name_zh,
            "description_zh": self.description_zh,
            "length_category": self.length_category.value,
            "min_chars": self.length_category.min_chars,
            "max_chars": self.length_category.max_chars,
            "typical_pii_labels": self.typical_pii_labels,
            "context_keywords": self.context_keywords,
            "persona_zh": self.persona_zh,
        }


class ScenarioRegistry:
    """Registry of pre-configured authentic Taiwanese scenarios across domains and lengths."""

    _SCENARIOS: Dict[str, ScenarioDefinition] = {}

    @classmethod
    def register(cls, scenario: ScenarioDefinition) -> None:
        cls._SCENARIOS[scenario.scenario_id] = scenario

    @classmethod
    def get(cls, scenario_id: str) -> Optional[ScenarioDefinition]:
        return cls._SCENARIOS.get(scenario_id)

    @classmethod
    def list_all(cls) -> List[ScenarioDefinition]:
        return list(cls._SCENARIOS.values())

    @classmethod
    def list_by_domain(cls, domain: DomainCategory) -> List[ScenarioDefinition]:
        return [s for s in cls._SCENARIOS.values() if s.domain == domain]

    @classmethod
    def list_by_length(cls, length_cat: TextLengthCategory) -> List[ScenarioDefinition]:
        return [s for s in cls._SCENARIOS.values() if s.length_category == length_cat]

    @classmethod
    def filter(
        cls,
        domain: Optional[DomainCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
    ) -> List[ScenarioDefinition]:
        results = list(cls._SCENARIOS.values())
        if domain is not None:
            results = [s for s in results if s.domain == domain]
        if length_cat is not None:
            results = [s for s in results if s.length_category == length_cat]
        return results


# Pre-register authentic Taiwan domain scenarios across all 6 domains and 3 length scales
_DEFAULT_SCENARIOS: List[ScenarioDefinition] = [
    # ---------------- 1. HEALTHCARE ----------------
    ScenarioDefinition(
        scenario_id="health_sms_reminder",
        domain=DomainCategory.HEALTHCARE,
        name_zh="門診預約與檢查簡訊提醒",
        description_zh="醫院或診所寄發之門診看診通知簡訊，包含病患姓名、門診時間、看診醫師與診號。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["person", "phone_number", "date_of_birth"],
        context_keywords=["門診", "看診號", "診所", "掛號", "報到", "請攜帶健保卡"],
        persona_zh="醫院自動簡訊系統",
    ),
    ScenarioDefinition(
        scenario_id="health_line_consultation",
        domain=DomainCategory.HEALTHCARE,
        name_zh="診所官方 LINE 預約與症狀諮詢對話",
        description_zh="病患透過診所 LINE 官方帳號詢問門診時段、提供身分證號與生日進行初診掛號核對。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "national_id_number", "date_of_birth", "phone_number", "tw_line_id", "address"],
        context_keywords=["初診", "健保身分", "身分證號", "掛號", "診所小編", "預約時段", "藥物過敏"],
        persona_zh="診所櫃台行政人員與初診病患",
    ),
    ScenarioDefinition(
        scenario_id="health_discharge_summary",
        domain=DomainCategory.HEALTHCARE,
        name_zh="綜合醫院出院病歷摘要與用藥處方箋",
        description_zh="包含主訴、病史、理學檢查、手術處置、出院醫囑、醫師簽章證照字號及完整病患個人資訊。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "tw_nhi_card", "date_of_birth", "address", "phone_number", "tw_medical_license"],
        context_keywords=["病歷號", "出院摘要", "主治醫師", "主訴", "健保申報", "過敏史", "醫事證書", "醫令代碼"],
        persona_zh="綜合醫院專科主治醫師與病歷管理室",
    ),

    # ---------------- 2. BANKING & FINANCE ----------------
    ScenarioDefinition(
        scenario_id="bank_sms_otp_alert",
        domain=DomainCategory.BANKING_FINANCE,
        name_zh="信用卡消費刷卡通知與網銀 OTP 驗證簡訊",
        description_zh="銀行寄送之信用卡即時消費通知或網路銀行動態交易認證碼（OTP）簡訊。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["payment_card", "secret", "phone_number"],
        context_keywords=["刷卡通知", "動態密碼", "OTP", "末四碼", "授權碼", "玉山銀行", "台新銀行"],
        persona_zh="銀行自動推播防偽系統",
    ),
    ScenarioDefinition(
        scenario_id="bank_dispute_email",
        domain=DomainCategory.BANKING_FINANCE,
        name_zh="信用卡爭議帳款申訴與非本人交易聲明書",
        description_zh="持卡人發現未授權海外交易，致電或電郵客服申報爭議款項，填寫卡號、身分證與退款帳號。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "national_id_number", "payment_card", "bank_account", "phone_number", "email", "card_cvv"],
        context_keywords=["爭議款", "列爭議款", "盜刷", "非本人交易", "卡號", "客服中心", "帳單地址"],
        persona_zh="焦急的持卡人與信用卡部客服專員",
    ),
    ScenarioDefinition(
        scenario_id="bank_loan_credit_assessment",
        domain=DomainCategory.BANKING_FINANCE,
        name_zh="個人房屋抵押借款契約與徵信審核報告",
        description_zh="銀行個人房貸合約，詳載借款人、連帶保證人全名、身分證、戶籍地址、撥款帳號、統編與撥貸條款。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "address", "bank_account", "tax_id", "phone_number", "date_of_birth"],
        context_keywords=["借款人", "連帶保證人", "對保", "徵信報告", "撥貸帳戶", "抵押權設定", "不動產標示", "聯徵中心"],
        persona_zh="分行放款部經理與代書公證人",
    ),

    # ---------------- 3. TELECOM ----------------
    ScenarioDefinition(
        scenario_id="telecom_bill_due_sms",
        domain=DomainCategory.TELECOM,
        name_zh="電信資費帳單到期繳費提醒簡訊",
        description_zh="電信業者提醒用戶 5G 門號本期電信費用已出帳及繳費期限。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["phone_number", "person"],
        context_keywords=["電信帳單", "繳費期限", "中華電信", "台灣大哥大", "遠傳電信", "超商代碼"],
        persona_zh="電信營運商帳務通知系統",
    ),
    ScenarioDefinition(
        scenario_id="telecom_line_plan_change",
        domain=DomainCategory.TELECOM,
        name_zh="電信客服對話：攜碼續約與 SIM 卡遺失補發",
        description_zh="用戶透過線上文字客服申請掛失手機與補發晶片卡，核對雙證件號碼、戶籍地址與聯絡手機。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "national_id_number", "phone_number", "address", "date_of_birth", "email"],
        context_keywords=["雙證件", "攜碼", "SIM 卡補發", "資費專案", "掛失停話", "直營門市", "戶籍地"],
        persona_zh="電信直營線上專員與申辦用戶",
    ),
    ScenarioDefinition(
        scenario_id="telecom_broadband_contract",
        domain=DomainCategory.TELECOM,
        name_zh="光纖寬頻網路服務契約與裝機工程工單",
        description_zh="住宅光纖上網安裝合約，記載申請人身分證號、裝機地址、戶籍地址、自動扣款銀行帳號與派工紀錄。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "phone_number", "address", "bank_account", "email", "tax_id"],
        context_keywords=["裝機地址", "光纖電路", "Wi-Fi 分享器", "自動轉帳授權", "合約期限", "違約金", "派工單"],
        persona_zh="網路維運外包工程師與業務核印人員",
    ),

    # ---------------- 4. ECOMMERCE & LOGISTICS ----------------
    ScenarioDefinition(
        scenario_id="ecom_delivery_pickup_sms",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        name_zh="超商包裹貨到門市取件簡訊",
        description_zh="蝦皮或網購訂單已送達指定 7-11 / 全家超商門市，提醒攜帶證件取件。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["person", "phone_number"],
        context_keywords=["包裹已配達", "取件代碼", "7-ELEVEN", "全家便利商店", "身分證件", "蝦皮購物"],
        persona_zh="物流配送中心通知機器人",
    ),
    ScenarioDefinition(
        scenario_id="ecom_shopee_return_chat",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        name_zh="蝦皮拍賣買賣家聊聊退換貨與補寄爭議",
        description_zh="買家收受瑕疵商品，於聊聊對話提供真實姓名、收件超商門市、宅配住址、LINE ID 與退款帳號。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "phone_number", "address", "bank_account", "tw_line_id", "email"],
        context_keywords=["聊聊", "開箱錄影", "寄回地址", "賣家同意退貨", "黑貓收件", "退款帳戶", "店到店"],
        persona_zh="買家與賣家客服小編",
    ),
    ScenarioDefinition(
        scenario_id="ecom_crossborder_logistics_manifest",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        name_zh="跨境電商報關委任單與進口快遞分提單",
        description_zh="海外直郵進口報關清冊，詳列收件人身分證號、EZ WAY 實名認證號、通訊地址、電話與統編發票抬頭。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "phone_number", "address", "tax_id", "email", "postal_code"],
        context_keywords=["海關申報", "EZ WAY", "進口快遞", "分提單號", "委任書", "關稅代繳", "個資授權同意"],
        persona_zh="報關行專員與財政部關務署查驗員",
    ),

    # ---------------- 5. REAL ESTATE ----------------
    ScenarioDefinition(
        scenario_id="realestate_deposit_receipt",
        domain=DomainCategory.REAL_ESTATE,
        name_zh="看屋保留定金與押金簽收單",
        description_zh="房東或房仲出具之斡旋定金簡要收據，記載房東與房客姓名、聯絡手機與承租地址。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["person", "phone_number", "address"],
        context_keywords=["定金收據", "簽約保留", "押金", "房東簽收", "承租人"],
        persona_zh="獨立房東與承租房客",
    ),
    ScenarioDefinition(
        scenario_id="realestate_repair_and_transfer_line",
        domain=DomainCategory.REAL_ESTATE,
        name_zh="房東與租客 LINE 對話：修繕報修與租金匯款水單",
        description_zh="租客通報冷氣漏水並傳送租金匯款憑證，包含房東匯款銀行帳號、租客電話、LINE ID 與戶籍地資料。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "bank_account", "phone_number", "address", "tw_line_id", "email"],
        context_keywords=["房東先生", "水電師傅", "冷氣滴水", "房租已匯入", "帳號末五碼", "轉帳截圖", "簽收點交"],
        persona_zh="北漂租屋上班族與文山區房東",
    ),
    ScenarioDefinition(
        scenario_id="realestate_residential_lease_agreement",
        domain=DomainCategory.REAL_ESTATE,
        name_zh="內政部定型化住宅房屋租賃契約書",
        description_zh="標準租賃合約書完整條文，詳列出租人與承租人之姓名、身分證字號、戶籍地、通訊地、緊急聯絡人與公證條款。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "address", "phone_number", "bank_account", "tw_household_no", "date_of_birth"],
        context_keywords=["出租人（甲方）", "承租人（乙方）", "租賃標的物", "押金二個月", "戶籍地址", "連帶保證人", "內政部版合約", "公證人"],
        persona_zh="民間公證人事務所與簽約雙方",
    ),

    # ---------------- 6. LEGAL CONSULTATION ----------------
    ScenarioDefinition(
        scenario_id="legal_settlement_sms",
        domain=DomainCategory.LEGAL_CONSULTATION,
        name_zh="車禍和解賠償金入帳照會簡訊",
        description_zh="車禍當事人接獲之和解賠償金匯款入帳與結案提醒簡訊。",
        length_category=TextLengthCategory.SHORT,
        typical_pii_labels=["person", "bank_account", "license_plate"],
        context_keywords=["民事和解", "賠償款", "車號", "匯入完成", "撤回告訴"],
        persona_zh="調解委員會通訊系統",
    ),
    ScenarioDefinition(
        scenario_id="legal_mediation_dialogue",
        domain=DomainCategory.LEGAL_CONSULTATION,
        name_zh="鄉鎮市調解委員會車禍肇責協議紀錄",
        description_zh="兩造當事人於調解委員會陳述車禍經過，核對駕駛車牌、身分證號、駕照號碼與強制險理賠帳號。",
        length_category=TextLengthCategory.MID,
        typical_pii_labels=["person", "national_id_number", "license_plate", "drivers_license_number", "phone_number", "bank_account", "address"],
        context_keywords=["調解委員", "初判表", "路口碰撞", "肇事責任", "行車執照", "身分證號", "車險理賠"],
        persona_zh="調解委員、聲請人與對造人",
    ),
    ScenarioDefinition(
        scenario_id="legal_certified_notice_and_retainer",
        domain=DomainCategory.LEGAL_CONSULTATION,
        name_zh="郵局正式存證信函草稿與民事委任訴訟契約",
        description_zh="律師事務所受委任寄發之存證信函，詳列受託律師證號、寄件人與相對人姓名、身分證字號、公司統編與戶籍地址。",
        length_category=TextLengthCategory.LONG,
        typical_pii_labels=["person", "national_id_number", "tax_id", "address", "phone_number", "bank_account", "postal_code", "tw_medical_license"],
        context_keywords=["存證信函", "寄件人", "收件人", "台照", "限期清償", "委任律師", "訴訟代理人", "管轄法院"],
        persona_zh="主持律師與當事人",
    ),
]

# Initialize registry with default scenarios
for _sc in _DEFAULT_SCENARIOS:
    ScenarioRegistry.register(_sc)
