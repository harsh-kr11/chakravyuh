"""Infrastructure adapter interface.

Everything that touches the (simulated or real) environment goes through an
adapter: telemetry comes IN as TelemetryEvents, containment goes OUT as
ContainmentActions. This is the single seam between CHAKRAVYUH and the world,
which is what makes the system portable across a demo scenario, a benchmark
replay (OpTC/HAI), a closed-loop simulator (CybORG), or (with great care) real
infrastructure.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..graph import AttackGraph
from ..schemas import ContainmentAction, TelemetryEvent


class InfrastructureAdapter(ABC):
    """Base class for all environment adapters."""

    @abstractmethod
    def build_graph(self) -> AttackGraph:
        """Return the (initial) attack graph / asset topology."""

    @abstractmethod
    def stream_events(self) -> list[TelemetryEvent]:
        """Return the telemetry events to analyse."""

    @abstractmethod
    def crown_jewel(self) -> str:
        """Return the crown-jewel asset id to protect."""

    def apply_action(self, action: ContainmentAction) -> bool:
        """Apply a containment action to the environment. Returns success.

        Default is a no-op (safe). Real adapters override this.
        """
        return True
