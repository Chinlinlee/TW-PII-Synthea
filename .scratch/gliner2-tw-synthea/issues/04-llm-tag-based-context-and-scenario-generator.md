# LLM 語境生成與 Tag-to-Span 解析管線設計
Type: prototype
Status: open
Blocked by: 02, 03

## Question

如何設計 LLM Prompting 流程與 XML 標籤解析管線，以產生多樣且具備自然繁體中文口吻的台灣語境文本？
需涵蓋：
1. 長短文本分佈：`short`（單句/客服、15-120 字）、`mid`（LINE 對話、客訴信件、申辦表單、200-1000 字）、`long`（病歷紀錄、租賃/勞動契約、會議紀錄、1500-5000 字）。
2. 多樣化場景矩陣（醫療院所掛號、金融銀行開戶與爭議款、電信簽約、蝦皮/網購退貨、租屋、法律諮詢）。
3. XML-style 實體標籤注入與抽取規則（例如 `<person>...</person>`），並在去標籤化時精確計算每段 span 之字元級 `start` / `end` offset。
4. 結合 `tw-PII-bench` 的情境模式與種子模板擴充策略。
產出原型生成腳本與 parser 驗證。
