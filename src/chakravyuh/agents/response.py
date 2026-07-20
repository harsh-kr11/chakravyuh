"""Response / SOAR agent.

Executes containment actions against the (simulated) infrastructure adapter.
High-impact or OT actions are routed through a human-in-the-loop gate: the
agent will NOT execute them autonomously. A gate callback decides approval;
in the demo this auto-approves with an analyst id, in production it surfaces
on the command-console for a real analyst.
"""
from __future__ import annotations

from collections.abc import Callable

from ..schemas import ContainmentAction, ExecutionResult
from .base import Agent

GateFn = Callable[[ContainmentAction], tuple[bool, str | None]]


def auto_approve(action: ContainmentAction) -> tuple[bool, str | None]:
    """Demo gate: approve, attributing to a mock analyst."""
    return True, "analyst:demo"


def deny_all(action: ContainmentAction) -> tuple[bool, str | None]:
    """Safe default when no analyst responds: do not execute."""
    return False, None


class ResponseAgent(Agent):
    name = "response"

    def __init__(self, *args, gate: GateFn = auto_approve, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.gate = gate
        self.isolated: set[str] = set()   # simulated infra state

    def _execute(self, action: ContainmentAction) -> None:
        # Simulated infrastructure mutation.
        self.isolated.add(str(action.target))

    def process(self, actions: list[ContainmentAction]) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        for action in actions:
            if action.requires_human_gate:
                approved, approver = self.gate(action)
                if not approved:
                    results.append(ExecutionResult(
                        action=action, executed=False, gated=True,
                        approved_by=None,
                    ))
                    continue
                self._execute(action)
                results.append(ExecutionResult(
                    action=action, executed=True, gated=True,
                    approved_by=approver,
                ))
            else:
                self._execute(action)
                results.append(ExecutionResult(
                    action=action, executed=True, gated=False,
                ))
        return results
