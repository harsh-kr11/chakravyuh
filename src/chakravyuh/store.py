"""Persistent storage for analyzed incidents.

SQLite-backed (stdlib only, no extra dependency). Each pipeline run is stored
as one row: indexed summary columns for listing, plus the full result blob
(the same shape ``export.result_to_dict`` produces) for retrieval.

Summary columns track *execution* truth (``crown_jewel_protected_now`` /
pending), not the theoretical plan — so History cannot stay green after a deny.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class IncidentStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    crown_jewel_protected INTEGER NOT NULL,
                    cascade_averted INTEGER NOT NULL,
                    availability_cost REAL NOT NULL,
                    result_json TEXT NOT NULL
                )"""
            )
            cols = {
                row[1] for row in conn.execute("PRAGMA table_info(incidents)")
            }
            if "has_pending" not in cols:
                conn.execute(
                    "ALTER TABLE incidents ADD COLUMN has_pending "
                    "INTEGER NOT NULL DEFAULT 0"
                )

    @staticmethod
    def _summary(result: dict[str, Any]) -> tuple[int, int, float, int]:
        interdiction = result.get("interdiction", {})
        protected = int(bool(interdiction.get(
            "crown_jewel_protected_now",
            interdiction.get("crown_jewel_protected"),
        )))
        cascade = int(bool(interdiction.get(
            "cascade_averted_now",
            interdiction.get("cascade_averted"),
        )))
        cost = float(interdiction.get("availability_cost", 0.0))
        pending = int(bool(result.get("has_pending", False)))
        return protected, cascade, cost, pending

    def save(self, incident_id: str, scenario: str, result: dict[str, Any]) -> int:
        protected, cascade, cost, pending = self._summary(result)
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO incidents
                   (incident_id, scenario, created_at, crown_jewel_protected,
                    cascade_averted, availability_cost, result_json, has_pending)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    incident_id,
                    scenario,
                    datetime.now(timezone.utc).isoformat(),
                    protected,
                    cascade,
                    cost,
                    json.dumps(result, default=str),
                    pending,
                ),
            )
            if cur.lastrowid is None:
                raise RuntimeError("failed to persist incident")
            return int(cur.lastrowid)

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, incident_id, scenario, created_at,
                          crown_jewel_protected, cascade_averted,
                          availability_cost, has_pending
                   FROM incidents ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            {
                "id": r["id"],
                "incident_id": r["incident_id"],
                "scenario": r["scenario"],
                "created_at": r["created_at"],
                "crown_jewel_protected": bool(r["crown_jewel_protected"]),
                "cascade_averted": bool(r["cascade_averted"]),
                "availability_cost": r["availability_cost"],
                "has_pending": bool(r["has_pending"]),
            }
            for r in rows
        ]

    def get(self, row_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM incidents WHERE id = ?", (row_id,)
            ).fetchone()
        return json.loads(row["result_json"]) if row else None

    def update(self, row_id: int, result: dict[str, Any]) -> bool:
        """Overwrite a stored incident after approval/denial. Summary columns
        follow execution truth, not the original plan."""
        protected, cascade, cost, pending = self._summary(result)
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE incidents SET result_json = ?,
                   crown_jewel_protected = ?, cascade_averted = ?,
                   availability_cost = ?, has_pending = ?
                   WHERE id = ?""",
                (
                    json.dumps(result, default=str),
                    protected,
                    cascade,
                    cost,
                    pending,
                    row_id,
                ),
            )
            return cur.rowcount > 0
