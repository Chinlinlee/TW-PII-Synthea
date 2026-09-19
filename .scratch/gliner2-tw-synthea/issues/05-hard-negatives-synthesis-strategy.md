# 台灣在地難辨負樣本（Hard Negatives）生成策略調研
Type: research
Status: resolved
Blocked by: none

## Question

如何系統化建立台灣專屬的 Hard Negatives（外觀酷似 PII 但嚴禁標註為個資）資料生成策略？
調查並彙整：
1. **商家與品牌含人名**（如：梁社漢排骨、阿宗麵線、鬍鬚張魯肉飯、林東芳牛肉麵、林銀杏）之實體名冊與句子模板。
2. **公眾人物與歷史政治名詞**（如：賴清德、蔣中正、孫中山、中正紀念堂、中山高速公路、忠孝東路）之邊界排除規則。
3. **知名地標與公共建築地址**（如：台北101、總統府、國父紀念館、故宮博物院）。
4. **公共緊急與諮詢專線**（如：1999、165、110、119、1922、1980、0800 免付費客服電話）。
5. **機構/學校/政府公開通用信箱**（如：`service@gov.tw`、`admissions@ntu.edu.tw`）。
輸出可直接調用的實體字典清單與對應的合成語境生成規則。

## Answer

已在 `src/pii_synthea/negatives/` 完成系統化台灣難辨負樣本（Hard Negatives）子系統之實體編排、情境模板與合成調度引擎，並於 `tests/test_negatives.py` 完成 7 項全面單元測試（全專案 48 測項 100% 通過）。

### 1. 核心實體分類與干擾對照表 (HardNegativeCatalog)

涵蓋 6 大維度、共計 80+ 筆台灣在地高頻混淆實體：

| 分類 ID (`HardNegativeCategory`) | 易混淆之 PII 標籤 (`confusable_with`) | 代表性台灣在地實體清單 | 混淆特徵與排除邊界規則 |
| :--- | :--- | :--- | :--- |
| `brand_person_name` | `person` | 梁社漢排骨、鬍鬚張魯肉飯、阿宗麵線、林東芳牛肉麵、劉山東牛肉麵、林銀杏、吳寶春麥方店、郭元益、鼎泰豐、王品牛排、洪瑞珍三明治、金峰魯肉飯、施家麻油腰花、廖家牛肉麵、周氏蝦捲、萬巒海鴻豬腳、莊家火雞肉飯、曾記麻糬、薛家排骨飯、杜老爺冰淇淋、陳允寶泉、彭園會館 | 品牌內嵌真實自然人姓名結構，在「去買梁社漢排骨」語境下應視為商家法人/產品，嚴禁標註為 `person`。 |
| `public_historical_figure` | `person` / `address` | 孫中山、蔣中正、蔣經國、李登輝、賴清德、忠孝東路、中山北路、中正路、中山高速公路、中正紀念堂、國父紀念館、經國七海文化園區、八田與一紀念園區、延平北路、莫那魯道紀念碑 | (1) 公共歷史與現任政要新聞常客非一般自然人個資；(2) 偉人路名易被分詞錯誤切出人名（如「中正路」誤標「中正」為人名）。 |
| `public_landmark_address` | `address` | 台北101（台北市信義區信義路五段7號）、總統府（台北市中正區重慶南路一段122號）、行政院（台北市中正區忠孝東路一段1號）、國立故宮博物院（台北市士林區至善路二段221號）、台北車站（台北市中正區北平西路3號）、桃園國際機場（桃園市大園區航站南路9號）、台中國家歌劇院（台中市西屯區惠來路二段101號）、高雄流行音樂中心（高雄市鹽埕區真愛路1號）、國立臺灣大學（台北市大安區羅斯福路四段1號） | 全國知名公有地標與機關公開地址，在公共參訪、導覽情境下不屬私人居住或私密工作地址，做為無個資負樣本。 |
| `public_hotline` | `phone_number` | 1999（市民當家熱線）、165（反詐騙專線）、110（報案專線）、119（救護消防）、1922（疾管署防疫）、1980（張老師）、1925（安心專線）、113（保護專線）、1950（消保專線）、168（路況）、1968（高公局）、0800-000-123、0800-080-412、0800-030-598 | 外觀為 3~4 碼短碼或 0800 免付費公用號碼，易被模型誤判為手機號或私人家用市話，需嚴格排除。 |
| `public_email` | `email` | `service@gov.tw`、`admissions@ntu.edu.tw`、`mayor@gov.taipei`、`contact@president.gov.tw`、`info@itri.org.tw`、`service@cht.com.tw`、`press@mfa.gov.tw`、`cs@post.gov.tw`、`privacy@twcert.org.tw`、`consumer@ey.gov.tw` | 政府入口網、公立大學教務處、市府公務公開服務信箱，非自然人私人聯絡電郵。 |
| `official_code_number` | `tax_id` / `national_id_number` / `bank_account` / `tw_nhi_card` | AB-12345678（統一發票）、QP-98765432（雲端發票）、TW9876543210123（跨境物流單號）、711-89230194（超商取件碼）、府工建字第1120123456號（建築公文字號）、衛部醫字第1131660123號、診號：035號、檢驗單號：LAB-2024-99881 | 外觀與統編（8碼）、身分證（首碼英文字母加9碼數字）或健保卡（12碼）極為相似之公文流水序號、包裹條碼與發票字軌。 |

