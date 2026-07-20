"""RedEcho-style cross-sector demo scenario.

Builds a mock network spanning a power utility's IT and OT, plus a hospital
whose power load depends on the grid segment the SCADA server controls. Then
scripts a low-and-slow APT that walks from an internet-facing jump host toward
the SCADA crown jewel.

This scenario is intentionally small and deterministic so the demo and tests
are reproducible. Swap it for DARPA OpTC (IT) + HAI/SWaT (OT) replay to
evaluate on real benchmark data (see docs/DATASETS.md).

IMPORTANT (attribution honesty): RedEcho was reported as *pre-positioning*
against Indian power-sector organisations; the link to the 2020 Mumbai outage
is explicitly unsubstantiated. This scenario is a synthetic illustration, not
a claim about any real incident.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..schemas import (
    ActionType,
    Asset,
    AssetType,
    Sector,
    TelemetryEvent,
)

CROWN_JEWEL = "ot_scada_server"
HOSPITAL_LOAD = "hospital_power_load"


def build_graph() -> AttackGraph:
    ag = AttackGraph()

    assets = [
        Asset(asset_id="internet", sector=Sector.INTERNET,
              asset_type=AssetType.INTERNET, criticality=1),
        Asset(asset_id="it_jump_host", sector=Sector.POWER,
              asset_type=AssetType.IT_SERVER, criticality=2),
        Asset(asset_id="it_workstation", sector=Sector.POWER,
              asset_type=AssetType.IT_HOST, criticality=2),
        Asset(asset_id="domain_controller", sector=Sector.POWER,
              asset_type=AssetType.IT_SERVER, criticality=4),
        Asset(asset_id="engineer_cred", sector=Sector.POWER,
              asset_type=AssetType.IDENTITY, criticality=3),
        Asset(asset_id="ot_historian", sector=Sector.POWER,
              asset_type=AssetType.OT_HISTORIAN, criticality=4),
        Asset(asset_id=CROWN_JEWEL, sector=Sector.POWER,
              asset_type=AssetType.OT_SCADA, criticality=5,
              is_crown_jewel=True, tags=["grid_control"]),
        Asset(asset_id=HOSPITAL_LOAD, sector=Sector.HEALTH,
              asset_type=AssetType.SERVICE_LOAD, criticality=5,
              tags=["patient_safety"]),
    ]
    for a in assets:
        ag.add_asset(a)

    # Attacker-traversable edges: (exploit_cost low = easy for attacker),
    # (cut_cost = defender disruption if blocked).
    ag.add_edge("internet", "it_jump_host",
                exploit_cost=2.0, cut_cost=1.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("it_jump_host", "it_workstation",
                exploit_cost=1.0, cut_cost=1.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("it_workstation", "engineer_cred",
                exploit_cost=1.0, cut_cost=1.0,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_edge("it_workstation", "domain_controller",
                exploit_cost=3.0, cut_cost=6.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("engineer_cred", "ot_historian",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_edge("domain_controller", "ot_historian",
                exploit_cost=2.0, cut_cost=1.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("ot_historian", CROWN_JEWEL,
                exploit_cost=2.0, cut_cost=8.0,
                action_type=ActionType.BLOCK_LINK)

    # Protected cross-sector dependency: the hospital's power load depends on
    # the grid segment the SCADA server controls. This edge MUST NOT be cut.
    ag.add_edge(CROWN_JEWEL, HOSPITAL_LOAD,
                exploit_cost=99.0, cut_cost=100.0, protected=True,
                action_type=ActionType.BLOCK_LINK)

    return ag


# Scripted attacker progression that is DETECTED (the confirmed frontier),
# ordered (asset reached, technique, score). We interdict here — *before* the
# attacker reaches OT — so the optimiser can choose cheap upstream actions
# instead of being forced onto the expensive, human-gated OT edge.
ATTACK_STEPS: list[tuple[str, str, float]] = [
    ("it_jump_host", "T1078", 0.82),      # valid accounts, initial foothold
    ("it_workstation", "T1021", 0.78),    # remote services, lateral move
    ("engineer_cred", "T1003", 0.85),     # credential dumping
]

# The attacker's *intended* next hop (predicted, not yet reached). Preempting
# this is the whole point: cut the path to OT before it is taken.
PREDICTED_NEXT: list[tuple[str, str]] = [
    ("ot_historian", "T0812"),            # default creds into OT (predicted)
]

# Benign noise events (should NOT be flagged): tests false-positive handling.
BENIGN_EVENTS: list[tuple[str, float]] = [
    ("it_workstation", 0.20),
    ("domain_controller", 0.15),
]


def telemetry_stream() -> list[TelemetryEvent]:
    """Interleave benign noise with the malicious attack chain."""
    events: list[TelemetryEvent] = []
    for asset_id, score in BENIGN_EVENTS:
        events.append(TelemetryEvent(
            asset_id=asset_id, kind="auth",
            features={"anomaly_score": score}, is_malicious=False,
        ))
    for asset_id, technique, score in ATTACK_STEPS:
        events.append(TelemetryEvent(
            asset_id=asset_id, kind="auth",
            features={"anomaly_score": score},
            is_malicious=True, technique_hint=technique,
        ))
    return events
