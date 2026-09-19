# GLiNER2 微調技術規格與資料格式調研
Type: research
Status: open
Blocked by: none

## Question

針對目標模型 `fastino/gliner2-privacy-filter-PII-multi`（GLiNER2 205M），其官方微調訓練架構（`gliner2[train]`、`scripts/train_gliner2.py`、`TrainingDataset` / `ExtractorTrainer`）所要求的具體訓練資料格式為何？
特別需要釐清：
1. 繁體中文（無詞間空白）在 GLiNER2 的 Tokenization 與 Character Span Offset 映射行為，是否有字元級偏差需注意？
2. GLiNER2 預訓練模型的字彙表（Tokenizer Vocabulary）對繁體中文字元之覆蓋率，微調時是否需要擴充詞表或全權重微調？
3. 原生訓練指令、LoRA 參數配置、Loss 計算（Span representation 與 Label embedding 相似度）之最佳實踐？
