# 演算法合法之台灣在地 PII 生成與雙向驗證器原型
Type: prototype
Status: resolved
Blocked by: none

## Question

如何實作一個具備演算法真實性（Synthetically Validated）的 Python 台灣 PII 產生器與驗證庫？
需支援：
1. 身分證字號產生器（包含首字母縣市權重 + 性別代碼 + Checksum 計算）與新式外來人口統一證號。
2. 營利事業統一編號產生器（8 碼邏輯乘數 mod 10 / 第 7 碼為 7 之 mod 5 檢驗）。
3. 健保卡號（12 碼）、車牌號碼（舊式與新式 3+4、4+2 格式）、護照與駕照格式。
4. 台灣各縣市真實鄉鎮市區、常見路街名、巷弄號樓與 3+2 / 3+3 郵遞區號匹配生成器。
5. 台灣真實百家姓、男女常見名字、原住民音譯姓名庫。
6. 動態實體替換與 Span Offset 自動重算驗證器（確保 `text[start:end] == span_text` 100% 正確）。
產出可執行的原型腳本與單元測試。

## Answer

已於 `src/pii_synthea/generators/` 實作完整的台灣在地 PII 演算法生成與雙向驗證引擎，以及字元層級位移保全系統（Offset-Preserving Span Engine），並全數通過單元測試（30/30 passed）。

### 1. 模組架構與職責劃分

- `src/pii_synthea/generators/id_card.py`：
  - **身分證字號（National ID）**：實作 26 縣市英文代碼權重換算、性別代碼（1/2）與尾碼檢查碼演算法 `calculate_id_check_digit()`，支援隨機生成與 `validate_national_id()` 雙向校驗。
  - **外來人口統一證號（ARC）**：完整支援新式外來人口統號（首碼英文字母 + 第二碼 8/9 性別碼 + 檢查碼）與舊式外來人口統號（第二碼 A-D 英文代碼換算模 10 權重乘數）。
  - **戶口名簿戶號（`tw_household_no`）**：支援首碼英文 + 7 位數字之生成與格式驗證。
- `src/pii_synthea/generators/business.py`：
  - **營利事業統一編號（統編 / Tax ID）**：實作財政部官方標準之 8 碼邏輯乘數 `[1, 2, 1, 2, 1, 2, 4, 1]` 交叉乘積加總。
  - **特殊邊界驗證**：支援第 7 碼為 7 之特例（如華碩電腦統編 `23638777` 之 `(total - 1) % 10 == 0` 判定路徑）。內建台積電、鴻海、聯發科、華碩、統一超商等知名標竿企業統編。
- `src/pii_synthea/generators/address.py`：
  - **完整台灣行政區劃**：內建全台 22 縣市、368 鄉鎮市區之官方 3 碼郵遞區號對照表。
  - **真實道路與門牌**：包含都會區精確主要道路（如忠孝東路、台灣大道、一心路）與通用路街名、分段、巷弄號樓室門牌層次組合。
  - **郵遞區號**：支援 3 碼（如 `106`）、3+2 碼（`10667`）與 3+3 碼（`106-456`）之生成與驗證。
- `src/pii_synthea/generators/names.py`：
  - **百家姓氏**：收錄涵蓋全台逾 85% 人口之常見姓氏，以及複姓庫（歐陽、司徒、諸葛等）。
  - **男女與單字名**：真實台灣世代常見男子名（志豪、冠宇、柏翰等）、女子名（佳玲、雅婷、怡君等）與單字名。
  - **原住民族傳統姓名**：收錄具備傳統中點音譯姓名（如尤瑪·達魯、莫那·魯道）與羅馬拼音姓名（Yuma Taru、Walis Nokan）。
  - **中英雙語名**：支援台灣職場與外商常見之英文名字組合（如 Kevin Lin, Jessica Wu）。
- `src/pii_synthea/generators/phone.py`：
  - **行動電話（Mobile）**：支援中華電信、台灣大、遠傳等主流 09xx 號段，支援破折號 `0912-345-678`、緊湊、空格與國際國碼 `+886-912-345-678` 格式。
  - **市內電話（Landline）**：依據區碼（02 大台北/基隆 8 碼、04 台中 8 碼、07 高雄 8 碼、03 桃竹苗 7 碼等）產生正確碼長，並支援分機（分機/ext/#）。
- `src/pii_synthea/generators/financial.py`：
  - **信用卡卡號**：實作 16 碼 Luhn 演算法之 Visa、Mastercard、JCB 合法卡號生成與校驗。
  - **金融機構帳號**：收錄全台商業銀行與中華郵政 700 郵局之 10-16 位帳號。
  - **CVV 安全碼**：3 碼/4 碼驗證。
- `src/pii_synthea/generators/misc.py`：
  - 健保卡號（12 碼）、汽機車車牌（新式 ABC-1234、舊式 1234-AB、機車 123-ABC）、護照號碼（9 碼晶片護照 `3\d{8}`）、駕照號碼、民國/西元生日、LINE ID、PTT 帳號、醫事證書字號（醫字第/護理字第）、軍人證號（陸字第）、電子郵件與密碼金鑰。
- `src/pii_synthea/generators/master.py`：
  - `TaiwanPIIGenerator` 提供一鍵分發介面，支援直接透過 21 個 Canonical ID 或 GLiNER2 標籤生成合成資料，並支援固定隨機種子（`seed`）達成 100% 確定性重現。

### 2. 位移保全與 Span 自動校驗引擎 (`src/pii_synthea/generators/replacement.py`)

1. **`Span` 與 `SynthesisResult`**：
   - 封裝字元層級 `[start, end]`、`label`、`text` 與 `canonical_id`。
   - `validate()` 方法嚴格執行三道完整性防線：
     - 邊界檢查：`0 <= start < end <= len(text)`
     - 字串切片斷言：`assert text[start:end] == span.text`
     - 重疊檢測：排序後相鄰 Span 不得有任何字元重疊。
   - `to_gliner2_format()`：匯出為 GLiNER2 訓練資料標準規格。
2. **`TemplateEngine`**：
   - 支援 `{{label}}`、`<label>` 以及具備上下文綁定的索引標籤 `{{person:1}}`。
   - 在模板掃描替換過程中動態維護字串長度與累加 offset，生成後即時斷言 `assert text[s.start:s.end] == s.text`。
3. **`SpanReplacer`**：
   - 支援對既有文本中的已標註 Span 進行局部實體抽換，採右至左逆序替換與下游 offset 差值補償（delta shift），保持其他實體 offset 100% 正確。

### 3. CLI 擴充與測試驗證

- 單元測試套件 `tests/test_generators.py`（包含 26 個專屬測試函數，涵蓋各演算法隨機抽樣、極端特例、已知企業統編與位移校驗），搭配 `test_taxonomy.py` 共 30 個測試全部通過。
- `main.py` 擴充 CLI 指令：
  - `uv run python main.py generate-sample --seed 42`（快速抽樣 21 類實體）
  - `uv run python main.py render-template --seed 42`（測試模板注入與 Span 標註校驗）

