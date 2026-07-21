"""Tests for the LLM provider adapters.

No network calls / no real API keys needed — these mock the vendor SDK
client to check we call it correctly, in particular a regression guard for
a truncation bug: gemini-2.5-* "thinking" models spend part of
max_output_tokens on internal reasoning before emitting any visible answer
text, so a too-small budget can silently truncate the response to nothing.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("google.genai")

from chakravyuh.config import Settings  # noqa: E402
from chakravyuh.llm.providers import GeminiLLM  # noqa: E402


def test_gemini_complete_bounds_thinking_and_output_budget():
    settings = Settings(gemini_api_key="test-key", llm_model="gemini-2.5-flash")

    fake_response = MagicMock()
    fake_response.text = "a grounded answer"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("google.genai.Client", return_value=fake_client):
        llm = GeminiLLM(settings)
        result = llm.complete("prompt", system="sys")

    assert result == "a grounded answer"
    _, kwargs = fake_client.models.generate_content.call_args
    config = kwargs["config"]
    # Must leave real headroom for the answer above the thinking budget —
    # this is the exact regression that caused silent truncation.
    assert config.max_output_tokens > config.thinking_config.thinking_budget
    assert config.max_output_tokens >= 2048


def test_gemini_requires_api_key():
    settings = Settings(gemini_api_key="")
    with pytest.raises(RuntimeError):
        GeminiLLM(settings)
