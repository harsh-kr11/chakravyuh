"""LLM interface — provider-agnostic, optional, never in the safety path.

The LLM is used ONLY to produce natural-language rationale/summaries for
analysts. It never selects containment actions, never gates, and never touches
actuation. The deterministic core is fully functional without it.
"""
from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str, *, system: str = "") -> str: ...


class NullLLM:
    """Default: no external calls. Returns a deterministic templated string."""

    def complete(self, prompt: str, *, system: str = "") -> str:
        return "(LLM disabled — deterministic rationale only)"
