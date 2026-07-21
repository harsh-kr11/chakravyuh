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
# ordered (asset reached, technique, behavioural features). We interdict here
# — *before* the attacker reaches OT — so the optimiser can choose cheap
# upstream actions instead of being forced onto the expensive, human-gated OT
# edge. Feature vectors follow chakravyuh.ml.features.FEATURE_NAMES:
# [off_hours, failed_logins_1h, new_asset_pair, bytes_out_zscore,
#  process_count_zscore, privilege_level, session_duration_zscore] — no
# attack signature is encoded, only behavioural signal fed to the
# unsupervised UEBA model (see chakravyuh.ml). Anomaly scores are computed
# by that model, not hardcoded (fallback: "anomaly_score" below, used only
# if scikit-learn / the [detect] extra is not installed).
ATTACK_STEPS: list[tuple[str, str, dict[str, float]]] = [
    ("it_jump_host", "T1078", {   # valid accounts, initial foothold
        "off_hours": 1, "failed_logins_1h": 1, "new_asset_pair": 1,
        "bytes_out_zscore": 1.5, "process_count_zscore": 0.8,
        "privilege_level": 0, "session_duration_zscore": 0.5,
        "anomaly_score": 0.82,
    }),
    ("it_workstation", "T1021", {  # remote services, lateral move
        "off_hours": 1, "failed_logins_1h": 1, "new_asset_pair": 1,
        "bytes_out_zscore": 1.8, "process_count_zscore": 1.8,
        "privilege_level": 1, "session_duration_zscore": 1.0,
        "anomaly_score": 0.78,
    }),
    ("engineer_cred", "T1003", {  # credential dumping
        "off_hours": 1, "failed_logins_1h": 4, "new_asset_pair": 1,
        "bytes_out_zscore": 1.2, "process_count_zscore": 2.5,
        "privilege_level": 2, "session_duration_zscore": 1.5,
        "anomaly_score": 0.85,
    }),
]

# The attacker's *intended* next hop (predicted, not yet reached). Preempting
# this is the whole point: cut the path to OT before it is taken.
PREDICTED_NEXT: list[tuple[str, str]] = [
    ("ot_historian", "T0812"),            # default creds into OT (predicted)
]

# Benign noise events (should NOT be flagged): tests false-positive handling.
BENIGN_EVENTS: list[tuple[str, dict[str, float]]] = [
    ("it_workstation", {
        "off_hours": 0, "failed_logins_1h": 0, "new_asset_pair": 0,
        "bytes_out_zscore": 0.2, "process_count_zscore": 0.1,
        "privilege_level": 0, "session_duration_zscore": 0.1,
        "anomaly_score": 0.20,
    }),
    ("domain_controller", {
        "off_hours": 0, "failed_logins_1h": 0, "new_asset_pair": 0,
        "bytes_out_zscore": 0.1, "process_count_zscore": 0.1,
        "privilege_level": 0, "session_duration_zscore": 0.1,
        "anomaly_score": 0.15,
    }),
]


def telemetry_stream() -> list[TelemetryEvent]:
    """Interleave benign noise with the malicious attack chain."""
    events: list[TelemetryEvent] = []
    for asset_id, features in BENIGN_EVENTS:
        events.append(TelemetryEvent(
            asset_id=asset_id, kind="auth",
            features=dict(features), is_malicious=False,
        ))
    for asset_id, technique, features in ATTACK_STEPS:
        events.append(TelemetryEvent(
            asset_id=asset_id, kind="auth",
            features=dict(features),
            is_malicious=True, technique_hint=technique,
        ))
    return events
