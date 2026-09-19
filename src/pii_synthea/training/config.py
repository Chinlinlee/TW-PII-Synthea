"""
GLiNER2 Taiwan PII Fine-tuning Configuration.
Defines hyperparameters, LoRA adapter configs, differential learning rates,
and runtime tokenization policies for fastino/gliner2-privacy-filter-PII-multi.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GLiNER2TrainingConfig:
    """
    Configuration for fine-tuning fastino/gliner2-privacy-filter-PII-multi on Taiwan PII.
    
    Covers:
    - Base model selection & runtime Chinese word-splitter policy
    - LoRA adapter parameters (rank, alpha, dropout, target modules)
    - Differential learning rates (encoder_lr vs task_lr)
    - Batching, mixed precision, and early stopping
    """

    # Model & Architecture
    base_model: str = "fastino/gliner2-privacy-filter-PII-multi"
    model_type: str = "extractor"  # SpanExtractor legacy architecture
    max_width: int = 8             # Max span candidate width in words/chars
    token_pooling: str = "first"   # Pool first subtoken representation
    word_splitter: str = "char"    # Critical for Traditional Chinese: CharLevelSplitter

    # Dataset paths
    train_data_path: str = "data/gliner2_tw/train.jsonl"
    val_data_path: str = "data/gliner2_tw/val.jsonl"
    output_dir: str = "./models/gliner2_tw_pii"
    experiment_name: str = "gliner2_tw_pii_finetune"

    # Training Schedule & Optimization
    num_epochs: int = 10
    max_steps: int = -1
    batch_size: int = 8
    eval_batch_size: int = 8
    gradient_accumulation_steps: int = 2  # Effective batch size = 16
    encoder_lr: float = 1e-5             # Lower LR for pretrained mDeBERTa backbone
    task_lr: float = 5e-4                # Higher LR for span representation & classifiers
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    scheduler_type: str = "cosine"
    warmup_ratio: float = 0.1
    warmup_steps: int = 0

    # Precision & Performance
    fp16: bool = True
    bf16: bool = False
    group_by_length: bool = True
    max_len: Optional[int] = None
    gradient_checkpointing: bool = False
    num_workers: int = 4
    pin_memory: bool = True
    seed: int = 42

    # Evaluation & Checkpointing
    eval_strategy: str = "epoch"         # "epoch" or "steps"
    eval_steps: int = 250
    save_best: bool = True
    metric_for_best: str = "eval_loss"
    greater_is_better: bool = False
    save_total_limit: int = 3
    early_stopping: bool = True
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.001

    # Parameter-Efficient Fine-Tuning (LoRA)
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: float = 32.0
    lora_dropout: float = 0.05
    lora_use_dora: bool = False
    lora_target_modules: List[str] = field(
        default_factory=lambda: [
            "encoder",
            "span_rep",
            "classifier",
            "count_embed",
            "count_pred",
        ]
    )
    save_adapter_only: bool = True

    # Prompt schema enhancement
    include_descriptions: bool = True    # Include bilingual prompt descriptions during training

    # Telemetry & Logging
    logging_steps: int = 10
    report_to_wandb: bool = False
    wandb_project: Optional[str] = "gliner2-tw-pii"

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration to standard dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GLiNER2TrainingConfig:
        """Instantiates configuration from dictionary."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_gliner2_trainer_config(self) -> Dict[str, Any]:
        """
        Converts to the dictionary expected by gliner2.training.trainer.TrainingConfig.
        """
        return {
            "output_dir": self.output_dir,
            "experiment_name": self.experiment_name,
            "num_epochs": self.num_epochs,
            "max_steps": self.max_steps,
            "batch_size": self.batch_size,
            "eval_batch_size": self.eval_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "encoder_lr": self.encoder_lr,
            "task_lr": self.task_lr,
            "weight_decay": self.weight_decay,
            "max_grad_norm": self.max_grad_norm,
            "scheduler_type": self.scheduler_type,
            "warmup_ratio": self.warmup_ratio,
            "warmup_steps": self.warmup_steps,
            "fp16": self.fp16,
            "bf16": self.bf16,
            "eval_strategy": self.eval_strategy,
            "eval_steps": self.eval_steps,
            "save_best": self.save_best,
            "metric_for_best": self.metric_for_best,
            "greater_is_better": self.greater_is_better,
            "save_total_limit": self.save_total_limit,
            "early_stopping": self.early_stopping,
            "early_stopping_patience": self.early_stopping_patience,
            "early_stopping_threshold": self.early_stopping_threshold,
            "num_workers": self.num_workers,
            "pin_memory": self.pin_memory,
            "seed": self.seed,
            "group_by_length": self.group_by_length,
            "max_len": self.max_len,
            "gradient_checkpointing": self.gradient_checkpointing,
            "use_lora": self.use_lora,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "lora_target_modules": self.lora_target_modules,
            "save_adapter_only": self.save_adapter_only,
            "logging_steps": self.logging_steps,
            "report_to_wandb": self.report_to_wandb,
            "wandb_project": self.wandb_project,
        }

    def save_json(self, path: Path | str) -> None:
        """Saves configuration to JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: Path | str) -> GLiNER2TrainingConfig:
        """Loads configuration from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
