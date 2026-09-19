"""
Seed Template Library for Taiwan PII Synthetic Generation.
Provides an authentic, localized collection of templates across 6 domains
and 3 length scales (short, mid, long) for offline, deterministic synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pii_synthea.scenarios.domains import DomainCategory, TextLengthCategory


@dataclass(frozen=True)
class SeedTemplate:
    """A pre-configured template with domain, length category, and tags."""
    template_id: str
    domain: DomainCategory
    length_category: TextLengthCategory
    name_zh: str
    template_text: str


class SeedTemplateLibrary:
    """Registry and provider of localized Taiwanese seed templates."""

    _TEMPLATES: Dict[str, SeedTemplate] = {}

    @classmethod
    def register(cls, template: SeedTemplate) -> None:
        cls._TEMPLATES[template.template_id] = template

    @classmethod
    def get(cls, template_id: str) -> Optional[SeedTemplate]:
        return cls._TEMPLATES.get(template_id)

    @classmethod
    def list_all(cls) -> List[SeedTemplate]:
        return list(cls._TEMPLATES.values())

    @classmethod
    def list_by_domain(cls, domain: DomainCategory) -> List[SeedTemplate]:
        return [t for t in cls._TEMPLATES.values() if t.domain == domain]

    @classmethod
    def list_by_length(cls, length_cat: TextLengthCategory) -> List[SeedTemplate]:
        return [t for t in cls._TEMPLATES.values() if t.length_category == length_cat]

    @classmethod
    def filter(
        cls,
        domain: Optional[DomainCategory] = None,
        length_cat: Optional[TextLengthCategory] = None,
    ) -> List[SeedTemplate]:
        results = list(cls._TEMPLATES.values())
        if domain is not None:
            results = [t for t in results if t.domain == domain]
        if length_cat is not None:
            results = [t for t in results if t.length_category == length_cat]
        return results


# ---------------- 1. SHORT TEMPLATES (15-120 chars) ----------------

_SHORT_TEMPLATES = [
    SeedTemplate(
        template_id="short_health_sms",
        domain=DomainCategory.HEALTHCARE,
        length_category=TextLengthCategory.SHORT,
        name_zh="門診預約看診提醒簡訊",
        template_text="【台北慈濟醫院】提醒您：<person:1>病患門診預約已完成，請於預定看診時間攜帶健保IC卡至2樓家醫科3診報到，聯絡手機：<phone_number:1>。",
    ),
    SeedTemplate(
        template_id="short_bank_otp",
        domain=DomainCategory.BANKING_FINANCE,
        length_category=TextLengthCategory.SHORT,
        name_zh="網銀交易驗證碼簡訊",
        template_text="【國泰世華】您正在執行轉帳作業，動態驗證碼為：<secret:1>，本驗證碼3分鐘內有效。若非您本人操作請速撥客服專線。",
    ),
    SeedTemplate(
        template_id="short_bank_card_alert",
        domain=DomainCategory.BANKING_FINANCE,
        length_category=TextLengthCategory.SHORT,
        name_zh="信用卡即時消費通知",
        template_text="【玉山銀行】親愛的卡友<person:1>您好，您末四碼為<payment_card:1>的信用卡於今日刷卡消費NT$3,680元，感謝您的惠顧。",
    ),
    SeedTemplate(
        template_id="short_telecom_bill",
        domain=DomainCategory.TELECOM,
        length_category=TextLengthCategory.SHORT,
        name_zh="電信帳單到期通知",
        template_text="【中華電信通知】用戶<person:1>您好，您的5G門號<phone_number:1>本期電信資費帳單共計999元，繳費期限至本月底止，敬請留意。",
    ),
    SeedTemplate(
        template_id="short_ecom_pickup",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        length_category=TextLengthCategory.SHORT,
        name_zh="超商包裹到店簡訊",
        template_text="【7-ELEVEN 取件通知】<person:1>您好，您在蝦皮購物的包裹已配達鑫興門市，請攜帶身分證件並出示取貨條碼於7日內取件。",
    ),
    SeedTemplate(
        template_id="short_realestate_deposit",
        domain=DomainCategory.REAL_ESTATE,
        length_category=TextLengthCategory.SHORT,
        name_zh="看屋定金簽收單",
        template_text="茲收到承租人<person:1>先生交付之房屋租賃定金新台幣伍仟元整，保留承租位於<address:1>之住宅，特立此據。",
    ),
    SeedTemplate(
        template_id="short_legal_settlement_sms",
        domain=DomainCategory.LEGAL_CONSULTATION,
        length_category=TextLengthCategory.SHORT,
        name_zh="車禍和解賠償金入帳照會",
        template_text="【和解照會】有關車號<license_plate:1>碰撞事故，賠償金已匯入受害人<person:1>指定之帳戶，雙方民事爭議就此圓滿結案。",
    ),
]

# ---------------- 2. MID TEMPLATES (200-1000 chars) ----------------

_MID_TEMPLATES = [
    SeedTemplate(
        template_id="mid_health_line_registration",
        domain=DomainCategory.HEALTHCARE,
        length_category=TextLengthCategory.MID,
        name_zh="診所官方 LINE 門診掛號對話",
        template_text="""診所小編：您好！這裡是新竹安慎聯合診所官方 LINE，很高興為您服務。初次看診請先提供基本資料進行掛號建立喔！
