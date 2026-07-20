"""Cascade agent (cross-sector impact prediction).

Given the live attack graph and the attacker frontier, determine which crown
jewels are threatened and which *dependent loads in other sectors* would be
affected if a crown jewel is compromised or naively isolated. This is what
elevates a single-site IT incident into a national, cross-sector public-safety
concern — and it is the information the interdiction planner uses to avoid
severing protected dependencies.
"""
from __future__ import annotations

import networkx as nx

from ..graph import AttackGraph
from ..schemas import CascadeAssessment
from .base import Agent


class CascadeAgent(Agent):
    name = "cascade"

    def process(
        self,
        ag: AttackGraph,
        incident_id: str,
        attacker_frontier: list[str],
    ) -> CascadeAssessment:
        threatened: list[str] = []
        for cj in ag.crown_jewels():
            for s in attacker_frontier:
                if s in ag.g and nx.has_path(ag.g, s, cj):
                    threatened.append(cj)
                    break

        # Dependent loads: assets in a *different* sector reachable from a
        # threatened crown jewel via a protected dependency edge.
        loads_at_risk: list[str] = []
        cross_sector = False
        for cj in threatened:
            cj_sector = ag.asset(cj).sector
            for _, v, data in ag.g.out_edges(cj, data=True):
                if data.get("protected"):
                    loads_at_risk.append(v)
                    if ag.asset(v).sector != cj_sector:
                        cross_sector = True

        narrative = ""
        if threatened:
            narrative = (
                f"Attacker can reach crown jewel(s) {threatened}. "
            )
            if loads_at_risk:
                narrative += (
                    f"Compromise or naive isolation would jeopardise "
                    f"dependent load(s) {loads_at_risk}"
                    + (" across sectors." if cross_sector else ".")
                )

        return CascadeAssessment(
            incident_id=incident_id,
            threatened_crown_jewels=threatened,
            dependent_loads_at_risk=loads_at_risk,
            cross_sector=cross_sector,
            narrative=narrative,
        )
