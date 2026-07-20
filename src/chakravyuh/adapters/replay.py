"""Replay adapter: drive the pipeline from a fixed graph + event list.

This is how benchmark datasets (DARPA OpTC for IT, HAI/SWaT for OT) are wired
in — parse the dataset once into an AttackGraph + a list of TelemetryEvents and
replay them deterministically. The bundled scenario adapter is a special case.
"""
from __future__ import annotations

from ..graph import AttackGraph
from ..schemas import TelemetryEvent
from .base import InfrastructureAdapter


class ReplayAdapter(InfrastructureAdapter):
    def __init__(
        self,
        graph: AttackGraph,
        events: list[TelemetryEvent],
        crown_jewel: str,
    ) -> None:
        self._graph = graph
        self._events = events
        self._crown_jewel = crown_jewel

    def build_graph(self) -> AttackGraph:
        return self._graph

    def stream_events(self) -> list[TelemetryEvent]:
        return self._events

    def crown_jewel(self) -> str:
        return self._crown_jewel


class ScenarioAdapter(ReplayAdapter):
    """Convenience adapter built from a scenario module exposing
    build_graph(), telemetry_stream(), and CROWN_JEWEL."""

    def __init__(self, scenario) -> None:
        super().__init__(
            graph=scenario.build_graph(),
            events=scenario.telemetry_stream(),
            crown_jewel=scenario.CROWN_JEWEL,
        )
