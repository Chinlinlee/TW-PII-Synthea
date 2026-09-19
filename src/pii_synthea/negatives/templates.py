"""
Hard Negative Context Templates & Templates Library (Ticket 05).
Provides pure negative templates (100% negative context, producing zero spans)
and mixed templates (authentic PII coexisting with hard negative distractors,
ensuring exact span preservation for true PII while excluding distractors).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pii_synthea.negatives.catalog import HardNegativeCategory
from pii_synthea.scenarios.domains import TextLengthCategory


@dataclass(frozen=True)
class PureNegativeTemplate:
    """Template designed to produce zero PII spans with authentic negative distractors."""
    template_id: str
    category: HardNegativeCategory
    length_category: TextLengthCategory
    template_text: str
    description: str


@dataclass(frozen=True)
class MixedNegativeTemplate:
    """
    Template containing both genuine PII placeholders (<label> or {{label}})
    and hard negative placeholders ({neg_entity}), ensuring only genuine PII
    is labeled while negative distractors remain unannotated.
    """
    template_id: str
    category: HardNegativeCategory
    length_category: TextLengthCategory
    template_text: str
    description: str


class HardNegativeTemplateLibrary:
    """Curated collection of pure and mixed hard negative templates for Taiwan."""

    _PURE_TEMPLATES: List[PureNegativeTemplate] = [
        # --- BRAND_PERSON_NAME (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_brand_short_1",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.SHORT,
            template_text="今天中午我們全組叫了{brand}的外送便當，大家都覺得炸雞腿和招牌排骨飯非常入味。",
            description="同事聚餐叫外送短訊，含人名品牌",
        ),
        PureNegativeTemplate(
            template_id="pure_brand_short_2",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.SHORT,
            template_text="下班經過夜市順道去吃{brand}，排隊人潮很多，但出餐速度非常有效率。",
            description="夜市小吃用餐感想，含品牌名",
        ),
        PureNegativeTemplate(
            template_id="pure_brand_mid_1",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.MID,
            template_text=(
                "各位夥伴好，本週五部門聚餐地點已經確認選在{brand}。"
                "店家表示用餐時間為兩小時，已為我們保留大桌包廂。"
                "現場提供多道招牌台菜與精緻合菜，如有吃素或特殊飲食過敏需求，請提前於群組回覆登記。"
                "感謝大家配合，期待當天準時集合歡聚！"
            ),
            description="部門聚餐通知信件，含台菜名店",
        ),
        PureNegativeTemplate(
            template_id="pure_brand_long_1",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.LONG,
            template_text=(
                "【台灣老字號餐飲品牌專訪：漫談經營哲學與傳承】\n\n"
                "走進台灣歷史悠久的街頭巷弄，{brand}一直是在地饕客心中難以忘懷的經典風味。"
                "創辦初期從一輛簡陋的手推木頭攤車起家，堅持每日清晨天未亮便前往果菜市場挑選最新鮮的在地食材，"
                "憑藉著純手工調配的秘傳醬汁與嚴謹火候掌控，歷經數十年風雨洗禮，逐步擴展至今日家喻戶曉的連鎖規模。\n\n"
                "在經營策略上，品牌第二代負責人引進現代化中央廚房與食品安全HACCP認證體系，"
                "不僅嚴格把關進貨檢驗與保存溫度，更保留傳統古法烹調精隨，讓每一位上門的顧客都能品嚐到記憶中最純粹的家鄉風味。"
                "面對國際原物料價格上漲與餐飲市場激烈的競爭挑戰，{brand}始終堅持薄利多銷、回饋鄰里鄉親的創業初心。\n\n"
                "未來，該品牌更積極規劃進軍海外市場與跨境生鮮冷鏈電商，將道地台灣傳統飲食文化與溫暖人情味推向國際舞台，"
                "樹立本土中小企業穩健經營與文化傳承的成功典範。"
            ),
            description="餐飲美食深度專訪長文，無任何個人個資",
        ),

        # --- PUBLIC_HISTORICAL_FIGURE (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_hist_short_1",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            length_category=TextLengthCategory.SHORT,
            template_text="公車目前行駛在{public_figure}上，正逢下班尖峰時段，沿途車流量較大請乘客耐心等候。",
            description="公車行車動態廣播，含偉人命名路段",
        ),
        PureNegativeTemplate(
            template_id="pure_hist_mid_1",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            length_category=TextLengthCategory.MID,
            template_text=(
                "週末文化特展導覽公告：\n"
                "本週六上午十點，市府文化局將於{public_figure}舉辦近代台灣歷史文獻專題研討會。"
                "會中將展示珍貴的手稿檔案、早期黑白影像與近代開拓史料，邀請多位歷史學系教授出席講評。"
                "活動全程免費開放入場，歡迎對台灣歷史文化有興趣之市民朋友踴躍前往參觀交流。"
            ),
            description="歷史文獻特展活動快訊",
        ),

        # --- PUBLIC_LANDMARK_ADDRESS (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_landmark_short_1",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            length_category=TextLengthCategory.SHORT,
            template_text="外賓參訪團一行人預計於今日下午兩點抵達{landmark}進行參觀與官方合影留念。",
            description="官方外賓參訪動態，含知名公有地標",
        ),
        PureNegativeTemplate(
            template_id="pure_landmark_mid_1",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【市政觀光旅遊指南】\n"
                "搭乘台北捷運信義線或板南線，即可輕鬆造訪位於市中心的{landmark}。"
                "該場館周邊規劃有完善的無障礙步道與綠意盎然的景觀公園，每逢週末更常態性舉辦文創市集與戶外街頭藝人表演。"
                "館內各展廳全年無休對外開放，是國內外遊客感受都會建築美學與人文氣息的必遊景點。"
            ),
            description="捷運觀光文旅導覽，含公有地標地址",
        ),

        # --- PUBLIC_HOTLINE (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_hotline_short_1",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            length_category=TextLengthCategory.SHORT,
            template_text="若民眾接獲疑似詐騙可疑來電或陌生簡訊，請立即撥打{hotline}向專業人員求證諮詢。",
            description="防詐騙宣導快訊，含公用專線",
        ),
        PureNegativeTemplate(
            template_id="pure_hotline_mid_1",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【緊急市政與民生服務專線通報提醒】\n"
                "颱風季節來臨，請市民加強居家防颱措施。"
                "若發現路樹倒塌、路燈故障或道路積淹水災情，可隨時撥打{hotline}由專責話務中心為您派案處理。"
                "如遇人身安全立即危險或火災突發狀況，請務必改撥110或119報案，以爭取黃金搶救時間。"
            ),
            description="市政防汛宣導通知，含多個公用專線",
        ),

        # --- PUBLIC_EMAIL (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_email_short_1",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            length_category=TextLengthCategory.SHORT,
            template_text="各界對本次公開採購招標規範如有疑義，請逕寄電子郵件至{public_email}洽詢承辦單位。",
            description="公部門採購招標釋疑公告",
        ),
        PureNegativeTemplate(
            template_id="pure_email_mid_1",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【政府公開資訊與民眾意見反映管道】\n"
                "為提升公務行政透明度與公共服務滿意度，數位治理委員會已建立全天候民意反映信箱。"
                "民眾可將法規建言、施政反饋或檢舉資料直接發送至{public_email}，系統將自動分派至各權責局處。"
                "標準案件將於收到信件後三個工作日內給予正式書面回覆，感謝各位公民的共同參與。"
            ),
            description="政府公開數位服務管道公告",
        ),

        # --- OFFICIAL_CODE_NUMBER (SHORT, MID, LONG) ---
        PureNegativeTemplate(
            template_id="pure_code_short_1",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            length_category=TextLengthCategory.SHORT,
            template_text="本筆交易已開立雲端電子發票，字軌號碼為{code_number}，中獎獎金將自動匯入共通性載具。",
            description="超商/網購發票開立通知",
        ),
        PureNegativeTemplate(
            template_id="pure_code_mid_1",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【國際快遞與包裹清關即時貨態追蹤】\n"
                "您的跨境海運進口貨件目前已順利抵達台北港集散中心，海關申報貨況狀態正常。"
                "包裹託運單號為{code_number}，預計於完成海關抽檢作業後交由國內物流車隊派送。"
                "如需查詢即時配送進度，請隨時使用官方物流App輸入追蹤編號查詢最新里程碑。"
            ),
            description="快遞物流追蹤訊息，含非身分證的條碼序號",
        ),
    ]

    _MIXED_TEMPLATES: List[MixedNegativeTemplate] = [
        # --- BRAND_PERSON_NAME with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_brand_1",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.SHORT,
            template_text="訂單確認：顧客 <person:1> 先生您好，您在 {neg_entity} 訂購的餐點已出餐，外送地址為 <address:1>。",
            description="外送餐點確認單，包含人名品牌店名與真實顧客個資",
        ),
        MixedNegativeTemplate(
            template_id="mixed_brand_2",
            category=HardNegativeCategory.BRAND_PERSON_NAME,
            length_category=TextLengthCategory.MID,
            template_text=(
                "外送外帶訂單收據：\n"
                "親愛的顧客 <person:1> 您好！感謝您今日於 {neg_entity} 訂購餐點。\n"
                "外送聯絡電話為 <phone_number:1>，送達指定地點：<address:1>。\n"
                "本次消費款項已透過信用卡 <credit_card:1> 完成線上扣款，統一發票將發送至會員郵箱 <email:1>。"
            ),
            description="餐飲訂購明細，含人名品牌與電話、地址、信用卡、Email",
        ),

        # --- PUBLIC_HISTORICAL_FIGURE with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_hist_1",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            length_category=TextLengthCategory.SHORT,
            template_text="業務員 <person:1> 於 {neg_entity} 附近拜訪客戶，聯絡手機為 <phone_number:1>。",
            description="業務拜訪簡報，偉人路名與真實業務手機姓名",
        ),
        MixedNegativeTemplate(
            template_id="mixed_hist_2",
            category=HardNegativeCategory.PUBLIC_HISTORICAL_FIGURE,
            length_category=TextLengthCategory.MID,
            template_text=(
                "房屋租賃媒合看屋約定：\n"
                "租屋仲介 <person:1> 先生（聯絡電話：<phone_number:1>）已與房客確認於明日上午於 {neg_entity} 入口處碰面。\n"
                "本次帶看之獨立套房位於 <address:1>，請房客準時抵達。\n"
                "簽約時請攜帶身分證件以利核對承租人資格，保障雙方交易安全。"
            ),
            description="租屋看屋通知，含公有路名園區與仲介真實電話姓名",
        ),

        # --- PUBLIC_LANDMARK_ADDRESS with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_landmark_1",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            length_category=TextLengthCategory.SHORT,
            template_text="計程車派遣通知：司機已接單，乘客 <person:1> 請前往 {neg_entity} 前方避車彎候車。",
            description="叫車派車訊息，公有地標與真實乘客姓名",
        ),
        MixedNegativeTemplate(
            template_id="mixed_landmark_2",
            category=HardNegativeCategory.PUBLIC_LANDMARK_ADDRESS,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【商務會展貴賓接送派車單】\n"
                "接送司機：<person:1>，聯絡手機：<phone_number:1>，車牌號碼：<license_plate:1>。\n"
                "上車集合地點：{neg_entity}。\n"
                "最終送達私人住所地址：<address:1>。\n"
                "貴賓若行程有變更，請直接聯絡司機或致電主辦窗口。"
            ),
            description="商務接送，公有地標與真實司機電話、車牌、私人地址",
        ),

        # --- PUBLIC_HOTLINE with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_hotline_1",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            length_category=TextLengthCategory.SHORT,
            template_text="客服專員 <person:1> 提醒您：若遇緊急詐騙請速撥 {neg_entity}，或電洽私人手機 <phone_number:1>。",
            description="反詐宣導簡訊，含公用165與專員私人手機",
        ),
        MixedNegativeTemplate(
            template_id="mixed_hotline_2",
            category=HardNegativeCategory.PUBLIC_HOTLINE,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【市政民眾陳情案件立案確認函】\n"
                "陳情人姓名：<person:1>，身分證統一編號：<national_id_number:1>。\n"
                "通訊地址：<address:1>，聯絡電話：<phone_number:1>。\n"
                "本案已依您來電市民專線 {neg_entity} 登記之內容立案，權責單位派工處理中。\n"
                "案件處理進度查詢密碼將以簡訊發送至您的手機。"
            ),
            description="市政陳情案件回執，含真實市民全套個資與1999專線",
        ),

        # --- PUBLIC_EMAIL with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_email_1",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            length_category=TextLengthCategory.SHORT,
            template_text="申請人 <person:1> 補件資料已由專用信箱 <email:1> 轉發至機關通用信箱 {neg_entity}。",
            description="公文送件通知，私人信箱與公部門信箱混用",
        ),
        MixedNegativeTemplate(
            template_id="mixed_email_2",
            category=HardNegativeCategory.PUBLIC_EMAIL,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【大專院校新生入學註冊審查通知】\n"
                "錄取學生姓名：<person:1>，身分證字號：<national_id_number:1>。\n"
                "個人聯絡信箱：<email:1>，緊急聯絡電話：<phone_number:1>。\n"
                "請於規定期限內將畢業證書正本寄送至教務處招生組公開信箱：{neg_entity}。\n"
                "逾期未繳交者將視同放棄錄取資格。"
            ),
            description="大學註冊通知，含學生全套個資與學校招生公開信箱",
        ),

        # --- OFFICIAL_CODE_NUMBER with Real PII ---
        MixedNegativeTemplate(
            template_id="mixed_code_1",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            length_category=TextLengthCategory.SHORT,
            template_text="受款人 <person:1> 先生，發票號碼 {neg_entity} 之請款金額已匯入帳戶 <bank_account:1>。",
            description="發票報銷匯款通知，含發票號與真實個人帳戶",
        ),
        MixedNegativeTemplate(
            template_id="mixed_code_2",
            category=HardNegativeCategory.OFFICIAL_CODE_NUMBER,
            length_category=TextLengthCategory.MID,
            template_text=(
                "【健保特約醫療院所門診掛號證明】\n"
                "就醫病患：<person:1>，健保卡卡號：<tw_nhi_card:1>，身分證號：<national_id_number:1>。\n"
                "當日就診序號：{neg_entity}。\n"
                "病患通訊地址：<address:1>，手機：<phone_number:1>。\n"
                "看診時請出示實體健保卡，依燈號依序進入診間看診。"
            ),
            description="門診掛號單，含真實健保卡身分證與門診叫號序號",
        ),
    ]

    @classmethod
    def all_pure_templates(cls) -> List[PureNegativeTemplate]:
        return list(cls._PURE_TEMPLATES)

    @classmethod
    def all_mixed_templates(cls) -> List[MixedNegativeTemplate]:
        return list(cls._MIXED_TEMPLATES)

    @classmethod
    def get_pure(
        cls,
        category: Optional[HardNegativeCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
    ) -> List[PureNegativeTemplate]:
        res = cls._PURE_TEMPLATES
        if category:
            res = [t for t in res if t.category == category]
        if length_cat:
            res = [t for t in res if t.length_category == length_cat]
        return res

    @classmethod
    def get_mixed(
        cls,
        category: Optional[HardNegativeCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
    ) -> List[MixedNegativeTemplate]:
        res = cls._MIXED_TEMPLATES
        if category:
            res = [t for t in res if t.category == category]
        if length_cat:
            res = [t for t in res if t.length_category == length_cat]
        return res
