"""Colonial Pipeline (May 2021) — IT ransomware, don't shut OT.

Public-source reconstruction. Not Colonial's telemetry.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..graph.interdiction import naive_containment_cost
from ..schemas import ActionType, Asset, AssetType, Sector
from .events import anomalous_event

CROWN_JEWEL = "pipeline_scada"
FUEL_LOAD = "fuel_east_coast"

META = {
    "id": "colonial",
    "title": "Colonial Pipeline (May 2021)",
    "kind": "reconstruction",
    "sector": "energy",
    "one_liner": (
        "DarkSide hit IT only. Operators halted 5,500 miles of pipeline OT. "
        "The outage was the containment decision."
    ),
    "sources": [
        "https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-131a",
        "https://www.congress.gov/117/meeting/house/112689/witnesses/HHRG-117-HM00-Wstate-BlountJ-20210609.pdf",
    ],
    "disclaimer": (
        "Public-source reconstruction from CISA AA21-131A and CEO testimony. "
        "Not victim telemetry. OT was not known compromised; they shut it anyway."
    ),
}


def build_graph() -> AttackGraph:
    ag = AttackGraph()
    for asset in [
        Asset(asset_id="internet", sector=Sector.INTERNET,
              asset_type=AssetType.INTERNET, criticality=1),
        Asset(asset_id="vpn_account", sector=Sector.POWER,
              asset_type=AssetType.IDENTITY, criticality=3,
              tags=["legacy_vpn", "no_mfa"]),
        Asset(asset_id="it_workstation", sector=Sector.POWER,
              asset_type=AssetType.IT_HOST, criticality=2),
        Asset(asset_id="it_billing", sector=Sector.POWER,
              asset_type=AssetType.IT_SERVER, criticality=3),
        Asset(asset_id="ot_jump", sector=Sector.POWER,
              asset_type=AssetType.IT_SERVER, criticality=4,
              tags=["it_ot_boundary"]),
        Asset(asset_id=CROWN_JEWEL, sector=Sector.POWER,
              asset_type=AssetType.OT_SCADA, criticality=5,
              is_crown_jewel=True, tags=["pipeline_control"]),
        Asset(asset_id=FUEL_LOAD, sector=Sector.TRANSPORT,
              asset_type=AssetType.SERVICE_LOAD, criticality=5,
              tags=["east_coast_fuel"]),
    ]:
        ag.add_asset(asset)

    ag.add_edge("internet", "vpn_account",
                exploit_cost=1.0, cut_cost=1.0,
                action_type=ActionType.REVOKE_CREDENTIAL)
    ag.add_edge("vpn_account", "it_workstation",
                exploit_cost=1.0, cut_cost=1.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("it_workstation", "it_billing",
                exploit_cost=1.0, cut_cost=2.0,
                action_type=ActionType.ISOLATE_HOST)
    ag.add_edge("it_workstation", "ot_jump",
                exploit_cost=2.0, cut_cost=2.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge("ot_jump", CROWN_JEWEL,
                exploit_cost=3.0, cut_cost=15.0,
                action_type=ActionType.BLOCK_LINK)
    ag.add_edge(CROWN_JEWEL, FUEL_LOAD,
                exploit_cost=99.0, cut_cost=100.0, protected=True,
                action_type=ActionType.BLOCK_LINK)
    return ag


def telemetry_stream():
    return [
        anomalous_event("vpn_account", "T1133", score=0.86,
                        failed_logins_1h=3, privilege_level=2),
        anomalous_event("it_workstation", "T1486", score=0.88,
                        bytes_out_zscore=2.4, process_count_zscore=2.1),
    ]


def historical() -> dict:
    _, cost, severs = naive_containment_cost(build_graph(), CROWN_JEWEL)
    return {
        "decision": "Proactive shutdown of 5,500 miles of pipeline OT",
        "availability_cost": cost,
        "severs_protected": severs,
        "narrative": (
            "IT-only DarkSide. Operators halted OT because they could not see "
            "a finite cut. Fuel delivery is the protected load."
        ),
    }