病患：您好，我想預約這週五晚上心臟內科門診，我是第一次看診。
診所小編：好的，沒問題！請依序提供您的：1.真實姓名 2.身分證字號 3.民國出生年月日 4.聯絡電話 5.現居地址。
病患：好的！我姓名是 <person:1>，身分證字號是 <national_id_number:1>，出生日期是民國 <date_of_birth:1>，手機號碼是 <phone_number:1>，地址在 <address:1>，我的電子郵件是 <email:1>。
診所小編：收到！已為您完成建檔，您的門診預約代碼為 28 號，請於週五晚間 19:30 前攜帶健保 IC 卡至櫃檯報到繳費（健保掛號費 200 元）。如果有慢性病用藥史或過敏體質，請在看診時告知醫師喔！
病患：好的，謝謝小編！週五見。""",
    ),
    SeedTemplate(
        template_id="mid_bank_dispute_complaint",
        domain=DomainCategory.BANKING_FINANCE,
        length_category=TextLengthCategory.MID,
        name_zh="信用卡海外爭議款申訴電郵",
        template_text="""主旨：【爭議帳款申訴】信用卡未授權海外刷卡通報與扣款爭議申請
寄件人：<person:1> <<email:1>>
收件人：富邦銀行信用卡風控中心 <service@fubon.com>

富邦銀行信用卡客服中心您好：
本人 <person:1>（身分證字號：<national_id_number:1>，聯絡手機：<phone_number:1>）為貴行信用卡持卡人。
今早收到手機簡訊，通知本人持有之富邦尊御卡（卡號：<payment_card:1>，背面末三碼 CVV：<card_cvv:1>）於今日凌晨發生一筆海外線上美元交易（折合新台幣 28,450 元），消費商戶為海外遊戲平台。

本人當時正於家中就寢，該筆交易絕非本人或家屬授權進行，顯屬偽冒盜刷。懇請貴行立即協助：
1. 針對該張卡片進行緊急停卡處置並補發新卡至通訊地址：<address:1>。
2. 將該筆 28,450 元之款項列入「爭議款項」，暫停計收利息與費用。
3. 若需填寫「聲明書」或檢附報案三聯單，請將相關表格寄至本人電子信箱。若有退款需要，本人於貴行之活儲扣款帳戶為：<bank_account:1>。

請儘速來電或回信照會，感謝您的專業協助！
申訴人：<person:1> 敬上""",
    ),
    SeedTemplate(
        template_id="mid_telecom_service_dialogue",
        domain=DomainCategory.TELECOM,
        length_category=TextLengthCategory.MID,
        name_zh="電信線上文字客服資費變更與補卡對話",
        template_text="""客服專員 8042：您好，很高興為您服務！這裡是台灣大哥大網路客服，請問今天需要協助申辦什麼業務呢？
用戶：你好，我上週手機在捷運站掉了，剛剛買了新手機，想申請補發 eSIM 並且順便續約 5G 吃到飽專案。
客服專員 8042：好的，非常樂意為您辦理！由於補發晶片與合約變更涉及門號個資隱私，稍後需要跟您核對門號雙證件基本資料喔。請問遺失的門號是哪一支呢？
用戶：門號是 <phone_number:1>，登記在我的名字底下。
客服專員 8042：收到！請提供申請人全名、身分證字號、戶籍地址及出生年月日，謝謝您。
用戶：我是 <person:1>，身分證字號 <national_id_number:1>，生日是民國 <date_of_birth:1>，戶籍地址是 <address:1>。
客服專員 8042：資料核對正確，謝謝您！另外請提供您的常用電子信箱，稍後我會將電子身分驗證連結發送給您：
用戶：我的信箱是 <email:1>，麻煩了。
客服專員 8042：已發送驗證碼！驗證完成後，我們將在 10 分鐘內為您開通 eSIM QR Code，祝您使用順心！""",
    ),
    SeedTemplate(
        template_id="mid_ecom_shopee_return_chat",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        length_category=TextLengthCategory.MID,
        name_zh="蝦皮拍賣聊聊瑕疵商品退換貨對話",
        template_text="""買家：賣家您好，我收到昨天在您賣場購買的藍牙耳機了，但是左耳完全無法充入電量，開箱全程都有錄影存證。
