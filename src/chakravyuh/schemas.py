"""Core domain schemas for CHAKRAVYUH.

Every inter-agent payload is a typed model defined here. This module is the
contract the whole system (and its test-suite) is written against. Keep it
dependency-light and stable.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Assets & topology
# --------------------------------------------------------------------------- #
class Sector(str, Enum):
    POWER = "power"
    HEALTH = "health"
    FINANCE = "finance"
    TELECOM = "telecom"
    TRANSPORT = "transport"
    GOVERNMENT = "government"
    INTERNET = "internet"  # external / attacker origin


class AssetType(str, Enum):
    INTERNET = "internet"
    IT_HOST = "it_host"
    IT_SERVER = "it_server"
    IDENTITY = "identity"          # credential / account
    OT_HISTORIAN = "ot_historian"
    OT_SCADA = "ot_scada"
    OT_ACTUATOR = "ot_actuator"
    SERVICE_LOAD = "service_load"  # e.g. hospital power draw (a dependent load)


class Asset(BaseModel):
    asset_id: str
    sector: Sector
    asset_type: AssetType
    criticality: int = Field(ge=1, le=5, description="1=trivial .. 5=safety-critical")
    is_crown_jewel: bool = False
    tags: list[str] = Field(default_factory=list)

    @property
    def is_ot(self) -> bool:
        return self.asset_type in {
            AssetType.OT_HISTORIAN,
            AssetType.OT_SCADA,
            AssetType.OT_ACTUATOR,
        }


# --------------------------------------------------------------------------- #
# Telemetry & detection
# --------------------------------------------------------------------------- #
class TelemetryEvent(BaseModel):
    """A single raw event from the (simulated) IT/OT environment."""

    ts: datetime = Field(default_factory=_utcnow)
    asset_id: str
    kind: str                      # e.g. "auth", "process", "netflow", "ot_reading"
    features: dict[str, float] = Field(default_factory=dict)
    # Ground-truth label used only for evaluation / scenario scripting.
    is_malicious: bool = False
    technique_hint: str | None = None  # ATT&CK id (scenario ground truth)


class AnomalySignal(BaseModel):
    ts: datetime = Field(default_factory=_utcnow)
    asset_id: str
    score: float = Field(ge=0.0, le=1.0, description="deviation from baseline")
    kind: str
    detail: str = ""


# --------------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------------- #
class TechniqueMatch(BaseModel):
    technique_id: str              # e.g. "T1078"
    technique_name: str = ""
    tactic: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    asset_id: str | None = None


class IncidentContext(BaseModel):
    incident_id: str
    anomalies: list[AnomalySignal] = Field(default_factory=list)
    techniques: list[TechniqueMatch] = Field(default_factory=list)
    # Attacker's currently-reached asset ids (the "frontier").
    attacker_frontier: list[str] = Field(default_factory=list)
    predicted_next: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Containment & interdiction
# --------------------------------------------------------------------------- #
class ActionType(str, Enum):
    ISOLATE_HOST = "isolate_host"
    BLOCK_LINK = "block_link"
    REVOKE_CREDENTIAL = "revoke_credential"
    NOOP = "noop"


class ContainmentAction(BaseModel):
    action_type: ActionType
    # For BLOCK_LINK the target is the edge (src, dst); else a single asset id.
    target: str | tuple[str, str]
    reversible: bool = True
    est_disruption: float = Field(
        ge=0.0, default=0.0, description="availability cost if executed"
    )
    requires_human_gate: bool = False
    rationale: str = ""

    model_config = {"frozen": False}


class InterdictionPlan(BaseModel):
    incident_id: str
    actions: list[ContainmentAction] = Field(default_factory=list)
    attacker_cost_before: float = 0.0    # min path-cost to crown jewel pre-cut
    attacker_cost_after: float = 0.0     # inf => disconnected
    availability_cost: float = 0.0       # sum of est_disruption
    crown_jewel_protected: bool = False
    cascade_averted: bool = False
    baseline_availability_cost: float = 0.0  # naive containment cost, for contrast
    notes: str = ""


class CascadeAssessment(BaseModel):
    incident_id: str
    threatened_crown_jewels: list[str] = Field(default_factory=list)
    dependent_loads_at_risk: list[str] = Field(default_factory=list)
    cross_sector: bool = False
    narrative: str = ""


# --------------------------------------------------------------------------- #
# Execution & audit
# --------------------------------------------------------------------------- #
class ExecutionResult(BaseModel):
    action: ContainmentAction
    executed: bool
    gated: bool = False            # True if it was routed to a human gate
    pending: bool = False          # True if awaiting a real human decision
    approved_by: str | None = None
    error: str | None = None
    ts: datetime = Field(default_factory=_utcnow)


class AuditRecord(BaseModel):
    seq: int
    ts: datetime = Field(default_factory=_utcnow)
    actor: str                     # agent name or analyst id
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""

    def compute_hash(self) -> str:
        body = {
            "seq": self.seq,
            "ts": self.ts.isoformat(),
            "actor": self.actor,
            "event_type": self.event_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }
        blob = json.dumps(body, sort_keys=True, default=str).encode()
        return hashlib.sha256(blob).hexdigest()
