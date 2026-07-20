"""Compliance / reporting agent.

Auto-drafts a CERT-In incident report aligned with the 28 April 2022
Directions (six-hour reporting requirement). This is a *draft aid* for the
SOC, not a legal filing; a human reviews before submission.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..schemas import CascadeAssessment, IncidentContext, InterdictionPlan
from .base import Agent


class ComplianceAgent(Agent):
    name = "compliance"

    def draft_certin_report(
        self,
        ctx: IncidentContext,
        cascade: CascadeAssessment,
        plan: InterdictionPlan,
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        techniques = ", ".join(
            f"{t.technique_id} ({t.technique_name})" for t in ctx.techniques
        ) or "under analysis"
        actions = "\n".join(
            f"  - {a.action_type.value} -> {a.target} "
            f"(disruption={a.est_disruption}, gated={a.requires_human_gate})"
            for a in plan.actions
        ) or "  - none"

        return f"""\
CERT-In INCIDENT REPORT (DRAFT - auto-generated, pending analyst review)
=======================================================================
Generated (UTC): {now}
Incident ID: {ctx.incident_id}

1. Nature of incident: Unauthorised network intrusion / lateral movement
   toward a Protected System (Section 70A).
2. Affected sector(s): Power (Critical Information Infrastructure){
   ' + Health (cross-sector dependency)' if cascade.cross_sector else ''}.
3. Observed adversary techniques (MITRE ATT&CK): {techniques}
4. Attacker frontier at detection: {', '.join(ctx.attacker_frontier)}
5. Crown jewel(s) threatened: {', '.join(cascade.threatened_crown_jewels) or 'none'}
6. Cross-sector cascade risk: {'YES - ' + ', '.join(cascade.dependent_loads_at_risk)
   if cascade.dependent_loads_at_risk else 'none identified'}
7. Containment actions taken:
{actions}
8. Crown jewel protected after containment: {plan.crown_jewel_protected}
9. Cascade averted: {plan.cascade_averted}
10. Operational disruption (availability cost): {plan.availability_cost}
    (naive baseline would have cost {plan.baseline_availability_cost})

NOTE: Report timestamps must be NTP-synchronised (NIC/NPL) and logs retained
in India for 180 days per the CERT-In Directions, 2022.
"""
