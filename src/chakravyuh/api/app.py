"""FastAPI service exposing the CHAKRAVYUH pipeline.

Endpoints
---------
GET  /healthz                 liveness probe
GET  /scenario                the bundled demo scenario (graph + events) as JSON
POST /incidents/analyze       run the pipeline on a scenario or supplied payload,
                               persisting the result
GET  /incidents               list previously analyzed incidents (summary)
GET  /incidents/{id}          fetch one persisted incident's full result
GET  /incidents/{id}/briefing read-only, RAG-grounded LLM narrative for the incident
POST /incidents/{id}/ask      ask the analyst copilot a free-text question about it
GET  /                        minimal service description

The copilot endpoints are entirely read-only: they explain an
already-computed, already-executed containment plan using retrieved
ATT&CK/CVE/CERT-In context. They never select or influence containment
actions (see ``chakravyuh.agents.copilot``), and are optional — with no LLM
provider configured they still return the retrieved context, just without
LLM-generated prose.

Each analyze run is persisted to a SQLite-backed store (see ``chakravyuh.store``)
so incidents survive process restarts and can be listed/replayed. The service
is intended to sit behind the command-centre dashboard and behind an
authenticating gateway in production (auth is deliberately out of scope for
this reference).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .. import __version__
from ..adapters import ScenarioAdapter
from ..agents import AgentConfig
from ..agents.copilot import CopilotAgent
from ..config import load_settings
from ..export import result_to_dict
from ..orchestrator import Orchestrator
from ..scenarios import redecho
from ..store import IncidentStore

app = FastAPI(title="CHAKRAVYUH", version=__version__)

# Dashboard is a self-contained static page that may be served from a
# different origin/port than the API; allow it. Tighten this in a real
# deployment (specific origins) once auth is in front of the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def _store_for(db_path: str) -> IncidentStore:
    return IncidentStore(db_path)


def get_store() -> IncidentStore:
    return _store_for(load_settings().db_path)


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
        "endpoints": [
            "/healthz", "/scenario", "/incidents/analyze",
            "/incidents", "/incidents/{id}",
            "/incidents/{id}/briefing", "/incidents/{id}/ask",
        ],
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
def analyze(
    req: AnalyzeRequest, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    orch = _orchestrator(req)
    adapter = ScenarioAdapter(redecho)
    result = orch.run_adapter(adapter, incident_id=req.incident_id)
    data = result_to_dict(result, orch)
    data["db_id"] = store.save(req.incident_id, req.scenario, data)
    return data


@app.get("/incidents")
def list_incidents(
    limit: int = 50, store: IncidentStore = Depends(get_store)
) -> list[dict[str, Any]]:
    return store.list(limit=limit)


@app.get("/incidents/{row_id}")
def get_incident(
    row_id: int, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    data = store.get(row_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"incident {row_id} not found")
    return data


def _get_incident_or_404(row_id: int, store: IncidentStore) -> dict[str, Any]:
    data = store.get(row_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"incident {row_id} not found")
    return data


@app.get("/incidents/{row_id}/briefing")
def briefing(
    row_id: int, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    data = _get_incident_or_404(row_id, store)
    result = CopilotAgent().brief(data)
    return {
        "text": result.text,
        "citations": result.citations,
        "llm_used": result.llm_used,
    }


class AskRequest(BaseModel):
    question: str


@app.post("/incidents/{row_id}/ask")
def ask(
    row_id: int, req: AskRequest, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    data = _get_incident_or_404(row_id, store)
    result = CopilotAgent().ask(data, req.question)
    return {
        "text": result.text,
        "citations": result.citations,
        "llm_used": result.llm_used,
    }
