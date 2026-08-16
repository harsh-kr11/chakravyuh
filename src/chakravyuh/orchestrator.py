"""Orchestrator — the CHAKRAVYUH pipeline.

Deterministic control flow over the agents:

    detection -> attribution -> cascade -> interdiction -> (audit) -> response

The audit fail-safe is enforced here: every action is logged *before* it is
executed, and execution is aborted if the audit write fails. In production
this state machine is a LangGraph graph; here it is a small explicit pipeline
so the reference implementation has zero heavy dependencies.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .agents import (
    AgentConfig,
    AttributionAgent,
    AuditAgent,
    CascadeAgent,
    ComplianceAgent,
    DetectionAgent,
    InterdictionAgent,
    ResponseAgent,
    auto_approve,
)
from .agents.response import GateFn
from .connectors.base import Connector
from .graph import AttackGraph
from .schemas import (
    CascadeAssessment,
    ExecutionResult,
    IncidentContext,
    InterdictionPlan,
    TelemetryEvent,
)

_LOG = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    context: IncidentContext
    cascade: CascadeAssessment
    plan: InterdictionPlan
    executions: list[ExecutionResult] = field(default_factory=list)
    certin_report: str = ""
    audit_ok: bool = False
    mttd_steps: int | None = None  # events before first detection; None = none
    mttr_steps: int = 0   # actions taken to contain


class Orchestrator:
    def __init__(
        self,
        config: AgentConfig | None = None,
        gate: GateFn = auto_approve,
        connector: Connector | None = None,
    ) -> None:
        self.config = config or AgentConfig()
        self.detection = DetectionAgent(self.config)
        self.attribution = AttributionAgent(self.config)
        self.cascade = CascadeAgent(self.config)
        self.interdiction = InterdictionAgent(self.config)
        self.response = ResponseAgent(self.config, gate=gate, connector=connector)
        self.compliance = ComplianceAgent(self.config)
        self.audit = AuditAgent(self.config)

    def run(
        self,
        ag: AttackGraph,
        events: list[TelemetryEvent],
        crown_jewel: str,
        incident_id: str = "INC-0001",
        observe_only: bool = False,
    ) -> PipelineResult:
        # 1. detection
        signals = self.detection.process(events)
        self.audit.log("detection", "anomalies_detected",
                       {"count": len(signals),
                        "assets": [s.asset_id for s in signals]})

        # 2. attribution
        ctx = self.attribution.process(incident_id, signals, events)
        self.audit.log("attribution", "attack_attributed",
                       {"techniques": [t.technique_id for t in ctx.techniques],
                        "frontier": ctx.attacker_frontier})

        # 3. cascade
        cascade = self.cascade.process(ag, incident_id, ctx.attacker_frontier)
        self.audit.log("cascade", "cascade_assessed",
                       {"threatened": cascade.threatened_crown_jewels,
                        "loads_at_risk": cascade.dependent_loads_at_risk,
                        "cross_sector": cascade.cross_sector})

        # 4. interdiction planning (never raises — failed plans are structured)
        plan = self.interdiction.process(
            ag, incident_id, ctx.attacker_frontier, crown_jewel
        )
        self.audit.log("interdiction", "plan_computed", {
            "actions": [a.action_type.value for a in plan.actions],
            "availability_cost": plan.availability_cost,
            "baseline_cost": plan.baseline_availability_cost,
            "greedy_cost": plan.greedy_availability_cost,
            "crown_jewel_protected": plan.crown_jewel_protected,
            "cascade_averted": plan.cascade_averted,
        })

        # 5. response with audit-before-execute fail-safe
        executions: list[ExecutionResult] = []
        for action in plan.actions:
            try:
                self.audit.log("response", "action_intent",
                               {"action": action.action_type.value,
                                "target": str(action.target),
                                "gated": action.requires_human_gate,
                                "observe_only": observe_only})
            except Exception as exc:
                _LOG.warning("audit write failed, aborting action: %s", exc)
                continue

            if observe_only:
                result = ExecutionResult(
                    action=action, executed=False,
                    gated=action.requires_human_gate,
                )
                self.audit.log("response", "action_observed_only",
                               {"action": action.action_type.value})
            else:
                result = self.response.process([action], incident_id=incident_id)[0]
                self.audit.log(
                    "response",
                    "action_pending" if result.pending else "action_result",
                    {"action": action.action_type.value,
                     "executed": result.executed,
                     "gated": result.gated,
                     "approved_by": result.approved_by},
                )
            executions.append(result)

        # 6. compliance report
        report = self.compliance.draft_certin_report(
            ctx, cascade, plan, executions=executions,
            observe_only=observe_only,
        )
        self.audit.log("compliance", "certin_report_drafted",
                       {"incident_id": incident_id})

        mttd: int | None = None
        for i, e in enumerate(events, start=1):
            if self.detection.score_event(e) >= self.config.anomaly_threshold:
                mttd = i
                break

        return PipelineResult(
            context=ctx,
            cascade=cascade,
            plan=plan,
            executions=executions,
            certin_report=report,
            audit_ok=self.audit.verify(),
            mttd_steps=mttd,
            mttr_steps=len([e for e in executions if e.executed]),
        )

    def run_adapter(
        self, adapter, incident_id: str = "INC-0001", observe_only: bool = False
    ) -> PipelineResult:
        """Run the pipeline from any InfrastructureAdapter."""
        return self.run(
            adapter.build_graph(),
            adapter.stream_events(),
            adapter.crown_jewel(),
            incident_id=incident_id,
            observe_only=observe_only,
        )
