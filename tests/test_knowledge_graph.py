"""Tests for the Neo4j-backed knowledge graph.

Skips automatically if CHAKRAVYUH_NEO4J_URI is not set or Neo4j is
unreachable — the graph is an optional upgrade, never a hard dependency.
"""
from __future__ import annotations

import pytest

pytest.importorskip("neo4j")

from chakravyuh.config import load_settings  # noqa: E402
from chakravyuh.knowledge.graph import get_graph, reset_cache  # noqa: E402


@pytest.fixture
def graph():
    reset_cache()
    settings = load_settings()
    if not settings.neo4j_enabled:
        pytest.skip("CHAKRAVYUH_NEO4J_URI not set")
    g = get_graph(settings)
    if g is None:
        pytest.skip("Neo4j not reachable")
    yield g
    reset_cache()


def test_lookup_known_technique(graph):
    ctx = graph.lookup_technique("T1078")
    assert ctx is not None
    assert ctx.name == "Valid Accounts"
    assert ctx.tactic == "Initial Access"
    assert "Multi-factor Authentication" in ctx.mitigations
    assert any(c["id"] == "CVE-2020-1472" for c in ctx.cves)
    assert any(a["id"] == "ADV-SAMPLE-002" for a in ctx.advisories)


def test_lookup_unknown_technique_returns_none(graph):
    assert graph.lookup_technique("T9999") is None


def test_all_documents_nonempty(graph):
    docs = graph.all_documents()
    assert len(docs) >= 10
    assert all("text" in d and "source" in d for d in docs)


def test_attribution_agent_uses_graph_when_available(graph):
    from chakravyuh.adapters import ScenarioAdapter
    from chakravyuh.orchestrator import Orchestrator
    from chakravyuh.scenarios import redecho

    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    ids = {t.technique_id for t in result.context.techniques}
    assert "T1078" in ids
    match = next(t for t in result.context.techniques if t.technique_id == "T1078")
    assert match.technique_name == "Valid Accounts"
