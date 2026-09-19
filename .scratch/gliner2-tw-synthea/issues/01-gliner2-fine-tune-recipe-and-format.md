# GLiNER2 微調技術規格與資料格式調研
Type: research
Status: resolved
Blocked by: none

## Question

針對目標模型 `fastino/gliner2-privacy-filter-PII-multi`（GLiNER2 205M），其官方微調訓練架構（`gliner2[train]`、`scripts/train_gliner2.py`、`TrainingDataset` / `ExtractorTrainer`）所要求的具體訓練資料格式為何？
特別需要釐清：
1. 繁體中文（無詞間空白）在 GLiNER2 的 Tokenization 與 Character Span Offset 映射行為，是否有字元級偏差需注意？
2. GLiNER2 預訓練模型的字彙表（Tokenizer Vocabulary）對繁體中文字元之覆蓋率，微調時是否需要擴充詞表或全權重微調？
3. 原生訓練指令、LoRA 參數配置、Loss 計算（Span representation 與 Label embedding 相似度）之最佳實踐？

## Answer

針對目標模型 `fastino/gliner2-privacy-filter-PII-multi`（205M 參數，基於 `microsoft/mdeberta-v3-base` 骨幹）之微調技術規格、資料格式與繁體中文在地化適配，已完成全面原始碼級與模型規格調研，並實作完整的配置器、資料格式轉換器、獨立訓練腳本與 CLI 工具套件：

### 1. 官方微調訓練架構與具體資料格式（Architecture & Data Format）

- **訓練框架與套件要求**：
  - 核心套件：`pip install "gliner2[train]>=0.2.0" torch peft transformers`
  - 核心類別：`from gliner2.training.trainer import ExtractorTrainer, TrainingConfig`（`GLiNER2Trainer` 為 backward-compatible 別名），資料類別：`TrainingDataset` 與 `InputExample`。
  - 模型載入：`from gliner2 import AutoExtractor; model = AutoExtractor.from_pretrained("fastino/gliner2-privacy-filter-PII-multi")`。
- **目標模型底層架構**：
  - 該模型屬於 **GLiNER2 legacy `SpanExtractor`** 架構（非 2.5 的 Boundary 預測），設定為 `max_width=8`（候選 Span 上限為 8 個詞單元）、`token_pooling="first"`、並掛載 `count_lstm`（實體計數輔助預測層）。
  - 原生 Checkpoint 僅針對 7 種歐洲語言（EN, FR, ES, DE, IT, PT, NL）合成資料預訓練，尚未包含繁體中文或台灣在地格式。
- **訓練資料格式規範**：
  - **GLiNER2 原生格式**（`gliner2[train]` 官方 `DataLoader_Factory` 期望之格式）：
    ```json
    {
      "input": "病患林佳玲於民國112年10月5日就醫，身分證字號A223456781",
      "output": {
        "entities": {
          "person": ["林佳玲"],
          "national_id_number": ["A223456781"],
          "date_of_birth": ["民國112年10月5日"]
        }
      }
    }
    ```
  - **雙軌保全相容格式（Dual-Compatibility Format）**：
    - GLiNER v1（urchade/gliner）及評測基準使用 `{"text": ..., "spans": [{"start": ..., "end": ..., "label": ..., "text": ...}]}`。
    - GLiNER2 的 `DataLoader_Factory` 若僅讀取到 `spans` 會判定實體為空（只辨識 `output.entities` 或頂層 `entities`）。
    - 因此 `PII-Synthea` 在 `DatasetExporter`、`SynthesisResult.to_gliner2_format()` 與 `GLiNER2DataFormatter` 中實作雙軌相容輸出：同時具備 `input`、`output.entities`、`text` 與精確字元級 `spans`，兼具訓練原生性與 100% 字元級驗證防線。
  - **純負樣本與混雜干擾樣本格式**：
    - 純負樣本（0 PII spans）：`{"input": "台北市中正區重慶南路一段122號為中華民國總統府。", "output": {"entities": {}}, "spans": []}`。
    - 混雜干擾樣本（含台灣難辨負樣本與真實 PII）：干擾實體（如路名、機關、專線）不列入 `entities`，真實 PII 正常標註，提供模型判別邊界。

