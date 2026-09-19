## Destination

`PII-Synthea` 專案產出 10,000+ 筆具備精確 Span 標註、台灣在地檢查碼校驗與難辨負樣本的合成資料集，並完成 `fastino/gliner2-privacy-filter-PII-multi` 之台灣繁體中文版本微調、模型權重匯出與在 `lianghsun/tw-PII-bench` 上的客觀評測基準報告。

## Notes

- **目標模型**：`fastino/gliner2-privacy-filter-PII-multi`（基於 GLiNER2 205M 架構，支援多標籤 Conditioned Span 提取）
- **語言與地區**：繁體中文（台灣，zh-TW），涵蓋台灣特殊 PII 格式與生活文化語境
- **架構原則**：兩階段混合引擎（LLM 台灣語境生成 + 演算法實體校驗與精確 Offset 注入 + 難辨負樣本合成）
- **種子與基準**：`lianghsun/tw-PII-bench`（short/mid/long 分流，混合萃取種子模板，並作為最終客觀基準測試）
- **規模目標**：10,000+ 筆訓練語料（含短句、中篇對話、長文本合約/病歷與負樣本）
- **核心參考專案**：`K:\python\pii-project\pii-guard`（借鑒其台灣 PII 正則與驗證演算法）
- **相關技能**：`domain-modeling`, `research`, `prototype`, `grilling`

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [台灣 PII 實體與 GLiNER2 標籤映射體系設計](issues/02-taiwan-pii-label-taxonomy-mapping.md) — 確立 21 類台灣 PII 實體之混成映射架構（14 類對齊 GLiNER2 原生標籤 + 7 類在地擴充標籤如健保卡、車牌、LINE ID），產出 schema.json 與 taxonomy.py 映射庫。
- [演算法合法之台灣在地 PII 生成與雙向驗證器原型](issues/03-deterministic-taiwan-pii-generator-and-validator.md) — 實作 21 類台灣 PII 實體演算法生成與雙向校驗庫（身分證/居留證 Checksum、統編 mod 10 / mod 5、368 鄉鎮區地址與 3+3 郵遞區號、Luhn 信用卡、電話/健保卡/車牌等），並建置字元層級位移保全引擎（TemplateEngine, SpanReplacer）確保 assert text[start:end] == span.text 100% 正確。
- [LLM 語境生成與 Tag-to-Span 解析管線設計](issues/04-llm-tag-based-context-and-scenario-generator.md) — 建立六大領域情境矩陣（醫療、金融、電信、網購、租屋、法律）、三級篇幅分佈（short 15-120 字、mid 200-1000 字、long 1500-5000 字）、XML 標籤字元級去標籤與位移保全抽取器（TagToSpanParser）、正規化校驗抽換、Prompt 工程器與 19 組高真實度離線種子庫，支援 GLiNER2 與 tw-PII-bench 雙格式匯出。
- [台灣在地難辨負樣本（Hard Negatives）生成策略調研](issues/05-hard-negatives-synthesis-strategy.md) — 建立六大維度（人名品牌、歷史政治與偉人路名、知名地標、緊急與0800專線、政府學校通用信箱、發票與代碼序號）共80+筆台灣在地難辨實體名冊，實作純負樣本（0 spans）與混雜干擾樣本雙軌合成器（HardNegativeSynthesizer），結合字元級位移校驗，支援GLiNER2空標註訓練，推薦15%負樣本混合比例。
- [萬筆資料批次生成調度器與儲存匯出管線原型](issues/06-pipeline-batch-orchestration-and-storage.md) — 實作高可靠批次生成調度器（BatchPipelineOrchestrator）、嚴格格式驗證關卡（ValidationGate）、SHA-256 全流程去重（Deduplicator）、速率限制（RateLimiter）、斷點續傳檢查點（CheckpointManager）與雙格式匯出（GLiNER2 JSONL、Apache Parquet、tw-PII-bench JSONL、summary.json），整合 CLI `generate-dataset` 命令，本機生成輸送量達 640+ samples/sec。



## Not yet specified

- **GPU 算力與微調超參數調優**：待微調腳本與首批 10,000 筆資料就緒後，根據硬體顯存（VRAM）確認 Batch Size、LoRA Rank (r)、Learning Rate 與訓練 Epochs。
- **推論最佳化與下游整合**：微調後 GLiNER2 模型之 ONNX / 量化匯出，以及回流整合至 `pii-guard` 常駐服務作為神經網路偵測後端。
- **主動學習與難例回流（Active Learning Mining）**：在 `tw-PII-bench` 上預測失敗的邊界樣本（如複姓、罕見地址格式）如何自動回流合成引擎補充合成。

## Out of scope

- 從頭預訓練全新 Transformer / BERT / DeBERTa 骨幹模型（僅對 GLiNER2 進行 LoRA / 領域微調）。
- 開發面向終端用戶的人工標註 Web UI。
- 取代 `pii-guard` 的本機去識別化與文字還原常駐服務（`PII-Synthea` 專注於合成與微調）。
