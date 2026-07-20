"""Audit / provenance agent.

Maintains an append-only, SHA-256 hash-chained log of every decision and
action, supporting a court-admissible chain of custody (ISO/IEC 27037 spirit).
Mutating any past record breaks the chain, which ``verify()`` detects.

Fail-safe invariant: if an action cannot be logged, it must not be executed.
The orchestrator enforces this by logging *before* execution and aborting on
audit failure.
"""
from __future__ import annotations

from typing import Any

from ..schemas import AuditRecord
from .base import Agent


class AuditAgent(Agent):
    name = "audit"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[AuditRecord] = []

    def log(self, actor: str, event_type: str, payload: dict[str, Any]) -> AuditRecord:
        prev_hash = self.records[-1].hash if self.records else ""
        rec = AuditRecord(
            seq=len(self.records),
            actor=actor,
            event_type=event_type,
            payload=payload,
            prev_hash=prev_hash,
        )
        rec.hash = rec.compute_hash()
        self.records.append(rec)
        return rec

    def verify(self) -> bool:
        """Return True iff the entire chain is intact (tamper-evident)."""
        prev_hash = ""
        for rec in self.records:
            if rec.prev_hash != prev_hash:
                return False
            if rec.hash != rec.compute_hash():
                return False
            prev_hash = rec.hash
        return True

    def export(self) -> list[dict[str, Any]]:
        return [r.model_dump(mode="json") for r in self.records]