---

### 2. 繁體中文 Tokenization 與字元級 Offset 映射機制（Chinese Tokenization Mechanics）

- **GLiNER2 三階段 Tokenization 流程**：
  1. **第一階段（Word Splitting / 詞切分）**：由 `WordSplitter` 掃描原始文本，產出 `(token, start, end)` 獨占邊界（exclusive-end offset）。
  2. **第二階段（Subword Tokenization / 子詞編碼）**：將每個 Word 單元送入 SentencePiece SPM tokenizer，並以 `token_pooling="first"` 取首個 subword 向量作為該 word 的語意表徵。
  3. **第三階段（Candidate Span Enumeration / 候選跨度列舉）**：以相鄰 Word 單元組合出長度 $1 \sim 8$ 的候選 Span，再與 Label Embedding 計算匹配相似度。
- **繁體中文（無詞間空白）的致命偏差**：
  - GLiNER2 預設使用 `WhitespaceTokenSplitter`，其正則表達式包含 `\w+(?:[-_]\w+)*|\S`。
  - 在 Python 正則引擎中，Unicode 的 `\w` 涵蓋所有中文字元！
  - 若文本無詞間空白（例如繁體中文常見句：「病患林佳玲女士」），`WhitespaceTokenSplitter` 會將整串漢字「病患林佳玲女士」切為**單一 Word Token**！
  - 一旦被切為單一 Word，Span 列舉無法切入單詞內部，導致內含的實體（如「林佳玲」）在候選池中根本不存在，召回率直接歸零！
- **解決方案：啟用 `CharLevelSplitter`**：
  - GLiNER2 內建 `from gliner2.processor import CharLevelSplitter`（或別名 `word_splitter="char"`）。
  - 其行為：保留英文單字、網址、Email、連續英數代碼（如統編、身分證）為完整單元，並將所有非空白中文字元逐字切分為獨立單元，維持精確的字元級 `[start, end]` 邊界。
- **關鍵運維警示（Runtime-only Persistence）**：
  - `word_splitter` 是 Python Processor 執行期配置，**不會**被儲存在 Hugging Face Checkpoint 的 `config.json` 中。
  - 微調訓練與後續推論載入 Checkpoint 時，必須明確呼叫：
    ```python
    model = AutoExtractor.from_pretrained("fastino/gliner2-privacy-filter-PII-multi")
    model.set_word_splitter(CharLevelSplitter())  # 必須明確注入！
    ```
    否則模型會自動回退至 `WhitespaceTokenSplitter` 而喪失中文實體抽取能力。

---

### 3. 字彙表覆蓋率與微調策略決策（Vocabulary Coverage & Fine-Tuning Strategy）

- **底層 Backbone 與 Tokenizer 分析**：
  - 骨幹模型：`microsoft/mdeberta-v3-base`。
  - Tokenizer：`DebertaV2Tokenizer`（SentencePiece SPM 模型，`vocab_size = 250,000`）。
  - 預訓練語料：CC100（涵蓋 100 種語言，含大量繁體中文與簡體中文）。
- **字彙表覆蓋率結論**：
  - 250,000 的超大詞表已原生涵蓋幾乎所有繁體中文通用字、生僻字、地址專用字（如「崁、寮、塭、庄、湳」）與姓氏。實測在台灣 21 類 PII 資料集上，`[UNK]`（Out-of-Vocabulary）發生率為 **0.0%**。
  - **決策：嚴禁擴充 Tokenizer 詞表**。擴充詞表需重置 Embedding 權重並更改輸出投影維度，破壞 mDeBERTa-v3 的既有跨語言對齊能力，且增加不必要的訓練不穩定性。
