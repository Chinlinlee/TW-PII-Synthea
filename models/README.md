# 本機模型目錄

Git 不追蹤此目錄下的權重與 checkpoint（見根目錄 `.gitignore`）。**Canonical 微調權重**發布於 Hugging Face：

- **Repo**: [`a5566qq123/gliner2-tw-pii`](https://huggingface.co/a5566qq123/gliner2-tw-pii)（public LoRA adapter，base：`fastino/gliner2-privacy-filter-PII-multi`）

## 下載到本機（建議路徑）

```bash
uv run huggingface-cli download a5566qq123/gliner2-tw-pii \
  --local-dir models/gliner2_tw_pii/best
```

目前 release tag：**`v0.1.0-mid`**（mid split benchmark 對應權重）。

若需重新訓練：

```bash
uv run python scripts/train_gliner2_tw.py
```

訓練設定以版控內 [`configs/gliner2_tw_pii_training.json`](../configs/gliner2_tw_pii_training.json) 為準；執行後會在 `models/gliner2_tw_pii/` 寫入同內容的 `training_config.json` 與 adapter。

## 評估

```bash
uv run python scripts/evaluate_gliner2_tw.py \
  --model-path ./models/gliner2_tw_pii/best \
  --baseline-path fastino/gliner2-privacy-filter-PII-multi
```

Hub 上線並固定 revision/tag 後，評估腳本預設可改為 Hub id；benchmark 報告會在首次上傳後更新 `model_hub_id` / `revision` 欄位。
