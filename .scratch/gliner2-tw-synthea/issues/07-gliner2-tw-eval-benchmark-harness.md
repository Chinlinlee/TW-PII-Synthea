# GLiNER2 台灣 PII 評測工具與 Baseline 對比框架原型
Type: prototype
Status: open
Blocked by: 01, 02

## Question

如何建置對齊 `tw-PII-bench` 的模型評測管線（Eval Harness）？
需支援：
1. 載入 `fastino/gliner2-privacy-filter-PII-multi` 原始未微調權重進行 Zero-Shot Baseline 評測，產出原始模型在台灣資料上的各項指標。
2. 支援評測微調後的 GLiNER2 模型權重。
3. 計算精確的 Span-level 評測指標：Precision, Recall, F1-score（支援 Exact Match 與 Partial Overlap 兩種模式）。
4. 分別輸出 In-schema（8 類）、Taiwan-specific OOD（11 類）、Hard Negatives（5 類）及三大長度 Split（short/mid/long）之細項報告。
產出可直接執行的評測腳本與基準報告格式原型。
