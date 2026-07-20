"""Attribution agent (ATT&CK mapping + attacker-frontier reconstruction).

Maps each flagged anomaly to a MITRE ATT&CK technique and maintains the
attacker's frontier (the set of assets the attacker has plausibly reached).
The reference implementation resolves techniques from the scenario's
``technique_hint`` via the offline ATT&CK lookup; production swaps in a
knowledge-graph + RAG mapper over the STIX bundle and CERT-In advisories.
"""
from __future__ import annotations

from ..knowledge.attack import lookup
from ..schemas import (
    AnomalySignal,
    IncidentContext,
    TechniqueMatch,
    TelemetryEvent,
)
from .base import Agent


class AttributionAgent(Agent):
    name = "attribution"

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
                t = lookup(tid)
                techniques.append(TechniqueMatch(
                    technique_id=tid,
                    technique_name=t.name if t else "",
                    tactic=t.tactic if t else "",
                    confidence=sig.score,
                    asset_id=sig.asset_id,
                ))

        return IncidentContext(
            incident_id=incident_id,
            anomalies=anomalies,
            techniques=techniques,
            attacker_frontier=frontier,
        )
