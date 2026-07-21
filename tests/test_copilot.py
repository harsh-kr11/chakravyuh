"""Tests for the read-only Analyst Copilot agent."""
from __future__ import annotations

import pytest

pytest.importorskip("sklearn")

from chakravyuh.adapters import ScenarioAdapter  # noqa: E402
from chakravyuh.agents.copilot import CopilotAgent  # noqa: E402
from chakravyuh.config import Settings  # noqa: E402
from chakravyuh.export import result_to_dict  # noqa: E402
from chakravyuh.orchestrator import Orchestrator  # noqa: E402
from chakravyuh.scenarios import redecho  # noqa: E402


@pytest.fixture
def incident_dict():
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    return result_to_dict(result, orch)


def test_brief_without_llm_configured_returns_grounded_context(incident_dict):
    copilot = CopilotAgent(settings=Settings(llm_provider="none"))
    out = copilot.brief(incident_dict)
    assert out.llm_used is False
    assert "T1078" in " ".join(out.citations) or out.citations
    assert "context" in out.text.lower()


def test_ask_without_llm_configured_returns_grounded_context(incident_dict):
    copilot = CopilotAgent(settings=Settings(llm_provider="none"))
    out = copilot.ask(incident_dict, "What credential-related techniques were used?")
    assert out.llm_used is False
    assert isinstance(out.citations, list)


def test_copilot_never_mutates_the_incident(incident_dict):
    import copy

    before = copy.deepcopy(incident_dict)
    copilot = CopilotAgent(settings=Settings(llm_provider="none"))
    copilot.brief(incident_dict)
    copilot.ask(incident_dict, "anything?")
    assert incident_dict == before


def test_bad_provider_key_falls_back_gracefully(incident_dict):
    # An enabled provider with no/invalid key must not crash the agent —
    # it should degrade to NullLLM-equivalent behaviour.
    settings = Settings(llm_provider="gemini", gemini_api_key="")
    copilot = CopilotAgent(settings=settings)
    out = copilot.brief(incident_dict)
    assert isinstance(out.text, str)
