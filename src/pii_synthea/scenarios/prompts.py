"""
Prompt Builder for LLM Taiwan PII Context & Scenario Generation.
Produces highly structured, localized Traditional Chinese prompts for generating
synthetic PII texts with XML-style entity annotations.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from pii_synthea.scenarios.domains import (
    DomainCategory,
    ScenarioDefinition,
    ScenarioRegistry,
    TextLengthCategory,
)
from pii_synthea.taxonomy import TaxonomyMapper


class PromptBuilder:
    """
    Constructs prompt specifications for LLMs (Claude, GPT-4o, Gemini, Llama/Qwen)
    to generate authentic Taiwanese texts with exact XML entity tags.
    """

    SYSTEM_PROMPT_TEMPLATE = """你是一個專門生成「台灣繁體中文（zh-TW）個人資料（PII）高真實度語料」的資料合成專家。
你的任務是根據指定的場景主題與篇幅要求，產出文字語氣極度自然、貼合台灣真實生活與文化脈絡的文本，並精準使用 XML 標籤標記出文中的個人敏感資料。

【標籤標註規範】
1. 所有個人資料實體必須使用指定的 XML 標籤成對包覆：`<label>實體內容</label>`。
2. 若同一個人在文中多次出現（如姓名、身分證），請使用帶索引的標籤保持一致性：`<person:1>姓名</person:1>`，後續重複出現時仍標記為 `<person:1>姓名</person:1>`。
3. 標籤內部只包覆實體本身，嚴禁將前後標點符號、稱謂（如「先生」、「小姐」）或空白包入標籤內。
   正確：`<person>陳建宏</person>先生`
   錯誤：`<person>陳建宏先生</person>`
4. 嚴禁自我嵌套標籤（例如不能在 `<address>` 內嵌套 `<postal_code>`）。
5. 嚴格遵守「非個資不標記」原則（負樣本意識）：
   - 公開商家/品牌名稱中的人名不標記（例如「梁社漢排骨」、「鬍鬚張魯肉飯」、「林東芳牛肉麵」不是 person）。
   - 公共地標或著名建築不是 private address（例如「台北101」、「總統府」）。
   - 政府公共諮詢電話不是 private phone（例如「1999市民專線」、「165反詐騙」、「110報案」）。
   - 歷史政治人物或公開官員不是 private person（例如「蔣中正」、「孫中山」）。

【台灣用語與語言風格】
- 務必使用正體繁體中文（台灣標準國字與用詞習慣）。
- 自然融入台灣常見的生活詞彙（例如：健保卡、統編、掛號、對保、蝦皮取件、黑貓宅配、大安區、戶籍地、機車、斡旋金、存證信函、初判表等）。
- 對話情境請帶入真實台灣口吻與語氣助詞（例如：好的喔、蛤、收到、麻煩了、不好意思、祝順心）。
- 正式合約或病歷請維持標準公文法規或臨床病歷專用語氣。
"""

    FEW_SHOT_SHORT = """【範例（短句 SHORT）】
<person>林雅婷</person>您好，您在玉山銀行的信用卡末四碼為<payment_card>4532</payment_card>，本次交易動態驗證碼為<secret>892154</secret>，請於2分鐘內輸入，勿告知他人。

標註說明：
- person: 林雅婷
- payment_card: 4532
- secret: 892154"""

    FEW_SHOT_MID = """【範例（中篇 MID）】
客服小編：您好！這裡是中華電信數位客服，很高興為您服務。請問今天想諮詢什麼業務呢？
用戶：您好，我想把我的 5G 門號續約，但目前不住在台北了，想順便改帳單地址。
客服小編：好的，沒問題！為確保帳戶安全，請先提供您的身分證字號與出生年月日核對基本資料喔！
用戶：好的，我身分證字號是 <national_id_number>A129384756</national_id_number>，生日是民國 <date_of_birth>78年10月15日</date_of_birth>，姓名是 <person>陳志豪</person>。
客服小編：已核對完成，確認為陳先生本人。請問新的帳單寄送地址要變更為什麼呢？
用戶：請幫我改到 <address>台中市西屯區台灣大道三段99號12樓之2</address>，郵遞區號是 <postal_code>407</postal_code>，聯絡手機是 <phone_number>0912-345-678</phone_number>，電子信箱為 <email>chihhao.chen@gmail.com</email>。
客服小編：已為您登記變更，續約優惠方案合約已同步寄送至您的電子信箱，請查收！感謝您的支持。"""

    FEW_SHOT_LONG = """【範例（長篇 LONG）】
