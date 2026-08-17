"""Catalog scenarios: each reconstruction computes a finite cut that beats naive."""
from __future__ import annotations

import pytest

from chakravyuh.orchestrator import Orchestrator
from chakravyuh.scenarios.catalog import SCENARIOS, get, list_meta
from chakravyuh.schemas import format_target


def test_catalog_lists_five_cases():
    ids = {m["id"] for m in list_meta()}
    assert ids == {"redecho", "colonial", "ukraine2015", "aiims", "synnovis"}
    for meta in list_meta():
        assert meta["disclaimer"]
        assert meta["kind"] in {"reconstruction", "synthetic_illustration"}
        assert meta["sources"]


@pytest.mark.parametrize("sid", list(SCENARIOS))
def test_each_scenario_protects_jewel_cheaper_than_naive(sid):
    mod = get(sid)
    ag = mod.build_graph()
    events = mod.telemetry_stream()
    result = Orchestrator().run(ag, events, crown_jewel=mod.CROWN_JEWEL)
    assert result.plan.crown_jewel_protected is True
    assert result.plan.availability_cost < result.plan.baseline_availability_cost
    hist = mod.historical()
    assert hist["severs_protected"] is True
    protected_edges = [
        (u, v) for u, v, d in ag.g.edges(data=True) if d.get("protected")
    ]
    cut_targets = {format_target(a.target) for a in result.plan.actions}
    for u, v in protected_edges:
        assert format_target((u, v)) not in cut_targets


def test_unknown_catalog_id_raises():
    with pytest.raises(KeyError):
        get("does-not-exist")
