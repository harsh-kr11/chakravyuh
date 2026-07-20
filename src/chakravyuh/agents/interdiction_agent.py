"""Interdiction agent — thin agent wrapper around the interdiction planner."""
from __future__ import annotations

from ..graph import AttackGraph
from ..graph.interdiction import plan_interdiction
from ..schemas import InterdictionPlan
from .base import Agent


class InterdictionAgent(Agent):
    name = "interdiction"

    def process(
        self,
        ag: AttackGraph,
        incident_id: str,
        attacker_frontier: list[str],
        crown_jewel: str,
    ) -> InterdictionPlan:
        plan = plan_interdiction(ag, incident_id, attacker_frontier, crown_jewel)
        # Apply blast-radius / OT gating policy to each action.
        for action in plan.actions:
            if action.est_disruption > self.config.blast_radius_threshold:
                action.requires_human_gate = True
        return plan
