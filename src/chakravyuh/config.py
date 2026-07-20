"""Runtime configuration, loaded from environment variables.

All settings are optional and have safe defaults, so the system runs fully
offline with zero configuration. API keys are only needed if you opt into
LLM-backed attribution rationale (see docs/PREREQUISITES.md).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # --- LLM (all optional; default is deterministic, no-LLM mode) --------- #
    llm_provider: str = _get("CHAKRAVYUH_LLM_PROVIDER", "none")  # none|anthropic|openai
    anthropic_api_key: str = _get("ANTHROPIC_API_KEY")
    openai_api_key: str = _get("OPENAI_API_KEY")
    llm_model: str = _get("CHAKRAVYUH_LLM_MODEL", "claude-sonnet-4-6")

    # --- detection / interdiction policy ---------------------------------- #
    anomaly_threshold: float = _get_float("CHAKRAVYUH_ANOMALY_THRESHOLD", 0.5)
    blast_radius_threshold: float = _get_float("CHAKRAVYUH_BLAST_RADIUS", 5.0)

    # --- api --------------------------------------------------------------- #
    api_host: str = _get("CHAKRAVYUH_API_HOST", "127.0.0.1")
    api_port: int = int(_get("CHAKRAVYUH_API_PORT", "8080"))

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider.lower() != "none"


def load_settings() -> Settings:
    return Settings()
