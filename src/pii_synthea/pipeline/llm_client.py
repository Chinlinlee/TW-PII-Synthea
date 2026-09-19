"""
OpenAI-compatible chat client for LLM-driven Taiwan PII scenario generation.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from pii_synthea.generators.replacement import Span
from pii_synthea.pipeline.dotenv_loader import load_project_dotenv


class LLMCompletionClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


@dataclass
class OpenAICompatibleLLMClient:
    """Minimal chat-completions client (OpenAI / Azure / local vLLM)."""

    base_url: str = "https://api.openai.com/v1"
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    timeout_sec: float = 120.0

    @classmethod
    def from_env(cls) -> "OpenAICompatibleLLMClient":
        load_project_dotenv()
        base = os.environ.get("PII_SYNTH_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        key = os.environ.get("PII_SYNTH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("PII_SYNTH_LLM_MODEL", "gpt-4o-mini")
        return cls(base_url=base, api_key=key, model=model)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_configured:
            raise RuntimeError(
                "LLM API key not configured. Set OPENAI_API_KEY or PII_SYNTH_LLM_API_KEY, "
                "or use --llm-offline-fallback for local seed-to-tag replay."
            )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.9,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP {e.code}: {err_body[:500]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"LLM request failed: {e}") from e

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"LLM returned no choices: {data!r}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content or not str(content).strip():
            raise RuntimeError("LLM returned empty content")
        return str(content).strip()


def spans_to_tagged_text(text: str, spans: Sequence[Span]) -> str:
    """Re-wraps clean text with XML tags for offline LLM-ingest replay."""
    sorted_spans = sorted(spans, key=lambda s: s.start)
    parts: list[str] = []
    cursor = 0
    for span in sorted_spans:
        parts.append(text[cursor:span.start])
        label = span.label
        parts.append(f"<{label}>{span.text}</{label}>")
        cursor = span.end
    parts.append(text[cursor:])
    return "".join(parts)
