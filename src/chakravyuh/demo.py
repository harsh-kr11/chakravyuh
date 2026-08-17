"""Narrated command-line demo of CHAKRAVYUH.

    python -m chakravyuh.demo
    python -m chakravyuh.demo --scenario colonial
    python -m chakravyuh.demo --hitl
"""
from __future__ import annotations

import argparse

from .agents import pending_approval
from .orchestrator import Orchestrator
from .scenarios.catalog import DEFAULT_ID
from .scenarios.catalog import get as get_scenario
from .schemas import format_target


def _rule(char: str = "-") -> str:
    return char * 68


def _cost(value: float) -> str:
    if value == float("inf"):
        return "UNREACHABLE"
    return f"{value:.1f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chakravyuh-demo")
    parser.add_argument("--scenario", default=DEFAULT_ID,
                        help="catalog id (default: redecho)")
    parser.add_argument(
        "--hitl", action="store_true",
        help="real pending approval for OT (does not execute gated actions). "
             "Not observe-only: ungated actions still run.",
    )
    args = parser.parse_args(argv)

    try:
        mod = get_scenario(args.scenario)
    except KeyError:
        print(f"unknown scenario {args.scenario!r}")
        return 2

    meta = mod.META
    print(_rule("="))
    print(" CHAKRAVYUH  |  incident-time interdiction")
    print(_rule("="))
    print(f" Case: {meta['title']}  [{meta['kind']}]")
    print(f" {meta['one_liner']}")
    print(f" {meta['disclaimer']}")

    ag = mod.build_graph()
    events = mod.telemetry_stream()
    orch = Orchestrator(gate=pending_approval) if args.hitl else Orchestrator()
    result = orch.run(ag, events, crown_jewel=mod.CROWN_JEWEL)

    print("\n[BEAT 1] Detection (behavioural, no signatures)")
    if not result.context.anomalies:
        print("   (no anomalies above threshold)")
    for s in result.context.anomalies:
        print(f"   ! anomaly on {s.asset_id:<22} score={s.score:.2f}")

    print("\n[BEAT 2] Attribution (MITRE ATT&CK)")
    for t in result.context.techniques:
        print(f"   -> {t.technique_id} {t.technique_name:<28} "
              f"[{t.tactic}] @ {t.asset_id}")
    print(f"   attacker frontier: {result.context.attacker_frontier}")

    print("\n[BEAT 3] Cross-sector cascade")
    print(f"   {result.cascade.narrative or 'no cascade risk flagged'}")

    print("\n[BEAT 4] Interdiction (the minimal-disruption cut)")
    p = result.plan
    for a in p.actions:
        gate = "  (HUMAN-GATED)" if a.requires_human_gate else ""
        print(f"   * {a.action_type.value:<18} {format_target(a.target):<36}"
              f" disruption={a.est_disruption}{gate}")
    after = "BLOCKED" if p.crown_jewel_protected else _cost(p.attacker_cost_after)
    print(f"   attacker path-cost to crown jewel: "
          f"{_cost(p.attacker_cost_before)} -> {after}")

    hist = mod.historical()
    print()
    print(f"   {'':22} {'Min-cut':<16} {'Historical / naive'}")
    print(f"   {'Actions':22} {len(p.actions):<16} {hist['decision'][:40]}")
    print(f"   {'Disruption':22} {p.availability_cost:<16.1f} "
          f"{p.baseline_availability_cost:.1f}")
    kept = "YES" if p.cascade_averted or not hist["severs_protected"] else "see plan"
    print(f"   {'Protected load kept':22} {kept:<16} "
          f"{'NO' if hist['severs_protected'] else 'n/a'}")
    if p.greedy_availability_cost > p.availability_cost:
        print(f"   greedy isolate-frontier would cost {p.greedy_availability_cost:.1f}")

    print("\n[BEAT 5] Response")
    for e in result.executions:
        if e.pending:
            status = "PENDING"
        elif e.executed:
            status = "EXECUTED"
        else:
            status = "HELD"
        who = f" by {e.approved_by}" if e.approved_by else ""
        print(f"   {status:<11} {e.action.action_type.value} "
              f"-> {format_target(e.action.target)}{who}")
    mttd = result.mttd_steps if result.mttd_steps is not None else "none"
    print(f"   MTTD (events to first detect): {mttd}   "
          f"MTTR (actions executed): {result.mttr_steps}")

    print("\n[BEAT 6a] CERT-In 6-hour report (auto-draft)")
    for line in result.certin_report.splitlines()[:10]:
        print("   " + line)
    print("   ...")

    print("\n[BEAT 6b] Audit trail")
    print(f"   {len(orch.audit.records)} records, chain verified: "
          f"{result.audit_ok}")

    print("\n" + _rule("="))
    pending = any(e.pending for e in result.executions)
    if pending:
        msg = "PLAN READY, OT actions pending human approval (--hitl)"
        ok = result.audit_ok and bool(p.actions)
    else:
        ok = bool(p.crown_jewel_protected and result.audit_ok)
        msg = "CONTAINED, cascade considered, audited" if ok else "see logs"
    print(f" RESULT: {msg}")
    print(_rule("="))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
