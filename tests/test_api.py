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


def test_api_ask_with_history(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("sklearn")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHAKRAVYUH_LLM_PROVIDER", "none")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-CHAT"}
    ).json()["db_id"]

    resp = client.post(
        f"/incidents/{db_id}/ask",
        json={
            "question": "and what about the domain controller?",
            "history": [
                {"question": "why was engineer_cred revoked?",
                 "answer": "it was part of the attacker's frontier."},
            ],
        },
    )
    assert resp.status_code == 200
    assert isinstance(resp.json()["text"], str)


def test_api_observe_mode_executes_nothing(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    resp = client.post(
        "/incidents/analyze",
        json={"incident_id": "INC-OBSERVE", "mode": "observe"},
    )
    body = resp.json()
    assert body["mode"] == "observe"
    assert body["has_pending"] is False
    assert all(not e["executed"] for e in body["executions"])
    assert all(not e["pending"] for e in body["executions"])
    # the plan itself is still fully computed and shown...
    assert body["interdiction"]["crown_jewel_protected"] is True
    # ...but nothing actually happened, so the real outcome must say so
    assert body["interdiction"]["crown_jewel_protected_now"] is False
    assert body["interdiction"]["cascade_averted_now"] is False


def test_api_respond_mode_leaves_gated_actions_pending(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    resp = client.post(
        "/incidents/analyze",
        json={"incident_id": "INC-RESPOND", "mode": "respond"},
    )
    body = resp.json()
    assert body["mode"] == "respond"
    assert body["has_pending"] is True
    gated = [e for e in body["executions"] if e["gated"]]
    ungated = [e for e in body["executions"] if not e["gated"]]
    assert all(e["pending"] and not e["executed"] for e in gated)
    assert all(e["executed"] and not e["pending"] for e in ungated)
    # a gated action is still pending -> not actually protected yet
    assert body["interdiction"]["crown_jewel_protected_now"] is False


def test_api_approve_executes_pending_action(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-APPROVE"}
    ).json()["db_id"]

    approved = client.post(
        f"/incidents/{db_id}/approve",
        json={"approved": True, "approver": "test-analyst"},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["has_pending"] is False
    assert all(not e["pending"] for e in body["executions"])
    gated = [e for e in body["executions"] if e["gated"]]
    assert all(e["executed"] and e["approved_by"] == "test-analyst" for e in gated)
    assert "ADDENDUM" in body["certin_report"]
    assert body["audit"]["ok"] is True
    # everything approved and executed -> the *actual* outcome now matches
    # the plan's theoretical guarantee, not just the plan on paper
    assert body["interdiction"]["crown_jewel_protected_now"] is True
    assert body["interdiction"]["cascade_averted_now"] is True

    # persisted, not just returned in-response
    refetched = client.get(f"/incidents/{db_id}").json()
    assert refetched["has_pending"] is False
    assert "ADDENDUM" in refetched["certin_report"]


def test_api_deny_leaves_action_unexecuted(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-DENY"}
    ).json()["db_id"]

    denied = client.post(
        f"/incidents/{db_id}/approve",
        json={"approved": False, "approver": "test-analyst"},
    )
    body = denied.json()
    gated = [e for e in body["executions"] if e["gated"]]
    assert all(not e["executed"] and not e["pending"] for e in gated)
    assert "DENIED" in body["certin_report"]
    # a required action was denied -- the *actual* outcome must say so even
    # though the original plan (on paper) claimed full protection. This is
    # the field any third-party API consumer should check, not
    # crown_jewel_protected, which never changes after the fact.
    plan = body["interdiction"]
    assert plan["crown_jewel_protected"] is True   # unchanged (plan-level)
    assert plan["crown_jewel_protected_now"] is False  # real, honest state
    assert plan["cascade_averted_now"] is False


def test_api_approve_retries_after_connector_failure(tmp_path, monkeypatch):
    """A connector failure (e.g. a network blip) is a technical problem, not
    a human decision -- the action must stay retryable, not get stuck."""
    pytest.importorskip("fastapi")
    from unittest.mock import MagicMock, patch

    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHAKRAVYUH_CONNECTOR", "webhook")
    monkeypatch.setenv("CHAKRAVYUH_WEBHOOK_URL", "https://example.invalid/hook")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-RETRY"}
    ).json()["db_id"]

    with patch("httpx.post", side_effect=ConnectionError("refused")):
        first = client.post(
            f"/incidents/{db_id}/approve", json={"approved": True, "approver": "a"},
        )
    assert first.status_code == 200
    body = first.json()
    gated = [e for e in body["executions"] if e["gated"]][0]
    assert gated["executed"] is False
    assert gated["pending"] is True  # stayed retryable, didn't get stuck
    assert "refused" in gated["error"]
    assert body["has_pending"] is True

    fake_response = MagicMock(status_code=200, text="")
    with patch("httpx.post", return_value=fake_response):
        second = client.post(
            f"/incidents/{db_id}/approve", json={"approved": True, "approver": "a"},
        )
    assert second.status_code == 200
    body2 = second.json()
    gated2 = [e for e in body2["executions"] if e["gated"]][0]
    assert gated2["executed"] is True
    assert gated2["pending"] is False
    assert gated2["error"] is None
    assert body2["has_pending"] is False


def test_api_approve_with_no_pending_actions_is_400(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-TWICE"}
    ).json()["db_id"]
    client.post(f"/incidents/{db_id}/approve", json={"approved": True})

    second = client.post(f"/incidents/{db_id}/approve", json={"approved": True})
    assert second.status_code == 400


def test_api_custom_events_override_bundled_scenario(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    custom_events = [
        {
            "asset_id": "it_jump_host",
            "kind": "auth",
            "features": {
                "off_hours": 1, "failed_logins_1h": 1, "new_asset_pair": 1,
                "bytes_out_zscore": 1.5, "process_count_zscore": 0.8,
                "privilege_level": 0, "session_duration_zscore": 0.5,
                "anomaly_score": 0.9,
            },
            "is_malicious": True,
            "technique_hint": "T1078",
        },
    ]
    resp = client.post(
        "/incidents/analyze",
        json={
            "incident_id": "INC-CUSTOM", "mode": "observe", "events": custom_events,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    flagged = {a["asset_id"] for a in body["anomalies"]}
    assert flagged == {"it_jump_host"}  # only the one custom event, nothing else


def test_api_scenarios_catalog():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    listed = client.get("/scenarios").json()
    ids = {row["id"] for row in listed}
    assert "colonial" in ids and "synnovis" in ids
    sc = client.get("/scenario?id=colonial").json()
    assert sc["crown_jewel"] == "pipeline_scada"
    assert sc["kind"] == "reconstruction"
    assert client.get("/scenario?id=nope").status_code == 404


def test_api_analyze_colonial(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    body = client.post(
        "/incidents/analyze",
        json={"incident_id": "INC-COL", "scenario": "colonial", "mode": "observe"},
    ).json()
    assert body["interdiction"]["crown_jewel_protected"] is True
    interdiction = body["interdiction"]
    assert interdiction["availability_cost"] < (
        interdiction["baseline_availability_cost"]
    )
    assert body["historical"]["severs_protected"] is True
    assert "PENDING" in body["certin_report"] or "PROPOSED" in body["certin_report"]
    assert body["interdiction"]["crown_jewel_protected_now"] is False


def test_api_deny_history_not_green(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CHAKRAVYUH_DB_PATH", str(tmp_path / "test.db"))
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    db_id = client.post(
        "/incidents/analyze", json={"incident_id": "INC-HIST"}
    ).json()["db_id"]
    client.post(
        f"/incidents/{db_id}/approve",
        json={"approved": False, "approver": "x"},
    )
    listed = client.get("/incidents").json()
    row = next(r for r in listed if r["id"] == db_id)
    assert row["crown_jewel_protected"] is False
    assert row["has_pending"] is False


def test_api_readyz():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    body = TestClient(app).get("/readyz").json()
    assert body["status"] == "ok"
    assert body["detect"] in {"sklearn", "heuristic"}
    assert "llm_enabled" in body
    assert body["store"] is True


def test_api_telemetry_event_schema_endpoint():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from chakravyuh.api.app import app

    client = TestClient(app)
    resp = client.get("/schema/telemetry-event")
    assert resp.status_code == 200
    schema = resp.json()
    assert "asset_id" in schema["properties"]
    assert "features" in schema["properties"]
