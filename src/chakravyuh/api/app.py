"""FastAPI service exposing the CHAKRAVYUH pipeline.

Endpoints
---------
GET  /healthz                 liveness probe
GET  /scenario                the bundled demo scenario (graph + events) as JSON
POST /incidents/analyze       run the pipeline on a scenario or supplied payload
GET  /                        minimal service description

The service is deterministic and stateless per request. It is intended to sit
behind the command-centre dashboard and behind an authenticating gateway in
production (auth is deliberately out of scope for this reference).
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from .. import __version__
from ..adapters import ScenarioAdapter
from ..agents import AgentConfig
from ..config import load_settings
from ..export import result_to_dict
from ..orchestrator import Orchestrator
from ..scenarios import redecho

app = FastAPI(title="CHAKRAVYUH", version=__version__)


class AnalyzeRequest(BaseModel):
    incident_id: str = "INC-0001"
    scenario: str = "redecho"        # only bundled scenario for now
    anomaly_threshold: float | None = None


def _orchestrator(req: AnalyzeRequest) -> Orchestrator:
    settings = load_settings()
    cfg = AgentConfig(
        anomaly_threshold=(
            req.anomaly_threshold
            if req.anomaly_threshold is not None
            else settings.anomaly_threshold
        ),
        blast_radius_threshold=settings.blast_radius_threshold,
    )
    return Orchestrator(cfg)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "CHAKRAVYUH",
        "version": __version__,
        "description": "Incident-time cross-sector attack-path interdiction",
        "endpoints": ["/healthz", "/scenario", "/incidents/analyze"],
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/scenario")
def scenario() -> dict[str, Any]:
    ag = redecho.build_graph()
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
            "src": u, "dst": v,
            "exploit_cost": d["exploit_cost"],
            "cut_cost": d["cut_cost"],
            "protected": d["protected"],
        }
        for u, v, d in ag.g.edges(data=True)
    ]
    events = [e.model_dump(mode="json") for e in redecho.telemetry_stream()]
    return {"nodes": nodes, "edges": edges, "events": events,
            "crown_jewel": redecho.CROWN_JEWEL}


@app.post("/incidents/analyze")
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    orch = _orchestrator(req)
    adapter = ScenarioAdapter(redecho)
    result = orch.run_adapter(adapter, incident_id=req.incident_id)
    return result_to_dict(result, orch)
