"""AIIMS Delhi ransomware (November 2022) — isolate the island, not the campus.

Public-source reconstruction. Does not decrypt already-encrypted hosts.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..graph.interdiction import naive_containment_cost
from ..schemas import ActionType, Asset, AssetType, Sector
from .events import anomalous_event

CROWN_JEWEL = "ehospital_app"
EMERGENCY = "emergency_ops"

META = {
    "id": "aiims",
    "title": "AIIMS Delhi (November 2022)",
    "kind": "reconstruction",
    "sector": "health",
    "one_liner": (
        "Five eHospital servers encrypted (~1.3 TB). CERT-In: improper "
        "segmentation. Isolate the island; do not yank emergency care."
    ),
    "sources": [
        "https://www.thehindu.com/news/national/13-tb-data-encrypted-in-ransomware-attack-on-aiims-by-unknown-threat-actors-centre/article66271226.ece",
        "https://sansad.in/getFile/loksabhaquestions/annex/1710/AU1837.pdf",
    ],
    "disclaimer": (
        "Public-source reconstruction from parliamentary / CERT-In reporting. "
        "Not victim telemetry. The five hosts were already encrypted — this "
        "engine does not decrypt. The case is the isolation decision given "
        "no segmentation, not 'eHospital would have stayed fully up'."
    ),
}


def build_graph() -> AttackGraph:
    ag = AttackGraph()
    for asset in [
        Asset(asset_id="internet", sector=Sector.INTERNET,
              asset_type=AssetType.INTERNET, criticality=1),
        Asset(asset_id="campus_jump", sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=3),
        Asset(asset_id="ehosp_s1", sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=4,
              tags=["ehospital_cluster"]),
        Asset(asset_id="ehosp_s2", sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=4,
              tags=["ehospital_cluster"]),
        Asset(asset_id=CROWN_JEWEL, sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=5,
              is_crown_jewel=True, tags=["patient_management"]),
        Asset(asset_id=EMERGENCY, sector=Sector.HEALTH,
              asset_type=AssetType.SERVICE_LOAD, criticality=5,
              tags=["emergency_care"]),
    ]:
        ag.add_asset(asset)

    ag.add_edge("internet", "campus_jump",
                exploit_cost=2.0, cut_cost=1.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("campus_jump", "ehosp_s1",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("campus_jump", "ehosp_s2",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("ehosp_s1", CROWN_JEWEL,
                exploit_cost=1.0, cut_cost=3.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("ehosp_s2", CROWN_JEWEL,
                exploit_cost=1.0, cut_cost=3.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge(CROWN_JEWEL, EMERGENCY,
                exploit_cost=99.0, cut_cost=100.0, protected=True,
                action_type=ActionType.BLOCK_LINK)
    return ag


def telemetry_stream():
    return [
        anomalous_event("campus_jump", "T1078", score=0.80),
        anomalous_event("ehosp_s1", "T1486", score=0.90,
                        bytes_out_zscore=2.8, process_count_zscore=2.2),
        anomalous_event("ehosp_s2", "T1486", score=0.89,
                        bytes_out_zscore=2.6, process_count_zscore=2.0),
    ]


def historical() -> dict:
    _, cost, severs = naive_containment_cost(build_graph(), CROWN_JEWEL)
    return {
        "decision": "Campus-scale eHospital outage (~two weeks of paper ops)",
        "availability_cost": cost,
        "severs_protected": severs,
        "narrative": (
            "No segmentation: the blast radius was the network. Isolate the "
            "alerting cluster; do not treat emergency ops as a cuttable edge."
        ),
    }
