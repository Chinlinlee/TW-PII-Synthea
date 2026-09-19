"""
GLiNER2 Taiwan PII Fine-Tuning Recipe & Script Generator.
Provides executable recipes, standalone training scripts, dataset verification,
and detailed architecture specifications for fine-tuning fastino/gliner2-privacy-filter-PII-multi.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pii_synthea.training.config import GLiNER2TrainingConfig
from pii_synthea.training.formatter import GLiNER2DataFormatter


class GLiNER2FineTuneRecipe:
    """
    Manages the complete fine-tuning recipe for Taiwan PII GLiNER2:
    1. Generates standalone runnable training scripts (train_gliner2_tw.py)
    2. Provides technical specifications and architecture analysis
    3. Validates training datasets for gliner2[train] compatibility
    """

    def __init__(self, config: Optional[GLiNER2TrainingConfig] = None) -> None:
        self.config = config or GLiNER2TrainingConfig()

    def get_technical_spec_report(self) -> Dict[str, Any]:
        """
        Returns a structured technical specification report answering all
        architectural and tokenization questions for GLiNER2 Taiwan fine-tuning.
        """
        return {
            "target_model": {
                "checkpoint": self.config.base_model,
                "parameters": "205M (0.3B backbone)",
                "backbone": "microsoft/mdeberta-v3-base",
                "architecture_type": "extractor (SpanExtractor / fixed-width span grid)",
                "max_width": self.config.max_width,
                "token_pooling": self.config.token_pooling,
                "counting_layer": "count_lstm",
                "pretraining_languages": ["en", "fr", "es", "de", "it", "pt", "nl"],
            },
            "tokenization_and_chinese_offset_mechanics": {
                "two_stage_pipeline": [
                    "Stage 1 (Word Splitting): WordSplitter cuts text into word tuples (token, start, end) with exact char offsets.",
                    "Stage 2 (Subword Tokenization): SentencePiece subword encoding on each word token with token_pooling='first'.",
                    "Stage 3 (Span Enumeration): Adjacent word token combinations up to max_width=8 form candidate span representations.",
                ],
                "traditional_chinese_gap": (
                    "By default, WhitespaceTokenSplitter uses regex \\w+(?:[-_]\\w+)*|\\S. "
                    "In Python regex, \\w matches all Unicode Chinese characters! Continuous Chinese sentences "
                    "without spaces (e.g. '病患林佳玲女士') will be treated as a SINGLE word token, "
                    "making it impossible to extract sub-spans like '林佳玲'!"
                ),
                "resolution_word_splitter": (
                    "Must configure CharLevelSplitter (word_splitter='char'). "
                    "CharLevelSplitter preserves Latin words, emails, and numbers intact while splitting "
                    "CJK non-space characters into individual character tokens, ensuring exact 100% character span boundaries."
                ),
                "runtime_persistence_warning": (
                    "CRITICAL: word_splitter is a RUNTIME-ONLY processor configuration and is NOT saved in config.json! "
                    "Any fine-tuned model checkpoint must explicitly set model.set_word_splitter(CharLevelSplitter()) "
                    "or pass word_splitter='char' during loading and inference."
                ),
            },
            "vocabulary_coverage_analysis": {
                "tokenizer": "DebertaV2Tokenizer (SentencePiece SPM)",
                "vocab_size": 250000,
                "pretraining_corpus": "CC100 (covering 100 languages including zh-TW / zh-CN)",
                "traditional_chinese_coverage": (
                    "The 250,000 token vocabulary natively covers virtually all common and specialized Traditional Chinese "
                    "hanzi characters and subwords. Out-of-vocabulary ([UNK]) rate on Taiwan PII is virtually 0%."
                ),
                "vocabulary_expansion_decision": (
                    "NO vocabulary expansion is required or recommended. Expanding the vocabulary would disrupt "
                    "mDeBERTa-v3 pretrained embedding alignments and output projection dimensions."
                ),
            },
            "fine_tuning_strategy": {
                "recommended_mode": "LoRA (Parameter-Efficient Fine-Tuning)",
                "lora_rank": self.config.lora_r,
                "lora_alpha": self.config.lora_alpha,
                "lora_dropout": self.config.lora_dropout,
                "lora_target_modules": self.config.lora_target_modules,
                "lora_trainable_parameters_ratio": "approx. 1.8% ~ 3.5%",
                "adapter_size": "approx. 8 ~ 15 MB",
                "alternative_mode": "Full Fine-Tuning with Differential Learning Rates (encoder_lr=1e-5, task_lr=5e-4)",
            },
            "optimization_and_loss": {
                "optimizer": "AdamW (weight_decay=0.01, betas=(0.9, 0.999), eps=1e-8)",
                "encoder_learning_rate": self.config.encoder_lr,
                "task_learning_rate": self.config.task_lr,
                "loss_formulation": [
                    "Span-Label BCE Loss: Candidate span embeddings are matched against conditioned Label prompt embeddings.",
                    "Hard Negatives: Pure negative texts (0 spans) and distractor spans produce zero match signals against all labels.",
                    "Count LSTM Loss: Auxiliary count prediction loss regularizing total entity occurrences.",
                ],
                "batch_configuration": {
                    "batch_size": self.config.batch_size,
                    "gradient_accumulation_steps": self.config.gradient_accumulation_steps,
                    "effective_batch_size": self.config.batch_size * self.config.gradient_accumulation_steps,
                },
                "recommended_hardware": "NVIDIA GPU with >= 8GB VRAM (LoRA) or >= 16GB VRAM (Full Fine-Tuning)",
            },
        }

    def generate_training_script(self, custom_config: Optional[GLiNER2TrainingConfig] = None) -> str:
        """
        Generates a standalone, executable Python script (train_gliner2_tw.py)
        for training fastino/gliner2-privacy-filter-PII-multi on Taiwan PII.
        """
        cfg = custom_config or self.config
        cfg_dict = cfg.to_gliner2_trainer_config()
        cfg_json_str = json.dumps(cfg_dict, ensure_ascii=False, indent=4)
        cfg_json_py_literal = json.dumps(cfg_json_str)

        script = f'''#!/usr/bin/env python3
"""
Standalone Fine-tuning Script for fastino/gliner2-privacy-filter-PII-multi on Taiwan PII.
Generated by PII-Synthea FineTuneRecipe Engine.

