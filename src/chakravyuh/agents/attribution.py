"""Attribution agent (ATT&CK mapping + attacker-frontier reconstruction).

Maps each flagged anomaly to a MITRE ATT&CK technique and maintains the
attacker's frontier (the set of assets the attacker has plausibly reached).
Resolves techniques from the scenario's ``technique_hint`` against the Neo4j
knowledge graph (``chakravyuh.knowledge.graph``) when configured/reachable,
falling back to the offline lookup (``chakravyuh.knowledge.attack``)
otherwise — the pipeline never requires Neo4j to run.
"""
from __future__ import annotations

from ..knowledge import attack as offline_attack
from ..knowledge.graph import get_graph
from ..schemas import (
    AnomalySignal,
    IncidentContext,
    TechniqueMatch,
    TelemetryEvent,
)
from .base import Agent


class AttributionAgent(Agent):
    name = "attribution"

    def _resolve(self, technique_id: str) -> tuple[str, str]:
        """Return (name, tactic) for a technique id, graph-first."""
        graph = get_graph()
        if graph is not None:
            ctx = graph.lookup_technique(technique_id)
            if ctx is not None:
                return ctx.name, ctx.tactic
        t = offline_attack.lookup(technique_id)
        return (t.name, t.tactic) if t else ("", "")

    def process(
        self,
        incident_id: str,
        anomalies: list[AnomalySignal],
        events: list[TelemetryEvent],
    ) -> IncidentContext:
        # Index technique hints by asset from the (malicious) events.
        hint_by_asset: dict[str, str] = {
            e.asset_id: e.technique_hint
            for e in events
            if e.technique_hint
        }

        techniques: list[TechniqueMatch] = []
        frontier: list[str] = []
        for sig in anomalies:
            if sig.asset_id not in frontier:
                frontier.append(sig.asset_id)
            tid = hint_by_asset.get(sig.asset_id)
            if tid:
                name, tactic = self._resolve(tid)
                techniques.append(TechniqueMatch(
                    technique_id=tid,
                    technique_name=name,
                    tactic=tactic,
                    confidence=sig.score,
                    asset_id=sig.asset_id,
                ))

        return IncidentContext(
            incident_id=incident_id,
            anomalies=anomalies,
            techniques=techniques,
            attacker_frontier=frontier,
        )
