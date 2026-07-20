"""Incident-time cross-sector attack-path interdiction — the novel core.

Problem
-------
During a live intrusion we know (a) the attacker's current frontier and
(b) the crown-jewel asset(s) we must protect. We want the *smallest-disruption*
set of containment actions that separates the attacker from the crown jewel,
**without** severing any protected cross-sector dependency (e.g. a hospital's
power draw from the grid the SCADA server controls).

Formulation
-----------
This is a minimum s-t cut. Build a flow network where:

* a synthetic super-source connects to every attacker-frontier node with
  infinite capacity;
* the sink is the crown jewel;
* every real edge's capacity = its ``cut_cost`` (defender disruption);
* protected dependency edges get **infinite** capacity so the min cut can
  never choose them.

The minimum cut is then, by construction, the cheapest (least operationally
disruptive) set of edges whose blocking disconnects the attacker from the
crown jewel while preserving every protected dependency. Each cut edge maps to
one concrete containment action.

Why this is the wedge
----------------------
Classic attack-graph interdiction is offline/pre-incident hardening. Online
intrusion-response work selects policies (POMDP/RL) on a single IT network.
Cross-sector cascade games model *physical* node attacks. Here we do all three
at once: a live-telemetry-driven cut, with an explicit availability cost, that
is cross-sector-cascade-aware.
"""
from __future__ import annotations

import networkx as nx

from ..schemas import ContainmentAction, InterdictionPlan
from .attack_graph import AttackGraph

_SUPER_SOURCE = "__ATTACKER_SUPERSOURCE__"
_INF = float("inf")


def _flow_network(
    ag: AttackGraph, attacker_frontier: list[str]
) -> nx.DiGraph:
    h = nx.DiGraph()
    for u, v, data in ag.g.edges(data=True):
        cap = _INF if data.get("protected") else float(data.get("cut_cost", 1.0))
        h.add_edge(u, v, capacity=cap)
    for a in attacker_frontier:
        if a in ag.g:
            h.add_edge(_SUPER_SOURCE, a, capacity=_INF)
    return h


def min_cost_interdiction(
    ag: AttackGraph,
    attacker_frontier: list[str],
    crown_jewel: str,
) -> tuple[list[tuple[str, str]], float]:
    """Return (cut_edges, total_cut_cost) separating attacker from crown jewel.

    Raises ValueError if the crown jewel is unreachable from the attacker
    (nothing to do) or if no finite cut exists (attacker already co-located
    with the crown jewel, or only protected edges remain).
    """
    if crown_jewel not in ag.g:
        raise ValueError(f"unknown crown jewel {crown_jewel!r}")

    h = _flow_network(ag, attacker_frontier)
    if _SUPER_SOURCE not in h or crown_jewel not in h:
        return [], 0.0
    if not nx.has_path(h, _SUPER_SOURCE, crown_jewel):
        return [], 0.0  # already separated — nothing to cut

    cut_value, (reachable, unreachable) = nx.minimum_cut(
        h, _SUPER_SOURCE, crown_jewel
    )
    if cut_value == _INF:
        raise ValueError(
            "no finite containment cut exists (attacker adjacent to crown "
            "jewel, or only protected dependencies separate them)"
        )

    cut_edges: list[tuple[str, str]] = []
    for u in reachable:
        if u == _SUPER_SOURCE:
            continue
        for v in ag.g.successors(u):
            if v in unreachable:
                cut_edges.append((u, v))
    return cut_edges, float(cut_value)


def naive_containment_cost(
    ag: AttackGraph, crown_jewel: str
) -> tuple[list[tuple[str, str]], float, bool]:
    """Baseline: 'isolate the crown jewel and everything touching it'.

    This is what a rule-based SOAR playbook or a panicking analyst does. It is
    typically far more disruptive and — crucially — will happily sever a
    protected cross-sector dependency, causing the very cascade we want to
    avoid. Returns (edges_cut, cost, severs_protected_dependency).
    """
    edges: list[tuple[str, str]] = []
    cost = 0.0
    severs_protected = False
    # Cut every edge incident to the crown jewel (in and out).
    for u in ag.g.predecessors(crown_jewel):
        data = ag.g.edges[u, crown_jewel]
        edges.append((u, crown_jewel))
        cost += float(data.get("cut_cost", 1.0))
    for v in ag.g.successors(crown_jewel):
        data = ag.g.edges[crown_jewel, v]
        edges.append((crown_jewel, v))
        cost += float(data.get("cut_cost", 1.0))
        if data.get("protected"):
            severs_protected = True
    return edges, cost, severs_protected


def plan_interdiction(
    ag: AttackGraph,
    incident_id: str,
    attacker_frontier: list[str],
    crown_jewel: str,
) -> InterdictionPlan:
    """High-level entry point: produce a full, comparable InterdictionPlan."""
    cost_before = ag.attacker_min_cost(attacker_frontier, crown_jewel)

    cut_edges, cut_cost = min_cost_interdiction(
        ag, attacker_frontier, crown_jewel
    )
    actions: list[ContainmentAction] = [
        ag.edge_to_action(u, v) for (u, v) in cut_edges
    ]

    # Recompute attacker reachability after applying the cut.
    residual = ag.g.copy()
    residual.remove_edges_from(cut_edges)
    cost_after = _INF
    for s in attacker_frontier:
        if s in residual and crown_jewel in residual:
            try:
                c = nx.shortest_path_length(
                    residual, s, crown_jewel, weight="exploit_cost"
                )
                cost_after = min(cost_after, c)
            except nx.NetworkXNoPath:
                continue

    # Did we preserve every protected dependency? (min-cut guarantees yes, but
    # we assert it explicitly for auditability.)
    severed_protected = any(
        ag.g.edges[u, v].get("protected") for (u, v) in cut_edges
    )
    _, naive_cost, naive_severs = naive_containment_cost(ag, crown_jewel)

    return InterdictionPlan(
        incident_id=incident_id,
        actions=actions,
        attacker_cost_before=cost_before,
        attacker_cost_after=cost_after,
        availability_cost=cut_cost,
        crown_jewel_protected=(cost_after == _INF),
        cascade_averted=(not severed_protected) and naive_severs,
        baseline_availability_cost=naive_cost,
        notes=(
            f"min-cost cut of {len(cut_edges)} edge(s); "
            f"naive baseline would cost {naive_cost:.1f} "
            f"and {'WOULD' if naive_severs else 'would not'} sever a "
            f"protected cross-sector dependency."
        ),
    )