房屋租賃契約書（範本節錄）
立契約書人
出租人（以下簡稱甲方）：<person:1>王大明</person:1>，身分證字號：<national_id_number:1>A123456789</national_id_number:1>，戶籍地址：<address:1>台北市大安區新生南路二段10號</address:1>，聯絡電話：<phone_number:1>0920-111-222</phone_number:1>。
承租人（以下簡稱乙方）：<person:2>李冠宇</person:2>，身分證字號：<national_id_number:2>B120987654</national_id_number:2>，出生年月日：民國 <date_of_birth:2>82年5月12日</date_of_birth:2>，戶口名簿戶號：<tw_household_no:2>B1234567</tw_household_no:2>，通訊地址：<address:2>新北市板橋區縣民大道二段7號</address:2>，聯絡電話：<phone_number:2>0933-888-999</phone_number:2>。

茲為房屋租賃事宜，雙方合意訂定下列條款，以資共同遵守：
第一條：租賃標的與範圍
房屋座落於 <address:3>新北市新莊區中正路100號5樓之1</address:3>，出租範圍為全部住宅使用。
第二條：租賃期限
自民國 113 年 10 月 01 日起至民國 114 年 09 月 30 日止，計一年。
第三條：租金及押租金
租金每月新台幣 22,000 元整，乙方應於每月 5 日前匯入甲方指定帳戶：台灣土地銀行（代碼 005），帳號：<bank_account:1>005-003-1234567</bank_account:1>。押租金新台幣 44,000 元整，於簽約時一次付清。
第四條：違約及返還
租賃關係消滅時，乙方應將租賃標的返還予甲方。若有爭議，雙方合意以台灣新北地方法院為第一審管轄法院。
立約人：
甲方：<person:1>王大明</person:1>（簽章）
乙方：<person:2>李冠宇</person:2>（簽章）"""

    @classmethod
    def build_prompt(
        cls,
        scenario: ScenarioDefinition,
        target_length: Optional[TextLengthCategory] = None,
        custom_instructions: Optional[str] = None,
        include_few_shot: bool = True,
        template_only: bool = False,
    ) -> Dict[str, str]:
        """
        Builds a complete system prompt and user prompt pair for LLM execution.

        Returns:
            Dict[str, str]: {"system": system_prompt, "user": user_prompt}
        """
        length_cat = target_length or scenario.length_category
        pii_specs = [TaxonomyMapper.get_spec(lbl) for lbl in scenario.typical_pii_labels]
        valid_specs = [s for s in pii_specs if s is not None]

        label_guide_lines = []
        for s in valid_specs:
            label_guide_lines.append(f"- `<{s.gliner2_label}>`：{s.display_name_zh}（例如：{s.prompt_description_zh}）")

        label_guide = "\n".join(label_guide_lines)

        user_prompt_lines = [
            f"請生成一篇關於【{scenario.domain.display_name_zh}】領域的繁體中文語料。",
            f"【具體情境】：{scenario.name_zh}",
            f"【情境說明】：{scenario.description_zh}",
            f"【角色設定】：{scenario.persona_zh}",
            f"【篇幅要求】：{length_cat.value.upper()} 規模（約 {length_cat.min_chars} 至 {length_cat.max_chars} 字）。",
            f"【關鍵情境詞彙】：{', '.join(scenario.context_keywords)}",
            "",
            "【必須涵蓋或優先使用的 PII 標籤清單】：",
            label_guide,
            "",
        ]

        if template_only:
            user_prompt_lines.append(
                "【特別模式：空標籤模板】請產出包含空標籤（如 `<person:1/>` 或 `<person:1></person:1>`）的語境模板，"
                "供演算法自動填入合法個資。"
            )
        else:
            user_prompt_lines.append(
                "【產出要求】：請直接產出包覆 XML 標籤的自然文本。直接輸出最終標註文本，不需多餘的問候語或包裹額外解釋。"
            )

        if custom_instructions:
            user_prompt_lines.extend(["", "【補充指令】：", custom_instructions])

        if include_few_shot:
            few_shots = {
                TextLengthCategory.SHORT: cls.FEW_SHOT_SHORT,
                TextLengthCategory.MID: cls.FEW_SHOT_MID,
                TextLengthCategory.LONG: cls.FEW_SHOT_LONG,
            }
            user_prompt_lines.extend(["", few_shots.get(length_cat, cls.FEW_SHOT_SHORT)])

        return {
            "system": cls.SYSTEM_PROMPT_TEMPLATE,
            "user": "\n".join(user_prompt_lines),
        }

    @classmethod
    def get_supported_labels_doc(cls) -> str:
        """Returns documentation of all 21 supported canonical labels for prompts."""
        specs = TaxonomyMapper.all_specs()
        lines = ["台灣 PII 支援標籤體系（21 類）："]
        for s in specs:
            lines.append(f"- `<{s.gliner2_label}>`（{s.canonical_id}）：{s.display_name_zh}，{s.prompt_description_zh}")
        return "\n".join(lines)
