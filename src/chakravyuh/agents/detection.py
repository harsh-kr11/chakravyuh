"""Detection agent (UEBA / behavioural anomaly).

Scores each telemetry event with an unsupervised IsolationForest
(``chakravyuh.ml``) fit over continuous behavioural features — no malware
signatures anywhere. If the ``[detect]`` extra (scikit-learn) is not
installed, falls back to reading a precomputed ``anomaly_score`` feature so
the zero-dependency core demo still runs deterministically.
"""
from __future__ import annotations

from ..ml.features import extract_features
from ..ml.model import get_model
from ..schemas import AnomalySignal, TelemetryEvent
from .base import Agent


class DetectionAgent(Agent):
    name = "detection"

    def score_event(self, event: TelemetryEvent) -> float:
        """Return a 0..1 anomaly score from the trained UEBA model.

        Falls back to a precomputed ``anomaly_score`` feature when
        scikit-learn is not installed.
        """
        model = get_model()
        if model is None:
            return float(event.features.get("anomaly_score", 0.0))
        try:
            return model.score(extract_features(event.features))
        except Exception:
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