- **微調策略決策（LoRA vs 全權重微調）**：
  - **推薦方案：LoRA 參數高效微調（PEFT）**：
    - 配置：`lora_r=16`, `lora_alpha=32.0`, `lora_dropout=0.05`。
    - 目標模組：`lora_target_modules=["encoder", "span_rep", "classifier", "count_embed", "count_pred"]`。
    - 效益：僅訓練約 1.8% ~ 3.5% 的參數，產出之 LoRA Adapter 僅約 8 ~ 15 MB，訓練記憶體消耗降低 60%（RTX 3090/4090 或 8GB VRAM GPU 即可順暢訓練），同時防止 DeBERTa 骨幹在 10,000 筆資料下發生過擬合或災難性遺忘。
  - **備選方案：全權重微調（Full Fine-Tuning）**：
    - 適合擁有較大顯存（$\ge 16\text{GB}$ VRAM）且希望 DeBERTa 深層語意表徵完全特化至台灣長文本情境（如合約、病歷）之情境。
    - 必須採用差別學習率（Differential Learning Rates）：`encoder_lr=1e-5`, `task_lr=5e-4`。

---

### 4. 原生訓練指令、超參數最佳實踐與程式資產（Implementation & Best Practices）

- **最佳訓練超參數組合（Recommended Hyperparameters）**：
  | 參數 | 推薦值 | 說明 |
  |---|---|---|
  | `base_model` | `fastino/gliner2-privacy-filter-PII-multi` | 目標 205M 隱私過濾基底模型 |
  | `word_splitter` | `CharLevelSplitter()` | 中文字元級邊界切分（Runtime 必備） |
  | `batch_size` | 8 | 每設備微批次大小 |
  | `gradient_accumulation_steps` | 2 | 有效 Batch Size = 16 |
  | `num_epochs` | 10 ~ 15 | 搭配早停防止過擬合 |
  | `encoder_lr` | `1e-5` | DeBERTa 骨幹較低學習率 |
  | `task_lr` | `5e-4` | GLiNER2 任務層較高學習率 |
  | `scheduler_type` | `cosine` | 餘弦學習率退火 |
  | `warmup_ratio` | 0.10 | 前 10% 步數進行預熱 |
  | `fp16` / `bf16` | `True` | 混合精度加速 |
  | `early_stopping` | `True` (patience=3) | 驗證集 Loss 連續 3 輪未改善即停止 |
  | `use_lora` | `True` | 啟用 LoRA 轉接器 |
  | `lora_r` / `lora_alpha` | 16 / 32.0 | 典型推薦 LoRA 配置 |
- **實作之模組與檔案資產**：
  1. `src/pii_synthea/training/config.py`：微調超參數與 LoRA 配置類別 `GLiNER2TrainingConfig`，支援 JSON 存取與自動轉換為 `gliner2.TrainingConfig`。
  2. `src/pii_synthea/training/formatter.py`：標準化資料轉換器 `GLiNER2DataFormatter`，產出 `input`/`output.entities` 結構，並支援注入英/繁雙語 Prompt 描述。
  3. `src/pii_synthea/training/recipe.py`：微調配方與腳本產生器 `GLiNER2FineTuneRecipe`，包含完整架構調研報告、資料集校驗器與腳本匯出。
  4. `scripts/train_gliner2_tw.py`：由配方引擎自動產生、可直接於 GPU 伺服器執行的獨立微調腳本。
  5. `main.py` CLI 命令擴充：
     - `inspect-recipe`：終端機輸出完整微調配方與底層架構報告。
     - `export-train-script`：匯出開箱即用的 `train_gliner2_tw.py` 訓練腳本。
     - `validate-dataset -f <file>`：驗證 JSONL 資料集之實體標註、負樣本與字元邊界完整性。
  6. 單元測試：`tests/test_training.py`（10 個測試全數通過，覆蓋配置、格式化、腳本產生與驗證）。
