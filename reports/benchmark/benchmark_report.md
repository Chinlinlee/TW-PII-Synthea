# GLiNER2 Taiwan PII Benchmark Evaluation Report

> **Target Model**: [`a5566qq123/gliner2-tw-pii`](https://huggingface.co/a5566qq123/gliner2-tw-pii) @ `v0.1.0-mid`  
> **Evaluated from**: `./models/gliner2_tw_pii/best`  
> **Benchmark**: `lianghsun/tw-PII-bench`  
> **Evaluation Date**: `2026-09-19`  
> **Matching Mode**: IoU Threshold $\ge 0.5$ (Relaxed) | Exact Character Span (Strict)

## 1. Executive Summary & Baseline Comparison

| Evaluation Dimension | Baseline (Zero-Shot) | Fine-Tuned (GLiNER2-TW) | Delta Improvement (Δ) |
|:---------------------|:---------------------|:------------------------|:----------------------|
| **In-schema Strict Micro F1** | 44.3% | **56.8%** | `+12.5%` |
| **Boundary-Relaxed Micro F1** | 49.6% | **65.0%** | `+15.4%` |
| **Taiwan OOD Generalization Rate** | 64.7% | **97.8%** | `+33.1%` |
| **Hard Negative FP / Item** | 0.00 | **0.00** | `-0.00` (suppressed) |

## 2. Per-Split Performance Summary

| Split | Items | In-schema Strict F1 | Relaxed F1 (IoU > 0.5) | OOD Generalization | Hard Neg FP/item |
|:------|:------|:-------------------|:-----------------------|:-------------------|:-----------------|
| `mid` | 300 | 56.8% | 65.0% | 97.8% | — |
| **Overall** | **300** | **56.8%** | **65.0%** | **97.8%** | **0.00** |

## 3. Block A — In-Schema Entity Breakdown (8 Categories)

| Label | Gold Mentions | TP | FP | FN | Precision | Recall | Strict F1 | Relaxed F1 |
|:------|:--------------|:---|:---|:---|:----------|:-------|:----------|:-----------|
| `private_person` | 516 | 482 | 166 | 34 | 74.4% | 93.4% | **82.8%** | 85.4% |
| `private_phone` | 180 | 175 | 63 | 5 | 73.5% | 97.2% | **83.7%** | 85.2% |
| `private_email` | 120 | 115 | 49 | 5 | 70.1% | 95.8% | **81.0%** | 83.8% |
| `private_address` | 115 | 0 | 23 | 115 | 0.0% | 0.0% | **0.0%** | 13.0% |
| `private_date` | 158 | 33 | 37 | 125 | 47.1% | 20.9% | **28.9%** | 60.5% |
| `private_url` | 166 | 0 | 0 | 166 | 0.0% | 0.0% | **0.0%** | 0.0% |
| `account_number` | 714 | 279 | 118 | 435 | 70.3% | 39.1% | **50.2%** | 67.0% |
| `secret` | 83 | 74 | 410 | 9 | 15.3% | 89.2% | **26.1%** | 28.6% |
| **Micro Average** | **—** | **1158** | **866** | **894** | **57.2%** | **56.4%** | **56.8%** | **65.0%** |
| **Macro Average** | **—** | **—** | **—** | **—** | **—** | **—** | **44.1%** | **52.9%** |

## 4. Block B — Taiwan-Specific OOD Entities (11 Categories)

| OOD Label | Expected Fallback | Total | ✓ Correct | △ Wrong Label | ✗ Missed | Generalization Rate | Detection Rate |
|:----------|:------------------|:------|:----------|:--------------|:---------|:--------------------|:---------------|
| `tw_national_id` | `account_number` | 89 | 88 | 1 | 0 | 98.9% | 100.0% |
| `tw_nhi_card` | `account_number` | 77 | 75 | 2 | 0 | 97.4% | 100.0% |
| `tw_company_id` | `account_number` | 78 | 68 | 10 | 0 | 87.2% | 100.0% |
| `tw_license_plate` | *(none)* | 102 | 102 | 0 | 0 | 100.0% | 100.0% |
| `tw_passport` | `account_number` | 59 | 58 | 1 | 0 | 98.3% | 100.0% |
| `tw_driver_license` | `account_number` | 66 | 66 | 0 | 0 | 100.0% | 100.0% |
| `tw_line_id` | `private_url` | 93 | 92 | 1 | 0 | 98.9% | 100.0% |
| `tw_ptt_id` | *(none)* | 68 | 68 | 0 | 0 | 100.0% | 100.0% |
| `tw_household_no` | `account_number` | 70 | 66 | 4 | 0 | 94.3% | 100.0% |
| `tw_medical_license` | `account_number` | 82 | 82 | 0 | 0 | 100.0% | 100.0% |
| `tw_military_id` | `account_number` | 75 | 75 | 0 | 0 | 100.0% | 100.0% |

- **OOD Overall Detection Rate (any span overlap)**: 100.0%
- **OOD Overall Generalization Rate (correct schema fallback)**: 97.8%

## 5. Block C — Hard Negative False Positives (5 Subtypes)

| Hard Negative Subtype | Total Items | False Positives (FPs) | FP / Item |
|:----------------------|:------------|:----------------------|:----------|
| `neg_business_name` | 0 | 0 | 0.00 |
| `neg_public_figure` | 0 | 0 | 0.00 |
| `neg_landmark_address` | 0 | 0 | 0.00 |
| `neg_public_hotline` | 0 | 0 | 0.00 |
| `neg_institutional_email` | 0 | 0 | 0.00 |
| **Total / Average** | **0** | **0** | **0.00** |
