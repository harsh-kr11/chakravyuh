"""Response / SOAR agent.

Executes containment actions against a pluggable ``Connector`` (defaults to
an in-memory simulation if none is configured). High-impact or OT actions are
routed through a human-in-the-loop gate: the agent will NOT execute them
autonomously.

A gate function returns ``(approved, approver)``:
  - ``(True, "name")``  -> approved, execute now
  - ``(False, None)``   -> denied, do not execute
  - ``(None, None)``    -> *pending* — a real decision hasn't been made yet
    (used by the API's propose/approve flow; the action is executed later via
    a separate, explicit approval call, not by this agent auto-deciding)

The demo/CLI path uses ``auto_approve`` (unchanged, fully backward
compatible). The API's real human-in-the-loop path uses ``pending_approval``.
"""
from __future__ import annotations

from collections.abc import Callable

from ..connectors.base import Connector
from ..schemas import ContainmentAction, ExecutionResult
from .base import Agent

GateFn = Callable[[ContainmentAction], tuple[bool | None, str | None]]


def auto_approve(action: ContainmentAction) -> tuple[bool | None, str | None]:
    """Demo gate: approve immediately, attributing to a mock analyst."""
    return True, "analyst:demo"


def deny_all(action: ContainmentAction) -> tuple[bool | None, str | None]:
    """Safe default when no analyst responds: do not execute."""
    return False, None


def pending_approval(action: ContainmentAction) -> tuple[bool | None, str | None]:
    """Real human-in-the-loop gate: never auto-decide. A separate, later
    approval call (see ``chakravyuh.api.app.approve``) makes the real call."""
    return None, None


class ResponseAgent(Agent):
    name = "response"

    def __init__(
        self,
        *args,
        gate: GateFn = auto_approve,
        connector: Connector | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.gate = gate
        self.connector = connector
        self.isolated: set[str] = set()   # simulated infra state (fallback)

    def _execute(self, action: ContainmentAction, incident_id: str = "") -> str | None:
        """Carry out an approved action. Returns an error string, or None on
        success. Uses the configured connector if present; otherwise simulates.
        """
        self.isolated.add(str(action.target))
        if self.connector is None:
            return None
        result = self.connector.execute(action, incident_id=incident_id)
        return None if result.ok else result.detail

    def process(
        self, actions: list[ContainmentAction], incident_id: str = ""
    ) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        for action in actions:
            if action.requires_human_gate:
                approved, approver = self.gate(action)
                if approved is None:
                    results.append(ExecutionResult(
                        action=action, executed=False, gated=True, pending=True,
                    ))
                    continue
                if not approved:
                    results.append(ExecutionResult(
                        action=action, executed=False, gated=True,
                        approved_by=None,
                    ))
                    continue
                error = self._execute(action, incident_id=incident_id)
                results.append(ExecutionResult(
                    action=action, executed=error is None, gated=True,
                    approved_by=approver, error=error,
                ))
            else:
                error = self._execute(action, incident_id=incident_id)
                results.append(ExecutionResult(
                    action=action, executed=error is None, gated=False, error=error,
                ))
        return results