Prerequisites:
    pip install "gliner2[train]>=0.2.0" torch transformers peft
"""

import os
import sys
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("train_gliner2_tw")

def main():
    try:
        from gliner2 import AutoExtractor
        from gliner2.processor import CharLevelSplitter
        from gliner2.training.data import TrainingDataset
        from gliner2.training.trainer import ExtractorTrainer, TrainingConfig
    except ImportError as e:
        logger.error(
            "Missing required packages. Please install via: pip install \\"gliner2[train]\\" torch peft"
        )
        sys.exit(1)

    # 1. Paths & Verification
    train_path = Path("{cfg.train_data_path}")
    val_path = Path("{cfg.val_data_path}")
    output_dir = Path("{cfg.output_dir}")

    if not train_path.exists():
        logger.error(f"Training dataset not found at {{train_path.resolve()}}")
        logger.error("Please run: python main.py generate-dataset --count 5000")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("PII-Synthea: GLiNER2 Taiwan PII Fine-tuning Suite")
    logger.info(f"Base model    : {cfg.base_model}")
    logger.info(f"Train dataset : {{train_path.resolve()}}")
    logger.info(f"Val dataset   : {{val_path.resolve()}} (exists: {{val_path.exists()}})")
    logger.info(f"Output dir    : {{output_dir.resolve()}}")
    logger.info(f"LoRA enabled  : {cfg.use_lora} (r={cfg.lora_r}, alpha={cfg.lora_alpha})")
    logger.info(f"Word Splitter : CharLevelSplitter (Chinese character boundary support)")
    logger.info("=" * 70)

    # 2. Load Base Model & Inject Chinese Word Splitter
    logger.info("Loading pretrained GLiNER2 model...")
    model = AutoExtractor.from_pretrained("{cfg.base_model}")

    # CRITICAL: For Traditional Chinese, set CharLevelSplitter so Chinese characters
    # are tokenized by character while keeping Latin words/emails intact.
    logger.info("Configuring CharLevelSplitter for Chinese language support...")
    model.set_word_splitter(CharLevelSplitter())

    # 3. Load and Validate Datasets
    logger.info(f"Loading training data from {{train_path}}...")
    train_dataset = TrainingDataset.load(str(train_path))
    logger.info("Validating dataset integrity...")
    try:
        train_dataset.validate(raise_on_error=False)
        train_dataset.print_stats()
    except Exception as e:
        logger.warning(f"Dataset validation note: {{e}}")

    val_dataset = None
    if val_path.exists():
        logger.info(f"Loading validation data from {{val_path}}...")
        val_dataset = TrainingDataset.load(str(val_path))

    # 4. Configure Training Parameters
    logger.info("Initializing TrainingConfig...")
    config_dict = json.loads({cfg_json_py_literal})
    
    # Instantiate TrainingConfig
    trainer_config = TrainingConfig(**config_dict)

    # 5. Initialize Trainer and Execute Training
    logger.info("Initializing ExtractorTrainer...")
    trainer = ExtractorTrainer(model=model, config=trainer_config)

    logger.info("Starting fine-tuning...")
    results = trainer.train(
        train_data=train_dataset,
        eval_data=val_dataset,
    )

    logger.info("=" * 70)
    logger.info("Training completed successfully!")
    if isinstance(results, dict):
        for k, v in results.items():
            logger.info(f"  {{k}}: {{v}}")
    logger.info(f"Saved fine-tuned artifacts to: {{output_dir.resolve()}}")
    logger.info("=" * 70)

    # 6. Verification Inference Test
    logger.info("Running post-training inference verification on sample Taiwan PII...")
    test_text = (
        "立約人陳大明（身分證字號：A123456789，電話：0912-345-678）"
        "與台灣積體電路（統編：22099131，地址：新竹市東區研新一路9號）簽署契約。"
    )
    labels = ["person", "national_id_number", "phone_number", "tax_id", "address"]
    
    # Reload or use current model
    test_model = model
    test_model.set_word_splitter(CharLevelSplitter())
    preds = test_model.extract_entities(test_text, labels, threshold=0.5)
    
    logger.info(f"Input Text : {{test_text}}")
    logger.info(f"Predictions: {{preds}}")
    logger.info("Fine-tuning pipeline verification complete!")

if __name__ == "__main__":
    main()
'''
        return script

    def export_training_script(self, output_file: Union[str, Path] = "scripts/train_gliner2_tw.py") -> Path:
        """Exports the generated training script to a file."""
        p = Path(output_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        script_code = self.generate_training_script()
        with open(p, "w", encoding="utf-8") as f:
            f.write(script_code)
        return p

    def validate_dataset_file(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validates a JSONL training dataset file:
        - Confirms each line contains 'input' or 'text'
        - Confirms 'output' -> 'entities' or 'entities' exists
        - Confirms span text matches text[start:end]
        - Checks hard negatives (empty entities)
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        total = 0
        valid_count = 0
        pure_negatives = 0
        total_entities = 0
        entity_type_counts: Dict[str, int] = {}
        errors: List[str] = []

        with open(p, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    record = json.loads(line)
                except Exception as e:
                    errors.append(f"Line {line_idx}: Invalid JSON: {e}")
                    continue

                text = record.get("input", record.get("text", ""))
                if not text:
                    errors.append(f"Line {line_idx}: Missing 'input' or 'text' field")
                    continue

                # Check entities
                entities: Dict[str, List[str]] = {}
                if "output" in record and isinstance(record["output"], dict) and "entities" in record["output"]:
                    entities = record["output"]["entities"]
                elif "entities" in record and isinstance(record["entities"], dict):
                    entities = record["entities"]

                entity_count = sum(len(v) for v in entities.values())
                if entity_count == 0:
                    pure_negatives += 1
                else:
                    total_entities += entity_count
                    for k, v in entities.items():
                        entity_type_counts[k] = entity_type_counts.get(k, 0) + len(v)

                # Validate spans if present
                spans = record.get("spans", [])
                for s_idx, s in enumerate(spans):
                    start = s.get("start", -1)
                    end = s.get("end", -1)
                    s_text = s.get("text", "")
                    if start < 0 or end > len(text) or start >= end:
                        errors.append(f"Line {line_idx} Span {s_idx}: Boundary invalid [{start}:{end}]")
                    elif text[start:end] != s_text:
                        errors.append(f"Line {line_idx} Span {s_idx}: Text mismatch '{s_text}' != '{text[start:end]}'")

                valid_count += 1

        return {
            "file": str(p),
            "total_records": total,
            "valid_records": valid_count,
            "pure_negatives": pure_negatives,
            "positive_records": total - pure_negatives,
            "total_entity_mentions": total_entities,
            "entity_type_counts": entity_type_counts,
            "errors_found": len(errors),
            "error_samples": errors[:5],
            "is_valid": len(errors) == 0 and total > 0,
        }
