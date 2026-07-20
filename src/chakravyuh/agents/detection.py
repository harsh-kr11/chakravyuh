"""Detection agent (UEBA / behavioural anomaly).

Reference implementation scores each telemetry event and raises an
``AnomalySignal`` when the deviation exceeds a threshold. The scoring function
here reads a precomputed ``anomaly_score`` (from the scenario) so the demo is
deterministic; the production detector plugs a real unsupervised model in via
``score_event`` (e.g. Isolation Forest on IT netflow/auth features, or a
reconstruction-based detector on ICS telemetry — see docs/DATASETS.md).

No malware signatures are used — detection is purely behavioural, satisfying
the challenge's "no known malware signature" requirement.
"""
from __future__ import annotations

from ..schemas import AnomalySignal, TelemetryEvent
from .base import Agent


class DetectionAgent(Agent):
    name = "detection"

    def score_event(self, event: TelemetryEvent) -> float:
        """Return a 0..1 anomaly score. Override with a real model."""
        return float(event.features.get("anomaly_score", 0.0))

    def process(self, events: list[TelemetryEvent]) -> list[AnomalySignal]:
        signals: list[AnomalySignal] = []
        for event in events:
            score = self.score_event(event)
            if score >= self.config.anomaly_threshold:
                signals.append(AnomalySignal(
                    ts=event.ts,
                    asset_id=event.asset_id,
                    score=score,
                    kind=event.kind,
                    detail=f"behavioural deviation on {event.asset_id}",
                ))
        return signals
