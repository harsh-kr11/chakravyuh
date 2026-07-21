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
        self._model = settings.llm_model or "claude-sonnet-4-6"

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
        self._model = settings.llm_model or "gpt-4o-mini"

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


class GeminiLLM:
    def __init__(self, settings: Settings) -> None:
        from google import genai  # lazy

        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model or "gemini-2.5-flash"

    def complete(self, prompt: str, *, system: str = "") -> str:
        from google.genai import types

        # gemini-2.5-* "thinking" models spend part of max_output_tokens on
        # internal reasoning before any visible answer text — with a small
        # budget, complex prompts can exhaust it before emitting a single
        # word (silent truncation, no error). Bound thinking explicitly and
        # size max_output_tokens with headroom above it so the answer always
        # has room regardless of how much the model "thinks".
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system or "You are a SOC analyst assistant.",
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=1024),
            ),
        )
        return resp.text or ""


def make_llm(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return AnthropicLLM(settings)
    if provider == "openai":
        return OpenAILLM(settings)
    if provider == "gemini":
        return GeminiLLM(settings)
    return NullLLM()
