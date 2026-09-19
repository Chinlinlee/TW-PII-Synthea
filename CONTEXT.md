# CONTEXT

## Glossary

### PII (Personally Identifiable Information / 個人資料)
Information that can be used to distinguish or trace an individual's identity, either alone or when combined with other personal or identifying information. In the Taiwan context, this includes national identification numbers, health insurance card numbers, unified business numbers (when identifying sole proprietors), phone numbers, addresses, personal names, dates of birth, etc.

### PII-Synthea
The synthetic PII dataset generator engine specifically designed for Traditional Chinese (Taiwan locale). It generates high-fidelity text containing realistic Taiwan PII with exact character-level span annotations.

### Span
A character-level continuous text slice defined by zero-indexed `[start, end]` boundaries within the source text, along with its associated PII `label`.

### GLiNER2
A schema-conditioned bidirectional transformer encoder model architecture designed for named entity recognition and structured information extraction. It extracts entities based on prompt-specified label embeddings.

### Target Model (`fastino/gliner2-privacy-filter-PII-multi`)
A 205M parameter multilingual PII detection model supporting 42 entity labels across 7 European languages. The objective of `PII-Synthea` is to synthesize Taiwan PII training data to fine-tune this model into a Taiwan (`zh-TW`) variant.

### Hard Negative
Text that exhibits linguistic, structural, or lexical similarity to personal data (such as restaurant names containing personal names, landmark addresses, or public government emergency hotlines) but must NOT be labeled as PII, used to prevent false positives.

### Canonical Taxonomy (標籤體系)
The 21-entity unified schema defined in `src/pii_synthea/taxonomy.py` and `schema.json`. It bridges GLiNER2's 42 native multilingual labels with Taiwan's legal and cultural PII definitions, providing prompt descriptions in both English and Traditional Chinese.

### Taiwan Extension Labels (台灣在地專屬標籤)
The subset of entities not natively present in GLiNER2's 42 classes but vital in Taiwan workflows: `tw_nhi_card` (健保卡), `license_plate` (車牌), `tw_line_id` (LINE ID), `tw_ptt_id` (PTT 帳號), `tw_household_no` (戶號), `tw_medical_license` (醫事證照字號), and `tw_military_id` (軍人證號).

### Deterministic PII Generator (演算法校驗生成器)
The programmatic entity generation subsystem under `src/pii_synthea/generators/` that produces algorithmically valid Taiwan PII: National IDs with county letter weights and check digits, New and Old ARCs, 8-digit Unified Business Numbers with MOF mod 10 / mod 5 logic, Luhn-valid credit cards, 368 official township postal codes, authentic Taiwanese surnames/given names/indigenous names, and realistic phone numbers.

### Offset Preservation Engine (位移保全與 Span 校驗引擎)
The character-level offset management architecture implemented in `TemplateEngine`, `SpanReplacer`, and `SynthesisResult`. It guarantees 100% boundary fidelity by calculating exact `[start, end]` boundaries across variable-length substitutions, enforcing non-overlapping constraints, and asserting `text[start:end] == span.text` prior to emitting GLiNER2 training examples.

### Domain Scenarios (在地領域場景矩陣)
The 6 canonical industry and situational domains implemented under `src/pii_synthea/scenarios/domains.py`: Healthcare (醫療院所與公衛), Banking & Finance (金融銀行與支付), Telecom (電信通訊與資費), E-commerce & Logistics (網購電商與物流配送), Real Estate (租屋不動產與物業), and Legal Consultation (法律諮詢與民事調解).

### Text Length Distribution (文本篇幅分佈)
The three length distribution tiers modeled in `TextLengthCategory`:
- `short` (15–120 chars): Customer service single turns, SMS notifications, transaction OTP/alerts, delivery notifications.
- `mid` (200–1000 chars): LINE chat transcripts, complaint emails, registration forms, inquiry dialogues.
- `long` (1500–5000 chars): Comprehensive hospital discharge summaries, residential lease agreements, commercial mortgage contracts, and certified legal arbitration transcripts.