賣家客服：買家您好！非常不好意思造成您的困擾，瑕疵品我們絕對負責到底！請問您可以將開箱影片上傳到聊聊，或者加我們售後 LINE 傳送嗎？
買家：我有加你們的 LINE 了，我的 LINE ID 是 <tw_line_id:1>，影片已經傳過去了。
賣家客服：已經看到影片了，確認為原廠電池瑕疵。我們將安排黑貓宅急便到府取回瑕疵商品，並直接為您退款。請提供收件資訊與退款銀行帳戶：
買家：好的，收件人是 <person:1>，取件地址是 <address:1>，聯絡手機是 <phone_number:1>。
退款帳號請退到我國泰世華銀行的帳戶：<bank_account:1>。
賣家客服：收到，已為您安排明天下午黑貓收件，司機前往前會先以電話聯繫您。退款預計在司機收件後的 24 小時內匯入您的帳戶，非常感謝您的體諒與配合！""",
    ),
    SeedTemplate(
        template_id="mid_realestate_landlord_tenant_chat",
        domain=DomainCategory.REAL_ESTATE,
        length_category=TextLengthCategory.MID,
        name_zh="房東租客修繕與租金轉帳對話紀錄",
        template_text="""租客小林：房東張先生您好，不好意思打擾了！客廳的冷氣這兩天開始滴水，而且吹出來的風不太冷，想請您協助找水電師傅來看一下。
房東：小林你好！收到，我明天下午聯絡常合作的日立電器師傅過去檢修。到時候請師傅去前先打你電話。你的手機還是 <phone_number:1> 沒變吧？
租客小林：對的，電話沒變。另外，本月份的房租 18,000 元我剛剛已經網銀轉帳過去了喔！
房東：好的，我查一下網銀。請問你匯款的帳號末五碼是多少呢？
租客小林：我是用台新銀行轉出的，完整帳號是 <bank_account:1>，匯款人姓名顯示 <person:1>。
房東：收到款項了！沒問題。另外內政部租金補貼審查單位有發函到租屋地址 <address:1>，你有空記得去一樓信箱收件喔。
租客小林：太好了，謝謝房東提醒，我等等下班回租屋處就去拿信！水電師傅明天聯絡我也請加我的 LINE：<tw_line_id:1> 傳訊息方便。""",
    ),
    SeedTemplate(
        template_id="mid_legal_mediation_record",
        domain=DomainCategory.LEGAL_CONSULTATION,
        length_category=TextLengthCategory.MID,
        name_zh="車禍民事賠償調解委員會言詞陳述紀錄",
        template_text="""調解委員主持紀錄：
本會於今日上午 10 時召開車禍侵權民事損害賠償事件調解會議。
聲請人：<person:1>（身分證字號：<national_id_number:1>，駕照號碼：<drivers_license_number:1>，住址：<address:1>，聯絡電話：<phone_number:1>）。
對造人：<person:2>（身分證字號：<national_id_number:2>，聯絡電話：<phone_number:2>）。

案情摘要：
雙方於上月 15 日於交叉路口發生擦撞事故。聲請人騎乘普通重型機車（車牌號碼：<license_plate:1>），對造人駕駛自用小客車（車牌號碼：<license_plate:2>），經交通警察大隊初判表分析，對造人行經無號誌路口未依規定減速禮讓。
經本會委員協調，雙方達成共識：
對造人同意給付聲請人車輛維修費與醫療補償金共計新台幣 36,000 元整，並於 7 日內電匯至聲請人指定之兆豐銀行帳號：<bank_account:1>。
聲請人同意於款項全數收訖後，拋棄本件事故其餘民刑事請求權，雙方均無異議並簽名確認。""",
    ),
]

# ---------------- 3. LONG TEMPLATES (1500-5000 chars) ----------------

_LONG_TEMPLATES = [
    SeedTemplate(
        template_id="long_health_discharge_record",
        domain=DomainCategory.HEALTHCARE,
        length_category=TextLengthCategory.LONG,
        name_zh="長庚醫療財團法人綜合醫院出院病歷摘要與診斷證明",
        template_text="""長庚醫療財團法人林口長庚紀念醫院
