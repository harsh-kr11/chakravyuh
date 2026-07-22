"""Tests for audit integrity, response gating, cascade, and the full pipeline."""
from __future__ import annotations

from chakravyuh.agents import (
    AuditAgent,
    ResponseAgent,
    auto_approve,
    deny_all,
    pending_approval,
)
from chakravyuh.orchestrator import Orchestrator
from chakravyuh.scenarios import redecho
from chakravyuh.schemas import ActionType, ContainmentAction


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def test_audit_chain_verifies_clean():
    a = AuditAgent()
    for i in range(5):
        a.log("t", "e", {"i": i})
    assert a.verify() is True


def test_audit_tamper_is_detected():
    a = AuditAgent()
    a.log("t", "e", {"i": 0})
    a.log("t", "e", {"i": 1})
    a.records[0].payload["i"] = 999   # tamper with a past record
    assert a.verify() is False


def test_audit_hash_is_deterministic():
    a = AuditAgent()
    rec = a.log("t", "e", {"k": "v"})
    assert rec.hash == rec.compute_hash()


# --------------------------------------------------------------------------- #
# Response gating
# --------------------------------------------------------------------------- #
def _gated_action() -> ContainmentAction:
    return ContainmentAction(
        action_type=ActionType.ISOLATE_HOST, target="ot_x",
        requires_human_gate=True, est_disruption=1.0,
    )


def test_gated_action_not_executed_when_denied():
    r = ResponseAgent(gate=deny_all)
    results = r.process([_gated_action()])
    assert results[0].executed is False
    assert results[0].gated is True
    assert "ot_x" not in r.isolated


def test_gated_action_executed_when_approved():
    r = ResponseAgent(gate=auto_approve)
    results = r.process([_gated_action()])
    assert results[0].executed is True
    assert results[0].approved_by == "analyst:demo"


def test_ungated_action_runs_autonomously():
    r = ResponseAgent(gate=deny_all)  # gate should be irrelevant
    action = ContainmentAction(
        action_type=ActionType.REVOKE_CREDENTIAL, target="cred",
        requires_human_gate=False,
    )
    results = r.process([action])
    assert results[0].executed is True
    assert results[0].gated is False


# --------------------------------------------------------------------------- #
# End-to-end
# --------------------------------------------------------------------------- #
def test_end_to_end_contains_and_averts_cascade():
    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    result = Orchestrator().run(ag, events, crown_jewel=redecho.CROWN_JEWEL)

    assert result.plan.crown_jewel_protected is True
    assert result.plan.cascade_averted is True
    assert result.plan.availability_cost < result.plan.baseline_availability_cost
    assert result.audit_ok is True
    assert result.cascade.cross_sector is True
    assert result.mttr_steps >= 1


def test_benign_events_not_flagged():
    """False-positive control: benign noise below threshold is not detected."""
    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    result = Orchestrator().run(ag, events, crown_jewel=redecho.CROWN_JEWEL)
    flagged = {s.asset_id for s in result.context.anomalies}
    # domain_controller only appears as benign noise -> must not be flagged
    assert "domain_controller" not in flagged


def test_end_to_end_audit_records_every_execution():
    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    orch = Orchestrator()
    result = orch.run(ag, events, crown_jewel=redecho.CROWN_JEWEL)
    intents = [r for r in orch.audit.records if r.event_type == "action_intent"]
    results_ = [r for r in orch.audit.records if r.event_type == "action_result"]
    # every executed action has both an intent and a result record (fail-safe)
    assert len(intents) == len(result.plan.actions)
    assert len(results_) == len(result.plan.actions)


# --------------------------------------------------------------------------- #
# Observe-only mode and real (pending) human-in-the-loop
# --------------------------------------------------------------------------- #
def test_observe_only_mode_executes_nothing():
    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    orch = Orchestrator()  # default gate would auto-approve -- must not matter
    result = orch.run(
        ag, events, crown_jewel=redecho.CROWN_JEWEL, observe_only=True
    )
    assert result.plan.actions  # a plan is still computed and shown
    assert all(not e.executed for e in result.executions)
    assert all(not e.pending for e in result.executions)
    assert result.audit_ok is True
    observed = [r for r in orch.audit.records if r.event_type == "action_observed_only"]
    assert len(observed) == len(result.plan.actions)


def test_pending_gate_leaves_gated_actions_unresolved():
    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    orch = Orchestrator(gate=pending_approval)
    result = orch.run(ag, events, crown_jewel=redecho.CROWN_JEWEL)

    gated = [e for e in result.executions if e.gated]
    ungated = [e for e in result.executions if not e.gated]
    assert gated, "expected at least one human-gated action in the bundled scenario"
    assert all(e.pending and not e.executed for e in gated)
    # ungated (low-risk) actions still run immediately even under real HITL
    assert all(e.executed and not e.pending for e in ungated)
    pending_records = [
        r for r in orch.audit.records if r.event_type == "action_pending"
    ]
    assert len(pending_records) == len(gated)
