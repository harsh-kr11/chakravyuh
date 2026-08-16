"""Synnovis / NHS pathology ransomware (June 2024).

A lab — not a hospital — went down. Blood-result delay contributed to a
patient death. That result path is the protected edge.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..graph.interdiction import naive_containment_cost
from ..schemas import ActionType, Asset, AssetType, Sector
from .events import anomalous_event

CROWN_JEWEL = "lab_lis"
ICU_RESULTS = "icu_blood_results"

META = {
    "id": "synnovis",
    "title": "Synnovis / NHS pathology (June 2024)",
    "kind": "reconstruction",
    "sector": "health",
    "one_liner": (
        "Qilin hit a blood lab serving London hospitals. Delayed results "
        "contributed to a patient death. Never cut the ICU result path."
    ),
    "sources": [
        "https://www.bbc.com/news/articles/cgr0yd67y9jo",
        "https://www.reuters.com/world/uk/cyberattack-london-hospitals-causes-further-disruption-2024-06-12/",
    ],
    "disclaimer": (
        "Public-source reconstruction from contemporaneous reporting and the "
        "King's College Hospital trust statement. Not victim telemetry. "
        "Cross-organisation dependency (lab → ICU), modelled as a protected edge."
    ),
}


def build_graph() -> AttackGraph:
    ag = AttackGraph()
    for asset in [
        Asset(asset_id="internet", sector=Sector.INTERNET,
              asset_type=AssetType.INTERNET, criticality=1),
        Asset(asset_id="lab_workstation", sector=Sector.HEALTH,
              asset_type=AssetType.IT_HOST, criticality=3,
              tags=["pathology_it"]),
        Asset(asset_id="lab_fileserver", sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=3),
        Asset(asset_id=CROWN_JEWEL, sector=Sector.HEALTH,
              asset_type=AssetType.IT_SERVER, criticality=5,
              is_crown_jewel=True, tags=["lis"]),
        Asset(asset_id=ICU_RESULTS, sector=Sector.HEALTH,
              asset_type=AssetType.SERVICE_LOAD, criticality=5,
              tags=["icu", "patient_safety"]),
    ]:
        ag.add_asset(asset)

    ag.add_edge("internet", "lab_workstation",
                exploit_cost=2.0, cut_cost=1.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("lab_workstation", "lab_fileserver",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("lab_workstation", CROWN_JEWEL,
                exploit_cost=1.0, cut_cost=3.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("lab_fileserver", CROWN_JEWEL,
                exploit_cost=2.0, cut_cost=4.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge(CROWN_JEWEL, ICU_RESULTS,
                exploit_cost=99.0, cut_cost=100.0, protected=True,
                action_type=ActionType.BLOCK_LINK)
    return ag


def telemetry_stream():
    return [
        anomalous_event("lab_workstation", "T1486", score=0.91,
                        bytes_out_zscore=2.9, process_count_zscore=2.4,
                        privilege_level=2),
    ]


def historical() -> dict:
    _, cost, severs = naive_containment_cost(build_graph(), CROWN_JEWEL)
    return {
        "decision": "Lab LIS outage; hospitals lost blood results for days",
        "availability_cost": cost,
        "severs_protected": severs,
        "narrative": (
            "Naive isolation of the LIS severs the ICU result feed. Isolate "
            "the compromised lab workstation instead."
        ),
    }
