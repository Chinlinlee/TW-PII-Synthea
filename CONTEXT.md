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



