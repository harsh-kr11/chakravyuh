"""Ukraine electric power attack (December 2015) — MITRE C0028.

Public-source reconstruction. Cut before the HMI, not the breaker circuit.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..graph.interdiction import naive_containment_cost
from ..schemas import ActionType, Asset, AssetType, Sector
from .events import anomalous_event

CROWN_JEWEL = "scada_hmi"
CIVILIAN_LOAD = "civilian_hospital_load"

META = {
    "id": "ukraine2015",
    "title": "Ukraine power grid (December 2015)",
    "kind": "reconstruction",
    "sector": "power",
    "one_liner": (
        "Sandworm reached SCADA HMIs and opened breakers. ~225k customers. "
        "Cut upstream of the HMI."
    ),
    "sources": [
        "https://attack.mitre.org/campaigns/C0028/",
        "https://www.cisa.gov/news-events/ics-alerts/ir-alert-h-16-056-01",
    ],
    "disclaimer": (
        "Public-source reconstruction from MITRE C0028 and CISA/SANS reporting. "
        "Not victim telemetry."
    ),
}


def build_graph() -> AttackGraph:
    ag = AttackGraph()
    for asset in [
        Asset(asset_id="internet", sector=Sector.INTERNET,
              asset_type=AssetType.INTERNET, criticality=1),
        Asset(asset_id="spearphish_pc", sector=Sector.POWER,
              asset_type=AssetType.IT_HOST, criticality=2),
        Asset(asset_id="engineer_cred", sector=Sector.POWER,
              asset_type=AssetType.IDENTITY, criticality=3),
        Asset(asset_id="ics_vpn", sector=Sector.POWER,
              asset_type=AssetType.IT_SERVER, criticality=4),
        Asset(asset_id=CROWN_JEWEL, sector=Sector.POWER,
              asset_type=AssetType.OT_SCADA, criticality=5,
              is_crown_jewel=True, tags=["hmi"]),
        Asset(asset_id=CIVILIAN_LOAD, sector=Sector.HEALTH,
              asset_type=AssetType.SERVICE_LOAD, criticality=5,
              tags=["hospital"]),
    ]:
        ag.add_asset(asset)

    ag.add_edge("internet", "spearphish_pc",
                exploit_cost=2.0, cut_cost=1.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("spearphish_pc", "engineer_cred",
                exploit_cost=1.0, cut_cost=1.0,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_edge("engineer_cred", "ics_vpn",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_edge("ics_vpn", CROWN_JEWEL,
                exploit_cost=2.0, cut_cost=12.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge(CROWN_JEWEL, CIVILIAN_LOAD,
                exploit_cost=99.0, cut_cost=100.0, protected=True,
                action_type=ActionType.BLOCK_LINK)
    return ag


def telemetry_stream():
    # Detected on IT — before HMI. That is the whole point.
    return [
        anomalous_event("spearphish_pc", "T1566", score=0.81),
        anomalous_event("engineer_cred", "T1003", score=0.87,
                        failed_logins_1h=4, privilege_level=2),
    ]


def historical() -> dict:
    _, cost, severs = naive_containment_cost(build_graph(), CROWN_JEWEL)
    return {
        "decision": "Attackers reached HMI; operators later took SCADA offline",
        "availability_cost": cost,
        "severs_protected": severs,
        "narrative": (
            "The lights went out at the HMI. Interdiction here is upstream: "
            "stolen creds / ICS VPN, not the breaker circuit."
        ),
    }