---

### 2. 雙軌生成策略：純負樣本 vs 混雜干擾樣本

為使模型在下游具備高準確率（Precision）與低虛警率，實作雙軌合成機制：
1. **純負樣本（Pure Negative, `spans == []`）**：
   - 語境包含上述負樣本實體（如美食專訪、防詐宣導、交通路況、招標公告），但全篇完全無任何真實個人 PII。
   - 匯出至 GLiNER2 格式時為 `{"text": "...", "spans": []}`，訓練模型學會輸出空標註。
2. **混雜干擾樣本（Mixed Distractor Negative, `spans == [true_pii...]`）**：
   - 將真實個人 PII（如顧客姓名、手機、外送私人地址、信用卡）與負樣本干擾詞（如「梁社漢排骨」、「165專線」、「台北101」）共置於同一個情境。
   - 透過 `TagToSpanParser` 與精確字元位移驗證，確保**只有真實個人 PII 擁有 span 標註**，干擾實體嚴格不給予 span，訓練模型在複雜語境下的實體邊界辨別力。

---

### 3. 程式架構與代碼實體

- `src/pii_synthea/negatives/catalog.py`: `HardNegativeCatalog` 集中管理各類實體名冊、檢索與隨機抽樣。
- `src/pii_synthea/negatives/templates.py`: `HardNegativeTemplateLibrary` 收錄 14 組純負樣本模板與 12 組混雜干擾模板，涵蓋 short, mid, long 三種篇幅。
- `src/pii_synthea/negatives/generator.py`: `HardNegativeSynthesizer` 支援 `generate_pure()`、`generate_mixed()` 與 `generate_batch()`。
- `src/pii_synthea/scenarios/generator.py`: `ScenarioSynthesizer.synthesize_batch_with_negatives(total_count, negative_ratio=0.15, pure_negative_ratio=0.5)` 提供跨模組融合批次生產。
- `main.py` CLI 擴充：
  - `list-negatives`：檢視 6 大負樣本分類清冊與實體統計。
  - `generate-negative`：直接生成純負樣本或混雜樣本（`--mixed`），支援指定分類與匯出 GLiNER2 JSON。

---

### 4. 推薦訓練集融合比例（Dataset Blending Recipe）

在 Ticket 06 批次產出 10,000+ 筆資料時，建議採用以下配比：
- **一般 PII 正向情境（Positive PII）**：85%
- **難辨負樣本（Hard Negatives）**：15%
  - 其中 **50% 為純負樣本（Pure Negatives, 0 spans）**（提升拒識能力）
  - 其中 **50% 為混雜干擾樣本（Mixed Negatives）**（提升高難度邊界辨析力）

