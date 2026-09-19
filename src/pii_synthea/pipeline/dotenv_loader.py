"""Load optional repo-root .env for LLM credentials (lazy, once per process)."""

from __future__ import annotations

import os
from pathlib import Path

_dotenv_loaded = False


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_project_dotenv() -> bool:
    """
    Load environment variables from .env without overriding existing process env.

    Returns True if a .env file was found and passed to python-dotenv.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return False

    from dotenv import load_dotenv

    _dotenv_loaded = True

    custom = os.environ.get("PII_SYNTH_ENV_FILE")
    if custom:
        path = Path(custom)
        if path.is_file():
            load_dotenv(path, override=False)
            return True
        return False

    env_path = _project_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)
        return True
    return False


def reset_dotenv_loader_state() -> None:
    """Test-only: allow reloading .env in the same process."""
    global _dotenv_loaded
    _dotenv_loaded = False
