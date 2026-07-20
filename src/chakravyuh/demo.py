"""Narrated command-line demo of CHAKRAVYUH.

Runs the RedEcho-style cross-sector scenario end to end and prints the same
beats the on-stage dashboard would show. Deterministic and dependency-light.

    python -m chakravyuh.demo
"""
from __future__ import annotations

from .orchestrator import Orchestrator
from .scenarios import redecho


def _rule(char: str = "-") -> str:
    return char * 68


def main() -> int:
    print(_rule("="))
    print(" CHAKRAVYUH  |  National Cyber-Interdiction Grid  (demo)")
    print(_rule("="))

    ag = redecho.build_graph()
    events = redecho.telemetry_stream()
    orch = Orchestrator()
    result = orch.run(ag, events, crown_jewel=redecho.CROWN_JEWEL)

    print("\n[BEAT 1] Detection (behavioural, no signatures)")
    for s in result.context.anomalies:
        print(f"   ! anomaly on {s.asset_id:<20} score={s.score:.2f}")

    print("\n[BEAT 2] Attribution (MITRE ATT&CK)")
    for t in result.context.techniques:
        print(f"   -> {t.technique_id} {t.technique_name:<28} "
              f"[{t.tactic}] @ {t.asset_id}")
    print(f"   attacker frontier: {result.context.attacker_frontier}")

    print("\n[BEAT 3] Cross-sector cascade")
    print(f"   {result.cascade.narrative or 'no cascade risk'}")

    print("\n[BEAT 4] Interdiction (the minimal-disruption cut)")
    p = result.plan
    for a in p.actions:
        gate = "  (HUMAN-GATED)" if a.requires_human_gate else ""
        print(f"   * {a.action_type.value:<18} {str(a.target):<32}"
              f" disruption={a.est_disruption}{gate}")
    after = "BLOCKED" if p.crown_jewel_protected else f"{p.attacker_cost_after:.1f}"
    print(f"   attacker path-cost to crown jewel: "
          f"{p.attacker_cost_before:.1f} -> {after}")
    print(f"   availability cost: {p.availability_cost:.1f}   "
          f"(naive baseline: {p.baseline_availability_cost:.1f})")
    print(f"   crown jewel protected: {p.crown_jewel_protected}   "
          f"cascade averted: {p.cascade_averted}")

    print("\n[BEAT 5] Response (SOAR, human-gated for OT)")
    for e in result.executions:
        status = "EXECUTED" if e.executed else "GATED/held"
        who = f" by {e.approved_by}" if e.approved_by else ""
        print(f"   {status:<11} {e.action.action_type.value} "
              f"-> {e.action.target}{who}")
    print(f"   MTTD (events to first detect): {result.mttd_steps}   "
          f"MTTR (actions to contain): {result.mttr_steps}")

    print("\n[BEAT 6a] CERT-In 6-hour report (auto-draft)")
    for line in result.certin_report.splitlines()[:8]:
        print("   " + line)
    print("   ... (full report available via API)")

    print("\n[BEAT 6b] Audit trail")
    print(f"   {len(orch.audit.records)} records, chain verified: "
          f"{result.audit_ok}")

    print("\n" + _rule("="))
    verdict = (p.crown_jewel_protected and p.cascade_averted and result.audit_ok)
    msg = "CONTAINED, cascade averted, fully audited" if verdict else "see logs"
    print(f" RESULT: {msg}")
    print(_rule("="))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
