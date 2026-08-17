"""Shared behavioural event helper for bundled scenarios."""
from __future__ import annotations

from ..schemas import TelemetryEvent


def anomalous_event(
    asset_id: str,
    technique: str,
    *,
    score: float = 0.84,
    **features: float,
) -> TelemetryEvent:
    feat: dict[str, float] = {
        "off_hours": 1,
        "failed_logins_1h": 2,
        "new_asset_pair": 1,
        "bytes_out_zscore": 1.6,
        "process_count_zscore": 1.5,
        "privilege_level": 1,
        "session_duration_zscore": 1.0,
        "anomaly_score": score,
    }
    feat.update(features)
    return TelemetryEvent(
        asset_id=asset_id,
        kind="auth",
        features=feat,
        is_malicious=True,
        technique_hint=technique,
    )
