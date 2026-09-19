# 萬筆資料批次生成調度器與儲存匯出管線原型
Type: prototype
Status: resolved
Blocked by: 03, 04, 05

## Question

如何實作一個高可靠、支援中斷重啟且能穩定產出 10,000+ 筆資料的批次生成管線？
需滿足：
1. 平行呼叫或批次處理與速率限制（Rate limiting）管理。
2. 全流程資料去重（Deduplication）與分佈平衡檢查（確保每種 PII 實體與負樣本皆有足夠覆蓋度）。
3. 嚴格格式校驗器（每一筆資料執行 `assert text[s['start']:s['end']] == s['text']`，檢驗重疊 span 與邊界錯誤）。
4. 匯出為標準 GLiNER2 訓練格式（JSONL）與 Parquet，並自動劃分 Train / Validation 集。
產出管線 CLI 原型腳本。

## Resolution

已於 `src/pii_synthea/pipeline/` 實作完整高可靠批次生成調度器、格式校驗、去重、檢查點與雙格式匯出管線，並於 `main.py` 整合 `generate-dataset` CLI 命令。

### 1. 核心模組架構 (`src/pii_synthea/pipeline/`)

1. **`PipelineConfig` (`config.py`)**:
   - 集中定義管線超參數：`total_count`（目標總量，預設 1,000）、`output_dir`、`val_ratio`（預設 0.20）、`negative_ratio`（預設 0.15）、`pure_negative_ratio`（預設 0.50）、`batch_size`、`checkpoint_interval`、`resume`、`export_parquet`、`export_tw_bench`、`rate_limit_per_sec`、`seed`。
2. **`ValidationGate` & `ValidationReport` (`validator.py`)**:
   - 實作零容忍驗證關卡：
     1. 字元邊界校驗：`0 <= span.start < span.end <= len(text)`
     2. 文字精確對齊：`assert text[span.start:span.end] == span.text`
     3. 無重疊區間保證：`sorted_spans[i].end <= sorted_spans[i+1].start`
     4. 分類法標籤支援：可選啟用 `all_canonical_ids()` 白名單檢查。
   - 純負樣本允許 `len(spans) == 0` 通過。
3. **`Deduplicator` (`dedup.py`)**:
   - 使用正規化空白 + SHA-256 數位指紋雜湊表，全流程即時偵測語意/字串碰撞，過濾重複樣本並計入統計指標。
4. **`RateLimiter` (`rate_limiter.py`)**:
   - 支援可配置每秒呼叫次數限制（`rate_limit_per_sec`），為 LLM API 呼叫或高負載並行提供穩定的流量平滑與節流。
5. **`CheckpointManager` (`checkpoint.py`)**:
   - 於 `<output_dir>/.checkpoint/` 維護 `records.jsonl` 與 `metadata.json`。
   - 支援 `--resume` 中斷重啟：啟動時自動載入既有有效樣本與雜湊指紋，避免重工並精確補足剩餘配額。
6. **`DatasetExporter` (`exporter.py`)**:
   - 基於固定種子執行隨機洗牌，自動劃分 80/20 Train / Validation 集。
   - 支援三種匯出格式：
     - **GLiNER2 JSONL** (`train.jsonl`, `val.jsonl`)：標準 `{"text": "...", "spans": [{"start": ..., "end": ..., "label": ..., "text": ...}]}`。
     - **Apache Parquet** (`train.parquet`, `val.parquet`)：使用 `pyarrow` 寫入具備列式索引結構之資料表。
     - **tw-PII-bench JSONL** (`train_tw_bench.jsonl`, `val_tw_bench.jsonl`)：自動映射至基準評測標籤。
   - 匯出 `summary.json`：包含領域、長度、實體標籤分佈、負樣本佔比、耗時與每秒輸送量（throughput）。
7. **`BatchPipelineOrchestrator` (`orchestrator.py`)**:
   - 統籌六大領域（`HEALTHCARE`, `BANKING_FINANCE`, `TELECOM`, `ECOMMERCE_LOGISTICS`, `REAL_ESTATE`, `LEGAL_CONSULTATION`）與三級長度（`SHORT`, `MID`, `LONG`）之最小代表度貪婪平衡取樣。
   - 精確調配 15% 負樣本配額（50% 純負樣本 + 50% 混雜干擾樣本），覆蓋六大難辨負樣本類別。
   - 實測本機生成輸送量達 **640+ samples/second**。

### 2. CLI 命令擴充 (`main.py`)

新增 `generate-dataset` 子命令：
```bash
python main.py generate-dataset -n 1000 -o data/gliner2_tw --val-ratio 0.20 --negative-ratio 0.15 --seed 42
```
支援參數：
- `-n`, `--count`：生成樣本總量（預設 1000）
- `-o`, `--output-dir`：資料集輸出目錄（預設 `data/gliner2_tw`）
- `--val-ratio`：驗證集比例（預設 0.20）
- `--negative-ratio`：負樣本比例（預設 0.15）
- `--pure-negative-ratio`：純負樣本佔負樣本之比例（預設 0.50）
- `--batch-size`：批次大小（預設 100）
- `--checkpoint-interval`：檢查點儲存間隔（預設 100）
- `--resume`：從現有檢查點接續生成
- `--no-parquet`：停用 Parquet 檔案匯出
- `--export-tw-bench`：額外匯出 tw-PII-bench 格式
- `--rate-limit`：每秒生成速率限制
- `-s`, `--seed`：可重現隨機種子

### 3. 測試與驗證

- 新增 `tests/test_pipeline.py`（共 14 項單元測試，涵蓋 ValidationGate、Deduplicator、RateLimiter、CheckpointManager、DatasetExporter、BatchPipelineOrchestrator 與 CLI Integration）。
- 全庫測試：`uv run pytest` **62 passed in 0.47s**。
- 型別靜態檢查：`uv run mypy src` **Success: no issues found in 30 source files**。

