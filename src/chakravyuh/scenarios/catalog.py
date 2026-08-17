"""Scenario catalog — public-source reconstructions plus the RedEcho illustration."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from . import aiims, colonial, redecho, synnovis, ukraine2015

SCENARIOS: dict[str, ModuleType] = {
    redecho.META["id"]: redecho,
    colonial.META["id"]: colonial,
    ukraine2015.META["id"]: ukraine2015,
    aiims.META["id"]: aiims,
    synnovis.META["id"]: synnovis,
}

DEFAULT_ID = redecho.META["id"]


def get(scenario_id: str) -> ModuleType:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        raise KeyError(f"unknown scenario {scenario_id!r}") from exc


def list_meta() -> list[dict[str, Any]]:
    return [mod.META for mod in SCENARIOS.values()]


def payload(mod: ModuleType) -> dict[str, Any]:
    ag = mod.build_graph()
    nodes = [
        {
            "id": n,
            "sector": ag.asset(n).sector.value,
            "type": ag.asset(n).asset_type.value,
            "crown_jewel": ag.asset(n).is_crown_jewel,
        }
        for n in ag.g.nodes
    ]
    edges = [
        {
            "src": u,
            "dst": v,
            "exploit_cost": d["exploit_cost"],
            "cut_cost": d["cut_cost"],
            "protected": d["protected"],
        }
        for u, v, d in ag.g.edges(data=True)
    ]
    events = [e.model_dump(mode="json") for e in mod.telemetry_stream()]
    return {
        **mod.META,
        "nodes": nodes,
        "edges": edges,
        "events": events,
        "crown_jewel": mod.CROWN_JEWEL,
        "historical": mod.historical(),
    }
