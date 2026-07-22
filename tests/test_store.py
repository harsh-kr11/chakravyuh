"""Tests for the SQLite-backed incident store."""
from __future__ import annotations

from chakravyuh.adapters import ScenarioAdapter
from chakravyuh.export import result_to_dict
from chakravyuh.orchestrator import Orchestrator
from chakravyuh.scenarios import redecho
from chakravyuh.store import IncidentStore


def _sample_result(incident_id: str = "INC-1") -> dict:
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho), incident_id=incident_id)
    return result_to_dict(result, orch)


def test_store_roundtrip(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.db"))
    data = _sample_result("INC-1")
    row_id = store.save("INC-1", "redecho", data)
    assert row_id >= 1

    listing = store.list()
    assert len(listing) == 1
    assert listing[0]["incident_id"] == "INC-1"
    assert listing[0]["scenario"] == "redecho"
    assert listing[0]["crown_jewel_protected"] is True

    fetched = store.get(row_id)
    assert fetched is not None
    assert fetched["incident_id"] == "INC-1"
    assert store.get(row_id + 1) is None


def test_store_persists_across_instances(tmp_path):
    path = str(tmp_path / "incidents.db")
    data = _sample_result("INC-1")
    IncidentStore(path).save("INC-1", "redecho", data)

    reopened = IncidentStore(path)
    assert len(reopened.list()) == 1


def test_store_list_orders_newest_first(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.db"))
    first = store.save("INC-1", "redecho", _sample_result("INC-1"))
    second = store.save("INC-2", "redecho", _sample_result("INC-2"))

    listing = store.list()
    assert [row["id"] for row in listing] == [second, first]


def test_store_update_overwrites_result_blob(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.db"))
    data = _sample_result("INC-1")
    row_id = store.save("INC-1", "redecho", data)

    data["certin_report"] += "\nADDENDUM: approved by analyst"
    assert store.update(row_id, data) is True

    fetched = store.get(row_id)
    assert "ADDENDUM" in fetched["certin_report"]


def test_store_update_returns_false_for_missing_row(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.db"))
    assert store.update(999, {"incident_id": "x", "interdiction": {}}) is False
