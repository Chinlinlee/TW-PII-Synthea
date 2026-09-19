"""
Tests for PII-Synthea GLiNER2 Fine-tuning Recipe & Training Subsystem.
Covers:
- GLiNER2TrainingConfig serialization and conversion to ExtractorTrainer config
- GLiNER2DataFormatter input/output structure and description injection
- GLiNER2FineTuneRecipe technical spec report, standalone script generation, and dataset validation
"""

import json
from pathlib import Path

import pytest

from pii_synthea.generators.replacement import Span, SynthesisResult
from pii_synthea.training import (
    GLiNER2DataFormatter,
    GLiNER2FineTuneRecipe,
    GLiNER2TrainingConfig,
)


class TestGLiNER2TrainingConfig:
    """Tests training configuration defaults and serialization."""

    def test_default_config_matches_specifications(self):
        cfg = GLiNER2TrainingConfig()
        assert cfg.base_model == "fastino/gliner2-privacy-filter-PII-multi"
        assert cfg.model_type == "extractor"
        assert cfg.word_splitter == "char"
        assert cfg.max_width == 8
        assert cfg.token_pooling == "first"
        assert cfg.use_lora is True
        assert cfg.lora_r == 16
        assert cfg.lora_alpha == 32.0
        assert cfg.encoder_lr == 1e-5
        assert cfg.task_lr == 5e-4
        assert cfg.batch_size == 8
        assert cfg.gradient_accumulation_steps == 2
        assert "encoder" in cfg.lora_target_modules
        assert "span_rep" in cfg.lora_target_modules
        assert "classifier" in cfg.lora_target_modules

    def test_to_gliner2_trainer_config(self):
        cfg = GLiNER2TrainingConfig(num_epochs=12, batch_size=4)
        trainer_dict = cfg.to_gliner2_trainer_config()
        assert trainer_dict["num_epochs"] == 12
        assert trainer_dict["batch_size"] == 4
        assert trainer_dict["encoder_lr"] == 1e-5
        assert trainer_dict["task_lr"] == 5e-4
        assert trainer_dict["use_lora"] is True
        assert trainer_dict["lora_r"] == 16

    def test_json_roundtrip(self, tmp_path):
        cfg = GLiNER2TrainingConfig(num_epochs=5, experiment_name="test_exp")
        p = tmp_path / "config.json"
        cfg.save_json(p)
        loaded = GLiNER2TrainingConfig.load_json(p)
        assert loaded.num_epochs == 5
        assert loaded.experiment_name == "test_exp"
        assert loaded.base_model == cfg.base_model


class TestGLiNER2DataFormatter:
    """Tests data formatting for GLiNER2 ExtractorTrainer."""

    def test_formats_single_positive_record(self):
        text = "病患陳大明於民國112年10月5日就醫"
        spans = [
            Span(start=2, end=5, label="person", text="陳大明"),
            Span(start=6, end=17, label="date", text="民國112年10月5日"),
        ]
        rec = GLiNER2DataFormatter.to_record(text, spans)
        assert rec["input"] == text
        assert "person" in rec["output"]["entities"]
        assert rec["output"]["entities"]["person"] == ["陳大明"]
        assert rec["output"]["entities"]["date"] == ["民國112年10月5日"]
        assert rec["text"] == text
        assert len(rec["spans"]) == 2

    def test_formats_pure_hard_negative_record(self):
        text = "台北市中正區重慶南路一段122號為中華民國總統府。"
        rec = GLiNER2DataFormatter.to_record(text, spans=[])
        assert rec["input"] == text
        assert rec["output"]["entities"] == {}
        assert rec["spans"] == []

    def test_formats_with_bilingual_descriptions(self):
        text = "陳大明的身分證字號為A123456789"
        spans = [
            Span(start=0, end=3, label="person", text="陳大明"),
            Span(start=10, end=20, label="national_id_number", text="A123456789"),
        ]
        rec_en = GLiNER2DataFormatter.to_record(text, spans, include_descriptions=True, desc_lang="en")
        assert "entity_descriptions" in rec_en
        assert "person" in rec_en["entity_descriptions"]
        assert "national_id_number" in rec_en["entity_descriptions"]
        assert "Taiwan National Identification" in rec_en["entity_descriptions"]["national_id_number"]

        rec_zh = GLiNER2DataFormatter.to_record(text, spans, include_descriptions=True, desc_lang="zh")
        assert "身分證" in rec_zh["entity_descriptions"]["national_id_number"]

    def test_from_synthesis_result(self):
        res = SynthesisResult(
            text="立約人林佳玲，電話0912-345-678",
            spans=[
                Span(start=3, end=6, label="person", text="林佳玲"),
                Span(start=9, end=21, label="phone_number", text="0912-345-678"),
            ],
        )
        rec = GLiNER2DataFormatter.from_synthesis_result(res)
        assert rec["input"] == res.text
        assert rec["output"]["entities"]["person"] == ["林佳玲"]
        assert rec["output"]["entities"]["phone_number"] == ["0912-345-678"]


class TestGLiNER2FineTuneRecipe:
    """Tests technical report, script generation, and dataset validation."""

    def test_technical_spec_report_structure(self):
        recipe = GLiNER2FineTuneRecipe()
        report = recipe.get_technical_spec_report()
        assert "target_model" in report
        assert report["target_model"]["checkpoint"] == "fastino/gliner2-privacy-filter-PII-multi"
        assert report["target_model"]["backbone"] == "microsoft/mdeberta-v3-base"
        assert report["target_model"]["max_width"] == 8

        assert "tokenization_and_chinese_offset_mechanics" in report
        assert "CharLevelSplitter" in report["tokenization_and_chinese_offset_mechanics"]["resolution_word_splitter"]

        assert "vocabulary_coverage_analysis" in report
        assert report["vocabulary_coverage_analysis"]["vocab_size"] == 250000

        assert "fine_tuning_strategy" in report
        assert report["fine_tuning_strategy"]["recommended_mode"] == "LoRA (Parameter-Efficient Fine-Tuning)"

    def test_generate_and_export_training_script(self, tmp_path):
        recipe = GLiNER2FineTuneRecipe()
        script_path = tmp_path / "train_gliner2_tw.py"
        exported = recipe.export_training_script(script_path)
        assert exported.exists()

        code = exported.read_text(encoding="utf-8")
        assert "AutoExtractor.from_pretrained" in code
        assert "CharLevelSplitter" in code
        assert "model.set_word_splitter(CharLevelSplitter())" in code
        assert "ExtractorTrainer" in code
        assert "TrainingConfig" in code
        assert "lora_r" in code

    def test_validate_dataset_file(self, tmp_path):
        recipe = GLiNER2FineTuneRecipe()
        data_file = tmp_path / "sample_train.jsonl"

        lines = [
            json.dumps({
                "input": "病患王小明就診",
                "output": {"entities": {"person": ["王小明"]}},
                "text": "病患王小明就診",
                "spans": [{"start": 2, "end": 5, "label": "person", "text": "王小明"}]
            }, ensure_ascii=False),
            json.dumps({
                "input": "這是完全沒有個資的負樣本內容。",
                "output": {"entities": {}},
                "text": "這是完全沒有個資的負樣本內容。",
                "spans": []
            }, ensure_ascii=False),
        ]
        data_file.write_text("\n".join(lines), encoding="utf-8")

        res = recipe.validate_dataset_file(data_file)
        assert res["is_valid"] is True
        assert res["total_records"] == 2
        assert res["pure_negatives"] == 1
        assert res["positive_records"] == 1
        assert res["total_entity_mentions"] == 1
        assert res["errors_found"] == 0
