"""Compliance / reporting agent.

Auto-drafts a CERT-In incident report aligned with the 28 April 2022
Directions (six-hour reporting requirement). This is a *draft aid* for the
SOC, not a legal filing; a human reviews before submission.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..schemas import (
    CascadeAssessment,
    ExecutionResult,
    IncidentContext,
    InterdictionPlan,
    format_target,
)
from .base import Agent


class ComplianceAgent(Agent):
    name = "compliance"

    def draft_certin_report(
        self,
        ctx: IncidentContext,
        cascade: CascadeAssessment,
        plan: InterdictionPlan,
        executions: list[ExecutionResult] | None = None,
        observe_only: bool = False,
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        techniques = ", ".join(
            f"{t.technique_id} ({t.technique_name})" for t in ctx.techniques
        ) or "under analysis"

        execs = executions or []
        by_key = {
            (e.action.action_type.value, str(e.action.target)): e for e in execs
        }
        action_lines: list[str] = []
        for a in plan.actions:
            key = (a.action_type.value, str(a.target))
            ex = by_key.get(key)
            if observe_only or ex is None:
                status = "PROPOSED"
            elif ex.pending:
                status = "PENDING human approval"
            elif ex.executed:
                status = "EXECUTED"
            else:
                status = "HELD / DENIED"
            action_lines.append(
                f"  - [{status}] {a.action_type.value} -> {format_target(a.target)} "
                f"(disruption={a.est_disruption}, gated={a.requires_human_gate})"
            )
        actions = "\n".join(action_lines) or "  - none"

        pending = any(e.pending for e in execs)
        all_done = bool(execs) and all(e.executed for e in execs)
        protected_now = bool(plan.crown_jewel_protected) and all_done
        cascade_now = bool(plan.cascade_averted) and all_done

        if observe_only:
            containment_line = (
                "PROPOSED (observe mode — nothing executed in this run)"
            )
        elif pending:
            containment_line = (
                "PROPOSED — OT / high-blast actions still awaiting human approval. "
                "Do not treat the crown jewel as contained until those complete."
            )
        elif not execs:
            containment_line = "PROPOSED (nothing executed in this run)"
        else:
            containment_line = "see status tags on each action below"

        loads = cascade.dependent_loads_at_risk
        if cascade.cross_sector and loads:
            sectors = (
                f"cross-sector; dependent load(s) at risk: {', '.join(loads)}"
            )
        elif loads:
            sectors = f"dependent load(s) at risk: {', '.join(loads)}"
        elif cascade.threatened_crown_jewels:
            sectors = (
                "crown jewel(s) "
                + ", ".join(cascade.threatened_crown_jewels)
            )
        else:
            sectors = "under analysis"

        return f"""\
CERT-In INCIDENT REPORT (DRAFT - auto-generated, pending analyst review)
=======================================================================
Generated (UTC): {now}
Incident ID: {ctx.incident_id}

1. Nature of incident: Unauthorised network intrusion / lateral movement
   toward a Protected System (Section 70A).
2. Affected sector(s): {sectors}.
3. Observed adversary techniques (MITRE ATT&CK): {techniques}
4. Attacker frontier at detection: {', '.join(ctx.attacker_frontier) or 'none detected'}
5. Crown jewel(s) threatened: {', '.join(cascade.threatened_crown_jewels) or 'none'}
6. Cross-sector cascade risk: {'YES - ' + ', '.join(loads)
   if loads else 'none identified'}
7. Containment actions: {containment_line}
{actions}
8. Crown jewel protected (plan): {plan.crown_jewel_protected}
   Crown jewel protected now (after execution): {protected_now}
9. Cascade averted (plan): {plan.cascade_averted}
   Cascade averted now: {cascade_now}
10. Operational disruption (availability cost): {plan.availability_cost}
    (naive isolate-jewel baseline: {plan.baseline_availability_cost};
     greedy isolate-frontier: {plan.greedy_availability_cost})

NOTE: Report timestamps must be NTP-synchronised (NIC/NPL) and logs retained
in India for 180 days per the CERT-In Directions, 2022.
"""
