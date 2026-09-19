# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Project Overview

**PII-Synthea** — 繁體中文（台灣在地化）合成個資（PII）資料集生成引擎。
專門生成具備精確字元級 Span 標註、在地合法檢查碼、真實語境與難辨負樣本的合成訓練語料，目標是用於微調 `fastino/gliner2-privacy-filter-PII-multi` 產出台灣專屬版本。

## Agent skills

### Issue tracker
GitHub Issues via `gh` CLI (`Chinlinlee/TW-PII-Synthea`). See `docs/agents/issue-tracker.md`.

### Domain docs
Single-context layout with `CONTEXT.md` at repo root and ADRs in `docs/adr/`. See `docs/agents/domain.md`.

## Tech Stack
- **Language**: Python 3.11+
- **Package manager**: `uv`
- **Target Model**: `fastino/gliner2-privacy-filter-PII-multi` (GLiNER2 architecture)