出院病歷摘要與臨床治療紀錄單
病歷號碼：MRN-2024-8931289
就醫序號：00384912
全民健康保險申報代碼：0101140019

一、病患基本身分資料（Patient Demographics）
病患姓名：<person:1>
身分證統一編號：<national_id_number:1>
健保卡卡號：<tw_nhi_card:1>
出生年月日：民國 <date_of_birth:1>
性別：男 / 女
聯絡電話（手機）：<phone_number:1>
室內聯絡電話：<phone_number:2>
戶籍地址：<address:1>
現居通訊地址：<address:2>
郵遞區號：<postal_code:1>
緊急聯絡人：<person:2>（與病患關係：配偶，緊急聯絡手機：<phone_number:3>）
主治醫師：<person:3>（醫師證書字號：<tw_medical_license:1>）
住院日期：民國 113 年 08 月 12 日
出院日期：民國 113 年 08 月 20 日
住院總日數：8 日

二、入院診斷與主訴（Admission Diagnosis & Chief Complaint）
主訴（Chief Complaint）：
病患於入院前三天突發反覆右上腹劇烈絞痛，並伴隨發燒（最高體溫達 38.9 度）、噁心嘔吐及全身倦怠。
理學檢查顯示右上腹壓痛明顯，墨菲氏徵象（Murphy's sign）呈現陽性。
急診腹部超音波顯示膽囊壁顯著增厚（厚度達 4.8 mm），並合併多顆直徑約 0.8 至 1.5 cm 之膽結石，總膽管無明顯擴張。
抽血生化報告：WBC 16,800/uL，CRP 82.5 mg/L，GOT 45 U/L，GPT 52 U/L，Total Bilirubin 1.6 mg/dL。
入院診斷：急性結石性膽囊炎（Acute calculous cholecystitis, ICD-10: K80.00）。

三、住院手術與處置過程（Hospital Course & Procedures）
病患於入院後立即接受靜脈廣效性抗生素（Ceftriaxone + Metronidazole）治療與點滴水分補充。
於民國 113 年 08 月 14 日上午由主治醫師 <person:3> 於全身麻醉下施行「腹腔鏡膽囊切除術（Laparoscopic Cholecystectomy）」。
術中發現膽囊嚴重水腫並與大網膜廣泛沾黏，經小心鈍性及銳性剝離後，安全游離膽囊管及膽囊動脈，並使用鈦合金血管夾確實夾閉結紮後切斷。
手術過程順利，出血量約 30 mL，術後留置腹腔引流管一隻。
病理切片報告（S24-19284）：Acute and chronic cholecystitis with cholelithiasis, negative for malignancy。
術後第一日病患腸蠕動恢復，引流管引流液清澈且量少，於術後第二日順利拔除引流管，傷口癒合良好無紅腫熱痛，各項血液感染發炎指數均已降至正常範圍。

四、出院處方用藥明細（Discharge Medications）
1. Keflex (Cephalexin) 500mg/cap, 每日 4 次，每次 1 粒，飯後服用，共 5 日份。
2. Acetaminophen (Tinten) 500mg/tab, 每日 3 次，每次 1 錠，疼痛時服用。
3. Ultracet (Tramadol/Acetaminophen), 備用，劇烈疼痛時服用。
4. Gascon (Simethicone) 40mg/tab, 每日 3 次，每次 1 錠，飯後緩解腹脹。

五、出院醫囑與追蹤衛教事項（Discharge Instructions & Follow-up）
1. 請病患務必保持手術腹部微創傷口乾燥清潔，一週內勿行盆浴，傷口若有滲出液或發紅發燒請立即返院急診。
2. 飲食請採清淡低脂飲食，避免油炸、辛辣及過度油膩食物，以防脂肪吸收不良引發腹瀉。
3. 門診追蹤時間：已預約於民國 113 年 08 月 27 日上午 09:30 至林口長庚醫學大樓 3 樓一般外科門診 12 診，由主治醫師 <person:3> 門診複診並進行拆線。
4. 本病歷摘要及診斷證明書正本由本院病歷管理部用印核發，供病患申請商業醫療保險理賠與勞保傷病給付之用。

主治醫師簽章：<person:3>（醫字第：<tw_medical_license:1>）
病歷審查醫師：<person:4>
醫療機構地址：<address:3>
機構聯絡總機：<phone_number:4>
病歷管理專線分機：2108""",
    ),
    SeedTemplate(
        template_id="long_realestate_lease_contract",
        domain=DomainCategory.REAL_ESTATE,
        length_category=TextLengthCategory.LONG,
        name_zh="內政部定型化住宅房屋租賃契約書正式完整版",
        template_text="""住宅房屋租賃契約書（內政部公告標準定型化範本）

