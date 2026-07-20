"""Thin, lazily-imported provider adapters.

Real network clients are imported inside the constructors so the base package
has no hard dependency on any vendor SDK. Enable by setting the provider and
the matching API key (see docs/PREREQUISITES.md).
"""
from __future__ import annotations

from ..config import Settings
from .base import LLMClient, NullLLM


class AnthropicLLM:
    def __init__(self, settings: Settings) -> None:
        import anthropic  # lazy; only needed if enabled

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model

    def complete(self, prompt: str, *, system: str = "") -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=system or "You are a SOC analyst assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            b.text for b in msg.content if getattr(b, "type", "") == "text"
        )


class OpenAILLM:
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI  # lazy

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model

    def complete(self, prompt: str, *, system: str = "") -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system",
                 "content": system or "You are a SOC analyst assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
        )
        return resp.choices[0].message.content or ""


def make_llm(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return AnthropicLLM(settings)
    if provider == "openai":
        return OpenAILLM(settings)
    return NullLLM()
