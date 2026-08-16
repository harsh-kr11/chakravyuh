"""FastAPI service exposing the CHAKRAVYUH pipeline.

Endpoints
---------
GET  /healthz                 liveness probe
GET  /scenario                the bundled demo scenario (graph + events) as JSON
GET  /schema/telemetry-event  JSON schema for the event shape a translator must produce
POST /incidents/analyze       run the pipeline (observe-only, or propose+respond),
                               persisting the result
POST /incidents/{id}/approve  resolve a pending human-gated action (approve or deny)
GET  /incidents               list previously analyzed incidents (summary)
GET  /incidents/{id}          fetch one persisted incident's full result
GET  /incidents/{id}/briefing read-only, RAG-grounded LLM narrative for the incident
POST /incidents/{id}/ask      ask the analyst copilot a free-text question about it
GET  /                        minimal service description

Two request modes, chosen via ``AnalyzeRequest.mode``:
  - "observe": compute and show the plan, execute nothing at all (not even
    low-risk autonomous actions). For a first, safe look at what the system
    would do.
  - "respond" (default): low-risk actions execute immediately; anything
    requiring a human gate is left genuinely *pending* — no auto-approval —
    until a real ``POST /incidents/{id}/approve`` call resolves it. This is
    the real human-in-the-loop path; see ``chakravyuh.agents.response``.

The copilot endpoints are entirely read-only: they explain an
already-computed incident using retrieved ATT&CK/CVE/CERT-In context. They
never select or influence containment actions (see
``chakravyuh.agents.copilot``), and are optional — with no LLM provider
configured they still return the retrieved context, just without
LLM-generated prose.

Each analyze run is persisted to a SQLite-backed store (see
``chakravyuh.store``) so incidents survive process restarts and can be
listed/replayed/resolved later. The service is intended to sit behind the
command-centre dashboard and behind an authenticating gateway in production
(auth is deliberately out of scope for this reference).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .. import __version__
from ..adapters import ReplayAdapter, ScenarioAdapter
from ..agents import AgentConfig, pending_approval
from ..agents.copilot import CopilotAgent
from ..config import load_settings
from ..connectors import make_connector
from ..export import result_to_dict
from ..orchestrator import Orchestrator
from ..scenarios.catalog import DEFAULT_ID, list_meta, payload
from ..scenarios.catalog import get as get_scenario
from ..schemas import AuditRecord, ContainmentAction, TelemetryEvent
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
    scenario: str = DEFAULT_ID
    anomaly_threshold: float | None = None
    mode: Literal["observe", "respond"] = "respond"
    # Bring-your-own telemetry: a real translator's output. Omit to use the
    # bundled demo events. The attack-graph *topology* is still the bundled
    # one either way — see docs/INTEGRATION.md for that boundary.
    events: list[TelemetryEvent] | None = None


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
    if req.mode == "observe":
        # Gate/connector are irrelevant: observe_only skips execution outright.
        return Orchestrator(cfg)
    return Orchestrator(cfg, gate=pending_approval, connector=make_connector(settings))


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "CHAKRAVYUH",
        "version": __version__,
        "description": "Incident-time cross-sector attack-path interdiction",
        "endpoints": [
            "/healthz", "/readyz", "/scenarios", "/scenario",
            "/schema/telemetry-event",
            "/incidents/analyze", "/incidents/{id}/approve",
            "/incidents", "/incidents/{id}",
            "/incidents/{id}/briefing", "/incidents/{id}/ask",
        ],
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, Any]:
    settings = load_settings()
    try:
        import sklearn  # noqa: F401
        detect = "sklearn"
    except ImportError:
        detect = "heuristic"
    try:
        from ..knowledge.graph import get_graph
        kg = get_graph() is not None
    except Exception:
        kg = False
    store_ok = True
    try:
        get_store().list(limit=1)
    except Exception:
        store_ok = False
    return {
        "status": "ok",
        "detect": detect,
        "llm_provider": settings.llm_provider,
        "llm_enabled": settings.llm_enabled,
        "neo4j": kg,
        "store": store_ok,
    }


@app.get("/scenarios")
def scenarios() -> list[dict[str, Any]]:
    return list_meta()


@app.get("/scenario")
def scenario(id: str = DEFAULT_ID) -> dict[str, Any]:
    try:
        mod = get_scenario(id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"unknown scenario {id!r}"
        ) from exc
    return payload(mod)


@app.get("/schema/telemetry-event")
def telemetry_event_schema() -> dict[str, Any]:
    """The exact JSON shape a translator must produce per event. Feed a list
    of these as ``events`` to ``POST /incidents/analyze`` — see
    docs/INTEGRATION.md for a worked, language-agnostic example.
    """
    return TelemetryEvent.model_json_schema()


@app.post("/incidents/analyze")
def analyze(
    req: AnalyzeRequest, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    try:
        mod = get_scenario(req.scenario)
    except KeyError as exc:
        raise HTTPException(
            status_code=400, detail=f"unknown scenario {req.scenario!r}"
        ) from exc
    orch = _orchestrator(req)
    if req.events is not None:
        adapter = ReplayAdapter(mod.build_graph(), req.events, mod.CROWN_JEWEL)
    else:
        adapter = ScenarioAdapter(mod)
    result = orch.run_adapter(
        adapter, incident_id=req.incident_id, observe_only=req.mode == "observe",
    )
    data = result_to_dict(result, orch)
    data["mode"] = req.mode
    data["scenario"] = req.scenario
    data["meta"] = mod.META
    data["historical"] = mod.historical()
    _apply_actual_outcome(data)
    data["db_id"] = store.save(req.incident_id, req.scenario, data)
    return data


def _get_incident_or_404(row_id: int, store: IncidentStore) -> dict[str, Any]:
    data = store.get(row_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"incident {row_id} not found")
    return data


def _apply_actual_outcome(data: dict[str, Any]) -> None:
    """Recompute the *actual*, not just planned, outcome from real execution
    state. ``all([])`` is True in Python — an empty action list must not look
    like a successful containment.
    """
    executions = data.get("executions") or []
    all_executed = bool(executions) and all(e.get("executed") for e in executions)
    interdiction = data["interdiction"]
    interdiction["crown_jewel_protected_now"] = (
        bool(interdiction.get("crown_jewel_protected")) and all_executed
    )
    interdiction["cascade_averted_now"] = (
        bool(interdiction.get("cascade_averted")) and all_executed
    )
    data["has_pending"] = any(e.get("pending") for e in executions)


def _append_audit_record(
    records: list[dict[str, Any]], actor: str, event_type: str, payload: dict[str, Any]
) -> None:
    prev_hash = records[-1]["hash"] if records else ""
    rec = AuditRecord(
        seq=len(records), actor=actor, event_type=event_type,
        payload=payload, prev_hash=prev_hash,
    )
    rec.hash = rec.compute_hash()
    records.append(rec.model_dump(mode="json"))


def _verify_audit_chain(records: list[dict[str, Any]]) -> bool:
    prev_hash = ""
    for r in records:
        if r["prev_hash"] != prev_hash:
            return False
        rec = AuditRecord.model_validate(r)
        if rec.hash != rec.compute_hash():
            return False
        prev_hash = rec.hash
    return True


class ApproveRequest(BaseModel):
    approved: bool
    approver: str = "analyst"
    # Which pending action to resolve; omit to resolve ALL pending actions
    # the same way (matches a single dashboard "Approve & contain" click).
    action_index: int | None = None


@app.post("/incidents/{row_id}/approve")
def approve(
    row_id: int, req: ApproveRequest, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    data = _get_incident_or_404(row_id, store)
    executions = data.get("executions") or []
    pending_idxs = [i for i, e in enumerate(executions) if e.get("pending")]
    if req.action_index is not None:
        pending_idxs = [i for i in pending_idxs if i == req.action_index]
    if not pending_idxs:
        raise HTTPException(
            status_code=400, detail="no matching pending action(s) to resolve"
        )

    connector = make_connector(load_settings())
    records = data["audit"]["records"]
    addendum_lines: list[str] = []

    for i in pending_idxs:
        entry = executions[i]
        action = ContainmentAction.model_validate(entry["action"])
        _append_audit_record(records, "response", "human_decision", {
            "action": action.action_type.value, "target": str(action.target),
            "approved": req.approved, "approver": req.approver,
        })
        if req.approved:
            if connector is not None:
                outcome = connector.execute(action, incident_id=data["incident_id"])
                ok, detail = outcome.ok, outcome.detail
            else:
                ok, detail = True, "simulated"
            if ok:
                entry.update(
                    executed=True, pending=False, approved_by=req.approver, error=None,
                )
                addendum_lines.append(
                    f"  - {action.action_type.value} -> {action.target}: "
                    f"APPROVED by {req.approver} (executed=True)"
                )
                _append_audit_record(records, "response", "action_result", {
                    "action": action.action_type.value, "executed": True,
                    "approved_by": req.approver,
                })
            else:
                # A connector failure is a technical problem, not a human
                # decision -- stay pending so this specific action can be
                # retried (e.g. once a transient network issue clears)
                # rather than getting stuck unresolved forever.
                entry.update(
                    executed=False, pending=True,
                    approved_by=req.approver, error=detail,
                )
                addendum_lines.append(
                    f"  - {action.action_type.value} -> {action.target}: "
                    f"APPROVED by {req.approver} but NOT executed -- connector "
                    f"error ({detail}); still pending, retry with another approve call"
                )
                _append_audit_record(records, "response", "action_execution_failed", {
                    "action": action.action_type.value, "approved_by": req.approver,
                    "error": detail,
                })
        else:
            entry.update(executed=False, pending=False, approved_by=None, error=None)
            addendum_lines.append(
                f"  - {action.action_type.value} -> {action.target}: "
                f"DENIED by {req.approver}"
            )
            _append_audit_record(records, "response", "action_result", {
                "action": action.action_type.value, "executed": False,
                "approved_by": None,
            })

    data["certin_report"] += (
        "\n\nADDENDUM - human decisions recorded after initial draft:\n"
        + "\n".join(addendum_lines) + "\n"
    )
    data["audit"]["ok"] = _verify_audit_chain(records)
    data["metrics"]["mttr_steps"] = len([e for e in executions if e["executed"]])
    _apply_actual_outcome(data)

    store.update(row_id, data)
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
    data = _get_incident_or_404(row_id, store)
    _apply_actual_outcome(data)
    data["db_id"] = row_id
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
    history: list[dict[str, str]] | None = None


@app.post("/incidents/{row_id}/ask")
def ask(
    row_id: int, req: AskRequest, store: IncidentStore = Depends(get_store)
) -> dict[str, Any]:
    data = _get_incident_or_404(row_id, store)
    result = CopilotAgent().ask(data, req.question, history=req.history)
    return {
        "text": result.text,
        "citations": result.citations,
        "llm_used": result.llm_used,
    }