立契約書人：
出租人（以下簡稱甲方）：<person:1>
身分證統一編號：<national_id_number:1>
出生年月日：民國 <date_of_birth:1>
戶籍地址：<address:1>
通訊聯絡地址：<address:2>
聯絡電話（手機）：<phone_number:1>
電子郵件信箱：<email:1>

承租人（以下簡稱乙方）：<person:2>
身分證統一編號：<national_id_number:2>
出生年月日：民國 <date_of_birth:2>
戶籍地戶號：<tw_household_no:2>
戶籍地址：<address:3>
聯絡電話（手機）：<phone_number:2>
通訊 LINE ID：<tw_line_id:2>
電子郵件信箱：<email:2>

乙方之連帶保證人（以下簡稱丙方）：<person:3>
身分證統一編號：<national_id_number:3>
戶籍地址：<address:4>
聯絡電話：<phone_number:3>

茲就甲方將其合法管領之住宅房屋出租與乙方使用事宜，經雙方依法審閱本契約全部條款逾三日，合意簽署本契約以資共同信守：

第一條：租賃標的物現況與範圍
1. 房屋座落標示：<address:5>。
2. 租賃面積及範圍：權狀建物面積約 28.5 坪，含附屬建物、客廳、廚房、主臥室、客臥室及陽台，連同地下室編號 B1-42 號坡道平面停車位一平面車位。
3. 房屋使用用途：本房屋限定僅供乙方作為純住宅自住使用，未經甲方事前書面同意，乙方不得轉供營業、辦公、危險物品儲存或轉租他人。

第二條：租賃期間
1. 本租賃合約期限自民國 113 年 11 月 01 日起至民國 115 年 10 月 31 日止，共計兩年整。
2. 租期屆滿時，租賃關係即告消滅，甲方不另為通知。乙方若有意續約，應於租期屆滿前二個月以書面或通訊軟體向甲方提出協議。

第三條：租金約定與支付方式
1. 房屋每月租金為新台幣貳萬陸仟元整（NT$ 26,000 元）。
2. 乙方應於每月 5 日前，將當月租金無息全額電匯至甲方指定之金融機構帳戶：
   金融機構代碼：013（國泰世華商業銀行世貿分行）
   受款帳戶帳號：<bank_account:1>
   戶名：<person:1>
3. 租金不包含水費、電費、瓦斯費、大樓管委會每月管理費（新台幣 2,200 元整）及第四台網路費，上述雜支由乙方自行如期依單據繳納。

第四條：押租金（保證金）之收取與返還
1. 乙方應於簽訂本契約之同時，交付甲方相當於兩個月租金之押金，計新台幣伍萬貳仟元整（NT$ 52,000 元）。
2. 甲方收訖後立據簽收。押金於租期屆滿、租賃標的物依現況點交清空返還甲方，並扣除乙方未繳清之水電雜費、修繕損害賠償金後，由甲方無息全數退還至乙方指定帳戶：<bank_account:2>。

第五條：房屋附屬設備與修繕責任
1. 租賃物附屬設備包括：大金變頻冷暖空調三台、林內強制排氣瓦斯熱水器一台、櫻花雙口瓦斯爐、日立雙門電冰箱、客廳沙發茶几組。
2. 房屋本體結構、滲漏水及附屬設備於正常自然耗損折舊下之故障修繕，由甲方負責負擔修繕費用。但因乙方故意、過失或未盡善良管理人注意義務所致之毀損，由乙方自負修繕及賠償費用。

第六條：特別約定與管轄法院
1. 乙方於租賃期間嚴禁在屋內從事吸毒、賭博、聚眾喧嘩、開毒品派對或存放違禁品等不法行為。若有違反，甲方得立即終止契約，押金不予退還，並依法報警究辦。
2. 雙方因本契約涉訟時，合意以臺灣臺北地方法院為第一審管轄法院。

本契約書壹式貳份，由甲、乙、丙三方各執乙份為憑。

立契約書人：
甲方（出租人）：<person:1>（簽名蓋章）
乙方（承租人）：<person:2>（簽名蓋章）
丙方（連帶保證人）：<person:3>（簽名蓋章）
中華民國 113 年 10 月 28 日""",
    ),
    SeedTemplate(
        template_id="long_legal_settlement_agreement",
        domain=DomainCategory.LEGAL_CONSULTATION,
        length_category=TextLengthCategory.LONG,
        name_zh="重大交通事故民事侵權賠償和解書暨公證協議",
        template_text="""民事車禍損害賠償和解協議書

