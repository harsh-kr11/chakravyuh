"""Real-infrastructure adapter — intentionally a guarded stub.

Connecting an autonomous cyber-response system to production OT/ICS is
dangerous. This stub exists to document the interface, NOT to be run live. It
raises unless explicitly force-enabled, and even then performs no actions.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..schemas import ContainmentAction, TelemetryEvent
from .base import InfrastructureAdapter


class RealAdapter(InfrastructureAdapter):
    def __init__(self, *, i_understand_the_risks: bool = False) -> None:
        if not i_understand_the_risks:
            raise RuntimeError(
                "RealAdapter must not be used without a qualified OT-safety "
                "review. See SECURITY.md. Pass i_understand_the_risks=True only "
                "in a controlled, non-production environment."
            )

    def build_graph(self) -> AttackGraph:  # pragma: no cover - stub
        raise NotImplementedError("wire to your CMDB / asset inventory")

    def stream_events(self) -> list[TelemetryEvent]:  # pragma: no cover - stub
        raise NotImplementedError("wire to your SIEM / EDR / OT historian")

    def crown_jewel(self) -> str:  # pragma: no cover - stub
        raise NotImplementedError("configure your Protected System asset id")

    def apply_action(self, action: ContainmentAction) -> bool:  # pragma: no cover
        raise NotImplementedError(
            "wire to your SOAR / firewall / IAM — with human gates intact"
        )
