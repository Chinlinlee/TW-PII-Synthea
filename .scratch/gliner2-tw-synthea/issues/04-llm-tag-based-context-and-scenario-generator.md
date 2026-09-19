# LLM 語境生成與 Tag-to-Span 解析管線設計
Type: prototype
Status: resolved
Blocked by: 02, 03

## Question

如何設計 LLM Prompting 流程與 XML 標籤解析管線，以產生多樣且具備自然繁體中文口吻的台灣語境文本？
需涵蓋：
1. 長短文本分佈：`short`（單句/客服、15-120 字）、`mid`（LINE 對話、客訴信件、申辦表單、200-1000 字）、`long`（病歷紀錄、租賃/勞動契約、會議紀錄、1500-5000 字）。
2. 多樣化場景矩陣（醫療院所掛號、金融銀行開戶與爭議款、電信簽約、蝦皮/網購退貨、租屋、法律諮詢）。
3. XML-style 實體標籤注入與抽取規則（例如 `<person>...</person>`），並在去標籤化時精確計算每段 span 之字元級 `start` / `end` offset。
4. 結合 `tw-PII-bench` 的情境模式與種子模板擴充策略。
產出原型生成腳本與 parser 驗證。

## Answer

已於 `src/pii_synthea/scenarios/` 建立完整的台灣語境情境矩陣、XML 標籤字元級抽取與驗證解析器、Prompt 工程建構器、豐富種子模板庫與整合編排器，全數通過單元測試（41/41 passed in 0.09s）。

### 1. 模組架構與職責

- `src/pii_synthea/scenarios/domains.py`：
  - **六大核心領域矩陣（`DomainCategory`）**：
    1. `HEALTHCARE`（醫療院所與公衛）：門診掛號、病歷出院摘要、處方用藥、健保申報。
    2. `BANKING_FINANCE`（金融銀行與支付）：開戶徵信、信用卡爭議款、跨行匯款、房貸契約、OTP 動態密碼。
    3. `TELECOM`（電信通訊與資費）：5G 門號續約攜碼、SIM 卡遺失補發、光纖寬頻施工工單、帳單繳費。
    4. `ECOMMERCE_LOGISTICS`（網購電商與物流配送）：蝦皮退貨聊聊、7-11/全家超商取件、黑貓宅配、EZ WAY 跨境報關。
    5. `REAL_ESTATE`（租屋不動產與物業）：定金簽收單、房東修繕與租金匯款對話、內政部定型化住宅租賃契約。
    6. `LEGAL_CONSULTATION`（法律諮詢與民事調解）：車禍和解簡訊、調解委員會言詞陳述、存證信函與律師委任合約。
  - **三大篇幅級距（`TextLengthCategory`）**：
    - `SHORT`（15–120 字）：單句推播、驗證碼簡訊、取件提醒。
    - `MID`（200–1000 字）：LINE 多輪對話、客訴電郵、文字客服紀錄。
    - `LONG`（1500–5000 字）：正式臨床病歷、租賃契約、銀行借款契約、存證信函。
  - **情境註冊表（`ScenarioRegistry`）**：預置 18 種具備關鍵情境詞彙（如健保卡、統編、大安區、對保、掛號、初判表等）與角色設定的在地規格。

- `src/pii_synthea/scenarios/tag_parser.py`：
  - **XML 標籤抽取與字元級去標籤化（`TagToSpanParser`）**：
    - 支援封閉標籤 `<person>林志豪</person>`、帶索引標籤 `<person:1>林志豪</person:1>`、屬性標籤 `<person id="1">林志豪</person>`、自閉合標籤 `<person/>`、空標籤 `<person></person>` 與 Mustache `{{person:1}}`。
    - 自動剝除 LLM 常見之 Markdown codeblock 外層標記（````xml ... ````）。
    - 精確計算標籤剝除後純文字之零基字元級 `[start, end]` offset，即時斷言 `assert clean_text[start:end] == span.text` 且絕無重疊。
  - **演算法真偽檢查與自動校驗抽換（`normalize_invalid`）**：
    - 針對 LLM 幻覺生成的無效個資（如身分證字號 Checksum 錯誤之假號碼、無效統編、假信用卡號等），自動調用 `src/pii_synthea/generators/` 進行校驗。
    - 若校驗不合格，自動以 `TaiwanPIIGenerator` 產出合法台灣實體，並由 `SpanReplacer` 進行逆向替換與下游 offset 自動重算（delta shift），保證產出 100% 具備演算法真實性。

- `src/pii_synthea/scenarios/prompts.py`：
  - **LLM 提示詞建構器（`PromptBuilder`）**：
    - 封裝系統提示詞（規範繁體中文台灣正體國字、台灣在地生活詞彙、語氣助詞「蛤、喔、收到、麻煩了」、負樣本意識排除公共地標/店家名/政府專線）。
    - 針對 `short`、`mid`、`long` 三種篇幅提供針對性的 Few-shot 示範樣本。
    - 支援 `direct` 標籤產出模式與 `template_only` 空標籤骨架產出模式。

- `src/pii_synthea/scenarios/templates.py`：
  - **在地種子模板庫（`SeedTemplateLibrary`）**：
    - 內建覆蓋所有 6 大領域與 3 大篇幅級距（共 19 套高真實度樣板）。
    - 100% 離線可用，無需連網或調用付費 API 即可直接批次產出完全合規且位移校驗 100% 正確的合成訓練資料。

- `src/pii_synthea/scenarios/generator.py`：
  - **高階情境合成與資料匯出器（`ScenarioSynthesizer`）**：
    - 支援由種子單筆生成、按領域/長度權重分佈進行批次合成（`synthesize_batch`）。
    - 支援外部 LLM 回應字串解析（`ingest_llm_response`）。
    - **雙重格式匯出**：
      1. `export_gliner2_dataset()`：匯出 GLiNER2 標準訓練格式 JSONL。
      2. `export_tw_pii_bench_dataset()`：透過 `TaxonomyMapper` 自動將 21 類標籤雙向轉換為 `tw-PII-bench` 評測格式（`tw_national_id`、`private_person`、`private_address` 等）。

### 2. CLI 指令擴充與驗證

`main.py` 新增 4 大情境與標籤解析指令：
1. `uv run python main.py list-scenarios`：列出 18 種在地領域情境與長度規模。
2. `uv run python main.py generate-scenario --domain healthcare --length mid --seed 42`：離線合成完整門診掛號對話與精準 Span。
3. `uv run python main.py parse-tags --text "..." --normalize`：解析任意 XML 標籤字串，自動將無效個資正規化為合法台灣 PII。
4. `uv run python main.py build-prompt --scenario-id health_sms_reminder`：印出對應情境之 System/User Prompt 與 Few-shot 範例。

### 3. 測試覆蓋率
- `tests/test_scenarios.py` 新增 11 個單元測試，涵蓋領域定義、單一/多標籤解析、Markdown 剝除、空標籤生成、無效證號正規化抽換、Prompt 產出、全種子模板驗證、批次合成與 GLiNER2 / `tw-PII-bench` 檔案匯出。
- 全庫總計 **41 個測試全部通過**（41 passed in 0.09s）。