立和解書人：
甲方（被害人 / 賠償請求權人）：<person:1>
國民身分證統一編號：<national_id_number:1>
出生年月日：民國 <date_of_birth:1>
通訊住址：<address:1>
聯絡手機：<phone_number:1>
事故當時駕駛車輛牌照號碼：<license_plate:1>

乙方（加害人 / 損害賠償義務人）：<person:2>
國民身分證統一編號：<national_id_number:2>
出生年月日：民國 <date_of_birth:2>
駕照號碼：<drivers_license_number:1>
戶籍地址：<address:2>
聯絡手機：<phone_number:2>
事故當時駕駛車輛牌照號碼：<license_plate:2>
登記車主公司（統一編號：<tax_id:1>）：台灣速達通運股份有限公司

見證律師：<person:3> 律師（律師證字號：臺律字第 10842 號）
律師事務所通訊地址：<address:3>
律師聯絡專線：<phone_number:3>

茲雙方就民國 113 年 06 月 20 日下午 15 時 40 分許，發生於新北市板橋區縣民大道與漢生東路口之交通事故損害賠償事件，經見證律師與新北市政府調解委員會熱心斡旋，雙方互諒互讓，本於誠信原則達成和解協議，條款如下：

第一條：事故原委確認
乙方於上述時地駕駛車牌號碼 <license_plate:2> 之租賃客貨車，因變換車道未保持安全間距且未依號誌燈指示轉彎，致與甲方騎乘之重型機車（車號：<license_plate:1>）發生嚴重擦撞，致甲方受有右側鎖骨閉鎖性骨折、左膝韌帶挫傷撕裂及機車全損之損害。
本件事故業經新北市政府警察局海山分局交通分隊受處理在案（交通事故登記聯單編號：A11306200088）。

第二條：賠償總額與給付方式
1. 乙方同意賠償甲方因本件車禍所受之一切財產上及非財產上損害（包含但不限於急診與住院醫療費、鎖骨內固定鋼板手術自費耗材費、機車修復全損折價、六個月工作不能之薪資補償、看護看護費以及精神慰撫金），共計新台幣柒拾貳萬元整（NT$ 720,000 元）。
2. 給付方式：
   (1) 第一期款：乙方應於本和解書簽署之當日，將新台幣參拾萬元整（NT$ 300,000 元）以現金或即期支票交付甲方點收。
   (2) 第二期款：餘款新台幣肆拾貳萬元整（NT$ 420,000 元），乙方應於民國 113 年 07 月 31 日前，由乙方直接電匯至甲方開立之專屬金融帳戶：
       解款行代碼：004（臺灣銀行板橋分行）
       受款帳戶帳號：<bank_account:1>
       戶名：<person:1>
3. 本和解金額不包含強制汽車責任保險給付，甲方得另行依法向保險公司申請強制險醫療給付，乙方及車主公司應無條件出具理賠申請必要之車主蓋章證明文件。

第三條：刑事告訴之撤回與拋棄請求權
1. 甲方於收訖上述第一期和解款項之同時，應立即向臺灣新北地方檢察署出具「撤回刑事告訴狀」，具狀撤回對乙方過失傷害罪之刑事告訴（案號：113 年度偵字第 48190 號）。
2. 自本和解書簽訂且乙方如期履行各期賠償金給付完畢之時起，甲方願拋棄對乙方及登記車主台灣速達通運股份有限公司之其餘民事損害賠償請求權。

第四條：違約懲罰
乙方若有任何一期款項未依約如期足額匯入甲方指定帳戶，視為全部債務到期，乙方除應立即清償未到期之全部金額外，並應自遲延之日起按年利率百分之五加計遲延利息，另應給付甲方懲罰性違約金新台幣拾萬元整。

本和解協議書壹式肆份，經雙方及見證律師當場審閱無訛後簽名用印，由甲、乙雙方各執乙份，見證律師及調解會各留存乙份存卷備查。

立和解書人：
甲方（受害人）：<person:1>（簽名捺印）
乙方（賠償人）：<person:2>（簽名捺印）
車主法定代理人：<person:4>（統編：<tax_id:1>）
見證律師：<person:3>（簽章）
中華民國 113 年 07 月 05 日""",
    ),
    SeedTemplate(
        template_id="long_bank_credit_loan_agreement",
        domain=DomainCategory.BANKING_FINANCE,
        length_category=TextLengthCategory.LONG,
        name_zh="個人房屋抵押借款契約書暨綜合授信約定書",
        template_text="""個人房屋抵押借款契約書（玉山商業銀行定型化授信合約）

