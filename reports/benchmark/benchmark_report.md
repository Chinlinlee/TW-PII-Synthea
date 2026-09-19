# GLiNER2 Taiwan PII Benchmark Evaluation Report

> **Target Model**: `fastino/gliner2-privacy-filter-PII-multi`  
> **Benchmark**: `lianghsun/tw-PII-bench`  
> **Evaluation Date**: `2026-09-19`  
> **Matching Mode**: IoU Threshold $\ge 0.5$ (Relaxed) | Exact Character Span (Strict)

## 2. Per-Split Performance Summary

| Split | Items | In-schema Strict F1 | Relaxed F1 (IoU > 0.5) | OOD Generalization | Hard Neg FP/item |
|:------|:------|:-------------------|:-----------------------|:-------------------|:-----------------|
| `short` | 37 | 18.2% | 77.3% | 81.8% | 0.60 |
| **Overall** | **37** | **18.2%** | **77.3%** | **81.8%** | **0.60** |

## 3. Block A — In-Schema Entity Breakdown (8 Categories)

| Label | Gold Mentions | TP | FP | FN | Precision | Recall | Strict F1 | Relaxed F1 |
|:------|:--------------|:---|:---|:---|:----------|:-------|:----------|:-----------|
| `private_person` | 2 | 2 | 0 | 0 | 100.0% | 100.0% | **100.0%** | 100.0% |
| `private_phone` | 2 | 1 | 0 | 1 | 100.0% | 50.0% | **66.7%** | 66.7% |
| `private_email` | 2 | 0 | 2 | 2 | 0.0% | 0.0% | **0.0%** | 100.0% |
| `private_address` | 2 | 0 | 2 | 2 | 0.0% | 0.0% | **0.0%** | 0.0% |
| `private_date` | 2 | 0 | 0 | 2 | 0.0% | 0.0% | **0.0%** | 0.0% |
| `private_url` | 3 | 0 | 2 | 3 | 0.0% | 0.0% | **0.0%** | 80.0% |
| `account_number` | 10 | 1 | 7 | 9 | 12.5% | 10.0% | **11.1%** | 88.9% |
| `secret` | 2 | 0 | 2 | 2 | 0.0% | 0.0% | **0.0%** | 100.0% |
| **Micro Average** | **—** | **4** | **15** | **21** | **21.1%** | **16.0%** | **18.2%** | **77.3%** |
| **Macro Average** | **—** | **—** | **—** | **—** | **—** | **—** | **22.2%** | **66.9%** |

## 4. Block B — Taiwan-Specific OOD Entities (11 Categories)

| OOD Label | Expected Fallback | Total | ✓ Correct | △ Wrong Label | ✗ Missed | Generalization Rate | Detection Rate |
|:----------|:------------------|:------|:----------|:--------------|:---------|:--------------------|:---------------|
| `tw_national_id` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_nhi_card` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_company_id` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_license_plate` | *(none)* | 1 | 0 | 1 | 0 | 0.0% | 100.0% |
| `tw_passport` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_driver_license` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_line_id` | `private_url` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_ptt_id` | *(none)* | 1 | 0 | 1 | 0 | 0.0% | 100.0% |
| `tw_household_no` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_medical_license` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| `tw_military_id` | `account_number` | 1 | 1 | 0 | 0 | 100.0% | 100.0% |

- **OOD Overall Detection Rate (any span overlap)**: 100.0%
- **OOD Overall Generalization Rate (correct schema fallback)**: 81.8%

## 5. Block C — Hard Negative False Positives (5 Subtypes)

| Hard Negative Subtype | Total Items | False Positives (FPs) | FP / Item |
|:----------------------|:------------|:----------------------|:----------|
| `neg_business_name` | 2 | 1 | 0.50 |
| `neg_public_figure` | 2 | 1 | 0.50 |
| `neg_landmark_address` | 2 | 0 | 0.00 |
| `neg_public_hotline` | 2 | 2 | 1.00 |
| `neg_institutional_email` | 2 | 2 | 1.00 |
| **Total / Average** | **10** | **6** | **0.60** |
