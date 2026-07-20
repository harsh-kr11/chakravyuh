"""Tests for the minimum-cost cross-sector interdiction engine (the wedge)."""
from __future__ import annotations

import networkx as nx
import pytest

from chakravyuh.graph import AttackGraph, plan_interdiction
from chakravyuh.graph.interdiction import (
    min_cost_interdiction,
    naive_containment_cost,
)
from chakravyuh.schemas import ActionType, Asset, AssetType, Sector


def _simple_graph() -> AttackGraph:
    """internet -> a -> b -> CJ, with a protected CJ -> load dependency."""
    ag = AttackGraph()
    for aid, ctype, cj in [
        ("internet", AssetType.INTERNET, False),
        ("a", AssetType.IT_HOST, False),
        ("b", AssetType.IT_SERVER, False),
        ("cj", AssetType.OT_SCADA, True),
        ("load", AssetType.SERVICE_LOAD, False),
    ]:
        ag.add_asset(Asset(asset_id=aid, sector=Sector.POWER,
                           asset_type=ctype, criticality=3, is_crown_jewel=cj))
    ag.add_edge("internet", "a", exploit_cost=1, cut_cost=1)
    ag.add_edge("a", "b", exploit_cost=1, cut_cost=2)
    ag.add_edge("b", "cj", exploit_cost=1, cut_cost=5)
    ag.add_edge("cj", "load", exploit_cost=1, cut_cost=100, protected=True)
    return ag


def test_min_cut_separates_attacker_from_crown_jewel():
    ag = _simple_graph()
    cut_edges, cost = min_cost_interdiction(ag, ["internet"], "cj")
    residual = ag.g.copy()
    residual.remove_edges_from(cut_edges)
    assert not nx.has_path(residual, "internet", "cj")
    # cheapest single cut on the chain is edge internet->a (cost 1)
    assert cost == 1.0


def test_min_cut_is_minimal_not_naive():
    ag = _simple_graph()
    _, smart_cost = min_cost_interdiction(ag, ["internet"], "cj")
    _, naive_cost, _ = naive_containment_cost(ag, "cj")
    assert smart_cost < naive_cost


def test_protected_dependency_is_never_cut():
    ag = _simple_graph()
    # Put the attacker right before the crown jewel so the only forward barrier
    # is b->cj; the protected cj->load edge must still never be chosen.
    cut_edges, cost = min_cost_interdiction(ag, ["b"], "cj")
    assert ("cj", "load") not in cut_edges
    assert cost == 5.0  # forced onto b->cj, but never the protected edge


def test_naive_severs_protected_dependency():
    ag = _simple_graph()
    edges, cost, severs = naive_containment_cost(ag, "cj")
    assert severs is True
    assert ("cj", "load") in edges


def test_plan_marks_crown_jewel_protected_and_cascade_averted():
    ag = _simple_graph()
    plan = plan_interdiction(ag, "INC", ["internet"], "cj")
    assert plan.crown_jewel_protected is True
    assert plan.attacker_cost_after == float("inf")
    assert plan.cascade_averted is True
    assert plan.availability_cost < plan.baseline_availability_cost


def test_already_separated_returns_empty_cut():
    ag = _simple_graph()
    ag.g.remove_edge("b", "cj")  # no path to crown jewel
    cut_edges, cost = min_cost_interdiction(ag, ["internet"], "cj")
    assert cut_edges == []
    assert cost == 0.0


def test_unknown_crown_jewel_raises():
    ag = _simple_graph()
    with pytest.raises(ValueError):
        min_cost_interdiction(ag, ["internet"], "does_not_exist")


def test_edge_action_gating_semantics():
    ag = _simple_graph()
    ag.add_edge("a", "id", exploit_cost=1, cut_cost=1,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_asset(Asset(asset_id="id", sector=Sector.POWER,
                       asset_type=AssetType.IDENTITY, criticality=2))
    # revoke of a non-OT identity -> autonomous
    action = ag.edge_to_action("a", "id")
    assert action.action_type == ActionType.REVOKE_CREDENTIAL
    assert action.target == "a"          # targets the credential (src)
    assert action.requires_human_gate is False
    # block link into an OT device -> gated
    ot_action = ag.edge_to_action("b", "cj")
    assert ot_action.requires_human_gate is True
