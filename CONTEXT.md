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


