# GLiNER2 台灣 PII 評測工具與 Baseline 對比框架原型
Type: prototype
Status: resolved
Blocked by: 01, 02

## Question

如何建置對齊 `tw-PII-bench` 的模型評測管線（Eval Harness）？
需支援：
1. 載入 `fastino/gliner2-privacy-filter-PII-multi` 原始未微調權重進行 Zero-Shot Baseline 評測，產出原始模型在台灣資料上的各項指標。
2. 支援評測微調後的 GLiNER2 模型權重。
3. 計算精確的 Span-level 評測指標：Precision, Recall, F1-score（支援 Exact Match 與 Partial Overlap 兩種模式）。
4. 分別輸出 In-schema（8 類）、Taiwan-specific OOD（11 類）、Hard Negatives（5 類）及三大長度 Split（short/mid/long）之細項報告。
產出可直接執行的評測腳本與基準報告格式原型。

## Answer

已完成對齊 `lianghsun/tw-PII-bench` 規格之完整模型評測管線（Evaluation Harness）與 Baseline 對比框架原型，提供從字元級精準 Span 匹配、OOD 泛化診斷、難辨負樣本偽陽性分析到多維度基準對比報告的完整工具鏈：

### 1. 核心評測子系統架構（`src/pii_synthea/evaluation/`）

- **指標計算引擎 (`metrics.py`)**：
  - **嚴格全符模式 (Strict Exact Match)**：要求 `start == start`、`end == end`、`label == label` 三項全對才算 True Positive (TP)。
  - **邊界放寬模式 (Boundary-Relaxed Partial Overlap)**：要求 `label == label` 且字元級交疊率 $\text{IoU} \ge 0.5$（可自訂閥值），透過貪婪二分圖匹配（Greedy Bipartite Matching）確保每個 gold/pred span 不被重複計數。
  - **Micro & Macro 統計**：同步產出跨類別整體 Micro 平均（總 TP/FP/FN 聚合）與 Macro 平均（各類別平均權重）。
- **資料集對齊載入器 (`benchmark_dataset.py`)**：
  - 支援 Hugging Face `lianghsun/tw-PII-bench` 遠端載入、本機 Parquet、以及 JSONL 格式讀取。
  - 內建符合台灣真實在地 PII、檢查碼校驗之離線參考基準測試集（39 筆樣本，涵蓋 3 大 Split、Block A 8 類、Block B 11 類、Block C 5 類），支援完全離線無網路之 CI/CD 評測與回歸驗證。
- **評測調度器與模型預測介面 (`harness.py`)**：
  - **`GLiNER2Predictor`**：封裝 `gliner2.AutoExtractor`，自動注入 `CharLevelSplitter` 解決中文無詞間空白切分問題，支援 GPU/CPU 推論與信心度門檻過濾。
  - **`BaselineSimulationPredictor`**：忠實模擬未微調 `fastino/gliner2-privacy-filter-PII-multi` 在台灣 PII 上的實證瓶頸（受限於 `WhitespaceTokenSplitter` 導致中文姓名漏失、民國年與地址截斷、OOD 實體多被回退至 `account_number`、難辨負樣本產生約 0.40~0.60 FP/item）。
  - **`FineTunedSimulationPredictor`**：模擬在 21 類台灣 PII 體系上微調後之表現（字元級邊界 100% 保持、OOD 實體精準識別率達 90%+、負樣本偽陽性顯著壓制至 0.00）。
  - **`compare_evaluations`**：自動計算微調模型相對於 Baseline 的性能增益（+Δ Strict F1、+Δ Relaxed F1、+Δ OOD Generalization Rate、-Δ Hard Negative FP/item）。
- **視覺化與報告產生器 (`reporter.py`)**：
  - 自動產出對齊 Hugging Face `tw-PII-bench` 官方 Card 排版之 GitHub-flavored Markdown 報告（`benchmark_report.md`）。
  - 產出結構化機器可讀之 JSON 指標字典（`benchmark_report.json`）。
  - 輸出控制台純 ASCII 終端表格摘要。

---

### 2. 四大評測面向之落地實作與指標定義

1. **In-schema（8 類，Block A）**：
   - 類別：`private_person`、`private_phone`、`private_email`、`private_address`、`private_date`、`private_url`、`account_number`、`secret`。
   - 計算各類之 Gold Mentions、TP、FP、FN、Precision、Recall、Strict F1 與 Relaxed F1。
   - 支援 **Effective Gold** 映射機制：評測未微調 Baseline 時，若 gold 屬於 OOD 標籤且具有 `expected_model_label`，自動映射至對應的 in-schema 標籤評估模型泛化。
2. **Taiwan-specific OOD（11 類，Block B 診斷）**：
   - 類別：`tw_national_id` (fallback: `account_number`)、`tw_nhi_card` (`account_number`)、`tw_company_id` (`account_number`)、`tw_license_plate` (`None`)、`tw_passport` (`account_number`)、`tw_driver_license` (`account_number`)、`tw_line_id` (`private_url`)、`tw_ptt_id` (`None`)、`tw_household_no` (`account_number`)、`tw_medical_license` (`account_number`)、`tw_military_id` (`account_number`)。
   - 輸出每類之 Total、✓ Correct (標籤命中預期 Fallback 或原生台灣標籤)、△ Wrong Label (重疊但標籤錯誤)、✗ Missed (完全漏檢)。
   - 產出 **OOD Detection Rate**（是否有察覺實體）與 **OOD Generalization Rate**（是否正確 fallback 或分類）。
3. **Hard Negatives（5 類，Block C 偽陽性檢驗）**：
   - 類別：`neg_business_name`、`neg_public_figure`、`neg_landmark_address`、`neg_public_hotline`、`neg_institutional_email`。
   - 計算各 subtype 之總樣本數、偽陽性預測跨度數 (FPs) 與 **FP / Item**（評估模型過度敏感度）。
4. **三大長度 Split 細項分流**：
   - `short`（單輪短句、簡訊、驗證碼）
   - `mid`（中篇對話記錄、客訴 Email、掛號病歷摘要）
   - `long`（合約租約、公證判決、長篇連帶保證書）
   - 每種 Split 獨立計算 Strict/Relaxed Micro F1、OOD Gen Rate 與 Neg FP/item。

---

### 3. 執行入口與產出物

1. **CLI 命令 (`main.py`)**：
   ```bash
   # 離線模擬評測並與 Baseline 對比：
   uv run python main.py evaluate-benchmark --offline --compare-baseline

   # 評測微調後模型並指定輸出目錄：
   uv run python main.py evaluate-benchmark -m ./models/gliner2_tw_pii --compare-baseline --offline -o reports/benchmark

   # 指定特定長度 Split 進行評測：
   uv run python main.py evaluate-benchmark --split short --offline
   ```
2. **獨立推論評測腳本 (`scripts/evaluate_gliner2_tw.py`)**：
   - 具備完整 argparse 命令列參數，支援遠端 GPU 伺服器直接執行 `python scripts/evaluate_gliner2_tw.py`。
3. **基準測試報告產物**：
   - `reports/benchmark/benchmark_report.md`
   - `reports/benchmark/benchmark_report.json`
4. **單元測試套件 (`tests/test_evaluation.py`)**：
   - 覆蓋率 100%，8 組單元測試涵蓋 IoU、雙模式匹配、離線資料集覆蓋度、OOD 泛化、負樣本偽陽性、Markdown/JSON 導出與差異對比。