立契約書人：
借款人（以下簡稱甲方）：<person:1>
國民身分證統一編號：<national_id_number:1>
出生年月日：民國 <date_of_birth:1>
戶籍地址：<address:1>
通訊地址：<address:2>
聯絡電話（手機）：<phone_number:1>
電子郵件信箱：<email:1>

連帶保證人（以下簡稱乙方）：<person:2>
國民身分證統一編號：<national_id_number:2>
戶籍地址：<address:3>
聯絡電話（手機）：<phone_number:2>

貸款金融機構（以下簡稱丙方）：玉山商業銀行股份有限公司
統一編號：<tax_id:1>
法定代理人：<person:3>
分行營業地址：<address:4>

茲甲方因購置不動產及家庭生活週轉資金需要，向丙方申請房屋抵押貸款，經乙方同意擔任連帶保證人，雙方合意簽訂本契約，條款如下：

第一條：借款金額與授信期間
1. 借款本金：新台幣壹仟貳佰萬元整（NT$ 12,000,000 元）。
2. 借款期間：自民國 113 年 12 月 01 日起至民國 143 年 11 月 30 日止，計三十年。
3. 寬限期：自撥款日起算兩年，寬限期內僅按月計繳利息，第三年起依年金法按月平均攤還本息。

第二條：利率計算與調整機制
本借款利率按丙方定儲利率指數（現行為年息 1.72%）加碼年息 0.46% 計算，目前實質借款年利率為 2.18%。未來定儲利率指數調整時，丙方得隨之等幅調整。

第三條：撥款約定與扣款帳戶
丙方核貸後，甲方指定將本筆借款本金全額一次撥入甲方開立於丙方之活期儲蓄存款帳戶：
受款帳戶帳號：<bank_account:1>
戶名：<person:1>
日後每月攤還之本金與利息，甲方亦同意直接由該帳戶中自動授權扣繳。

第四條：抵押標的物之擔保
為擔保本借款債務之如期清償，甲方願提供其所有座落於 <address:5> 之不動產（土地及全部建物），設定第一順位最高限額抵押權新台幣 1,440 萬元整予丙方。

第五條：加速條款與違約金
甲方若有任何一期本息遲延給付逾三十日，或受強制執行、破產宣告之情事，丙方得視為全部債務到期，甲方除應立即清償全部剩餘本金外，並自遲延之日起按原約定利率加收百分之十之違約金；逾期六個月以上者，其超逾六個月部分加收百分之二十違約金。

第六條：個人資料保護與聯徵查詢同意
甲方與乙方同意丙方為辦理授信業務、風險控管之需要，得將其個人資料、授信紀錄蒐集、處理並報送至財團法人金融聯合徵信中心。

本契約書壹式參份，由甲、乙、丙三方各執乙份為憑。
立約人：
甲方（借款人）：<person:1>（簽章）
乙方（連帶保證人）：<person:2>（簽章）
丙方（貸款機構）：玉山商業銀行股份有限公司（用印）
中華民國 113 年 11 月 25 日""",
    ),
    SeedTemplate(
        template_id="long_telecom_enterprise_broadband_agreement",
        domain=DomainCategory.TELECOM,
        length_category=TextLengthCategory.LONG,
        name_zh="企業光纖寬頻網路服務契約與派工施工單",
        template_text="""企業商用光纖寬頻網路租用契約書（中華電信企業方案）

申租用戶單位（以下簡稱甲方）：
企業公司行號名稱：台灣神達資訊系統股份有限公司
統一編號：<tax_id:1>
公司法定代表人：<person:1>
負責人身分證字號：<national_id_number:1>
公司登記地址：<address:1>
光纖裝機施工地址：<address:2>
郵遞區號：<postal_code:1>

專案負責聯絡人：<person:2>
聯絡電話（公務手機）：<phone_number:1>
聯絡電子信箱：<email:1>

電信服務提供者（以下簡稱乙方）：中華電信股份有限公司
營業處地址：<address:3>
業務授權代表：<person:3>
專案代表聯絡手機：<phone_number:2>

茲就甲方租用乙方所提供之商用企業對稱式固定光纖電路網路服務，雙方同意訂定下列契約條款：

