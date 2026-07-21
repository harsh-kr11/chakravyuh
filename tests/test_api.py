"""Tests for the REST API, adapters, and export helpers."""
from __future__ import annotations

import json

import pytest

from chakravyuh.adapters import RealAdapter, ScenarioAdapter
from chakravyuh.export import result_to_dict, write_bundle
from chakravyuh.orchestrator import Orchestrator
from chakravyuh.scenarios import redecho


def test_scenario_adapter_drives_pipeline():
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    assert result.plan.crown_jewel_protected is True
    assert result.audit_ok is True


def test_real_adapter_refuses_without_ack():
    with pytest.raises(RuntimeError):
        RealAdapter()


def test_export_roundtrips_to_dict():
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    data = result_to_dict(result, orch)
    # JSON-serialisable and self-consistent
    blob = json.dumps(data, default=str)
    assert "interdiction" in data
    assert data["interdiction"]["crown_jewel_protected"] is True
    assert data["audit"]["ok"] is True
    assert len(blob) > 100


def test_write_bundle_creates_files(tmp_path):
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    paths = write_bundle(result, orch, str(tmp_path))
    for key in ("incident", "report", "audit"):
        assert (tmp_path / f"{key}.json").exists() or (tmp_path).joinpath(
            paths[key].split("/")[-1]
        ).exists()


def test_api_analyze_endpoint():
    pytest.importorskip("fastapi")  # skip if [api] not installed
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"

    resp = client.post("/incidents/analyze", json={"incident_id": "INC-API"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["incident_id"] == "INC-API"
    assert body["interdiction"]["crown_jewel_protected"] is True
    assert body["interdiction"]["cascade_averted"] is True
    assert body["audit"]["ok"] is True


def test_api_scenario_endpoint():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    sc = client.get("/scenario").json()
    assert sc["crown_jewel"] == redecho.CROWN_JEWEL
    assert len(sc["nodes"]) == 8
    assert len(sc["edges"]) == 8


def test_api_analyze_persists_and_is_listable(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    resp = client.post("/incidents/analyze", json={"incident_id": "INC-PERSIST"})
    assert resp.status_code == 200
    body = resp.json()
    db_id = body["db_id"]
    assert isinstance(db_id, int)

    listed = client.get("/incidents").json()
    assert any(
        row["id"] == db_id and row["incident_id"] == "INC-PERSIST" for row in listed
    )

    fetched = client.get(f"/incidents/{db_id}").json()
    assert fetched["incident_id"] == "INC-PERSIST"
    assert fetched["interdiction"]["crown_jewel_protected"] is True

    assert client.get("/incidents/999999").status_code == 404


def test_api_copilot_endpoints(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("sklearn")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHAKRAVYUH_LLM_PROVIDER", "none")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    analyze_resp = client.post(
        "/incidents/analyze", json={"incident_id": "INC-COPILOT"}
    )
    db_id = analyze_resp.json()["db_id"]

    brief = client.get(f"/incidents/{db_id}/briefing")
    assert brief.status_code == 200
    body = brief.json()
    assert body["llm_used"] is False
    assert isinstance(body["citations"], list)

    ask = client.post(
        f"/incidents/{db_id}/ask", json={"question": "What happened here?"}
    )
    assert ask.status_code == 200
    assert isinstance(ask.json()["text"], str)

    assert client.get("/incidents/999999/briefing").status_code == 404
