# 萬筆資料批次生成調度器與儲存匯出管線原型
Type: prototype
Status: open
Blocked by: 03, 04, 05

## Question

如何實作一個高可靠、支援中斷重啟且能穩定產出 10,000+ 筆資料的批次生成管線？
需滿足：
1. 平行呼叫或批次處理與速率限制（Rate limiting）管理。
2. 全流程資料去重（Deduplication）與分佈平衡檢查（確保每種 PII 實體與負樣本皆有足夠覆蓋度）。
3. 嚴格格式校驗器（每一筆資料執行 `assert text[s['start']:s['end']] == s['text']`，檢驗重疊 span 與邊界錯誤）。
4. 匯出為標準 GLiNER2 訓練格式（JSONL）與 Parquet，並自動劃分 Train / Validation 集。
產出管線 CLI 原型腳本。