第一條：租用電路規格與月租費率
1. 租用頻寬電路：HiLink 企業專線 500M / 500M 對稱型光纖乙太網路，配發 8 個固定公有 IP 位址。
2. 每月網路連線月租費：新台幣貳萬肆仟元整（NT$ 24,000 元，含營業稅）。
3. 電路首次設定裝機施工費：新台幣參仟伍佰元整，於第一期帳單合併計收。

第二條：合約租期與提前解約違約金
1. 本專案合約租用期限自工程竣工派工驗收合格之日起算，為期二十四個月整。
2. 甲方若於合約租期屆滿前提前退租或降速，應依合約未到期月數按比例補繳終端設備補助款及施工優惠違約金。

第三條：帳單繳款與金融自動轉帳
甲方同意每月電信資費帳單採電子帳單方式寄送至聯絡信箱 <email:1>，並授權乙方按月自甲方開立於第一商業銀行之公司存款帳戶自動扣繳款項：
金融機構代碼：007（第一銀行新板分行）
自動扣繳專用帳號：<bank_account:1>
戶名：台灣神達資訊系統股份有限公司

第四條：工程施工與設備保管
乙方預計派工於上述裝機地址進行光纜引進與光化終端設備（ONU）安裝。甲方應提供乾淨電源接地與專用機房機櫃空間。租賃期間設備財產權屬乙方所有，甲方應盡善良管理人注意義務保管。

第五條：個人資料保護法遵循
雙方就本契約履行所涉之個人聯絡資訊（包括姓名、電話、身分證號、電子信箱），均應切實遵守中華民國個人資料保護法之規定，僅得於本服務履行與帳務管理範圍內使用。

立約人：
甲方（申租企業）：台灣神達資訊系統股份有限公司
代表人：<person:1>（用印）
乙方（電信營運商）：中華電信股份有限公司企業客戶分公司（用印）
中華民國 113 年 09 月 18 日""",
    ),
    SeedTemplate(
        template_id="long_ecom_crossborder_manifest",
        domain=DomainCategory.ECOMMERCE_LOGISTICS,
        length_category=TextLengthCategory.LONG,
        name_zh="跨境電商進口貨物報關委任書與派送清冊",
        template_text="""海關進口快遞貨物個別委任報關書暨貨物派送清冊
報單號碼：CX-113-894-39182
分提單號（HAWB）：8912839102
海關監管代碼：00591

一、進口收件人（個人申報納稅義務人）基本資料
收件人姓名：<person:1>
國民身分證統一編號 / 居留證號：<national_id_number:1>
出生年月日：民國 <date_of_birth:1>
EZ WAY 實名認證綁定門號：<phone_number:1>
收件通訊地址：<address:1>
郵遞區號：<postal_code:1>
個人聯絡電子信箱：<email:1>

二、境外發貨電商平台與國內報關代理人
發貨電商商戶：跨境海外直郵全球購
清關申報代碼：TW-IMPORT-GLOBAL
受委任報關代理人：萬達國際物流股份有限公司
營利事業統一編號：<tax_id:1>
報關行營業地址：<address:2>
報關行專案聯絡電話：<phone_number:2>

三、進口包裹申報貨物明細
1. 品名：SONY 無線降噪耳機 WH-1000XM5（黑色）
2. 數量：1 組，淨重：0.85 KG
3. 申報完稅價格：新台幣 8,900 元整（未逾進口自用免稅門檻限制）
4. 進口稅則號別（CCC Code）：8518.30.00.00-6
5. 派送配合物流：黑貓宅急便物流專車（宅配車號：<license_plate:1>）
   配送司機姓名：<person:2>，司機聯絡手機：<phone_number:3>

四、委任報關與個資授權條款
1. 委任人 <person:1> 茲授權萬達國際物流股份有限公司代為向財政部關務署台北關辦理上述快遞貨物之進口通關、稅費申報及查驗提貨等一切手續。
2. 委任人保證上述申報之收件人姓名、身分證字號、聯絡手機及收件地址皆為本人真實資訊，並已於海關「EZ WAY 易利委」APP 完成實名委任確認。
3. 報關代理人承諾對委任人所提供之身分證證號及通訊地址負保密之責，除依法供海關查核通關外，絕不挪作其他商業用途。
4. 本清冊與委任書電子檔依關稅法第十七條規定留存五年備查。

委任人（進口人）：<person:1>（簽章確認）
受任人（報關行）：萬達國際物流股份有限公司（蓋章）
中華民國 113 年 10 月 15 日""",
    ),
]

# Register all default seed templates
for _t in _SHORT_TEMPLATES + _MID_TEMPLATES + _LONG_TEMPLATES:
    SeedTemplateLibrary.register(_t)