### TagToSpanParser (標籤位移解析引擎)
The XML extraction subsystem implemented in `src/pii_synthea/scenarios/tag_parser.py`. It strips enclosing (`<label>text</label>`), indexed (`<label:1>`), self-closing, and mustache tags, computes exact zero-indexed character offsets in clean text, asserts boundary integrity, and optionally normalizes hallucinated entities into algorithmically valid Taiwan PII.

### ScenarioSynthesizer (情境合成編排器)
The unified pipeline controller implemented in `src/pii_synthea/scenarios/generator.py`. It connects `SeedTemplateLibrary`, `PromptBuilder`, `TagToSpanParser`, and `TemplateEngine` to generate single or batch synthetic datasets with distribution control, exporting directly to GLiNER2 JSONL or `tw-PII-bench` format.

### CharLevelSplitter (中文分詞與邊界保全器)
The character-level token splitting policy required by GLiNER2 when processing continuous Traditional Chinese text without inter-word whitespace. It ensures Chinese text is tokenized per-character (preventing multi-character phrases from collapsing into a single word token) while keeping Latin words, emails, and phone digits contiguous. Because `word_splitter` is a runtime-only attribute not saved in checkpoint `config.json`, it must be explicitly injected via `model.set_word_splitter(CharLevelSplitter())` during fine-tuning and inference.

### GLiNER2FineTuneRecipe (GLiNER2 微調配方與腳本引擎)
The end-to-end training management subsystem implemented in `src/pii_synthea/training/`. It defines standard training parameters (differential learning rates: `encoder_lr=1e-5`, `task_lr=5e-4`), LoRA target modules (`encoder`, `span_rep`, `classifier`, `count_embed`, `count_pred`), and generates standalone executable training scripts (`scripts/train_gliner2_tw.py`) alongside dual-compatible dataset formats (`{"input": ..., "output": {"entities": ...}}` + exact spans).

### EvaluationHarness (評測工具與對比框架)
The benchmark evaluation and regression testing framework implemented under `src/pii_synthea/evaluation/`. It executes zero-shot baseline and fine-tuned model evaluation against `lianghsun/tw-PII-bench`, calculating strict exact match and boundary-relaxed (IoU) span metrics, Taiwan OOD detection/generalization, and hard negative false positive rates across `short`, `mid`, and `long` splits.

### tw-PII-bench (台灣在地 PII 客觀評測基準)
The gold standard Taiwan PII detection benchmark developed by Liang Hsun Huang (`lianghsun/tw-PII-bench`), structured into 3 length tiers (`short`, `mid`, `long`) across 3 core blocks:
- **Block A (In-schema)**: 8 canonical PII classes (`private_person`, `private_phone`, `private_email`, `private_address`, `private_date`, `private_url`, `account_number`, `secret`).
- **Block B (Taiwan OOD)**: 11 Taiwan-specific PII classes with defined fallback labels (`tw_national_id`, `tw_nhi_card`, `tw_company_id`, `tw_license_plate`, `tw_passport`, `tw_driver_license`, `tw_line_id`, `tw_ptt_id`, `tw_household_no`, `tw_medical_license`, `tw_military_id`).
- **Block C (Hard Negatives)**: 5 confusing distractor subtypes (`neg_business_name`, `neg_public_figure`, `neg_landmark_address`, `neg_public_hotline`, `neg_institutional_email`) containing zero true PII spans.

### Effective Gold (有效基準標籤與 Fallback 映射)
The benchmark evaluation convention where Out-of-Distribution (OOD) ground-truth spans are mapped to their `expected_model_label` (e.g. `tw_national_id` mapped to `account_number`) when calculating in-schema F1 against un-fine-tuned baseline models whose taxonomy lacks native Taiwan labels. OOD entities without fallback (`tw_license_plate`, `tw_ptt_id`) are excluded from effective in-schema scoring and evaluated purely in the OOD diagnostic block.




