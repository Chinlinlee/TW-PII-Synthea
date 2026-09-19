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
