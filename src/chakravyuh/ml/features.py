"""Canonical UEBA feature schema.

Every feature here is a continuous *behavioural* signal — none of them encode
"this matches technique X", which would make this a signature detector in
disguise. An unsupervised model finds the anomalies on its own.
"""
from __future__ import annotations

import numpy as np

FEATURE_NAMES = [
    "off_hours",              # 0/1 — access outside typical working hours
    "failed_logins_1h",       # count — recent failed logins
    "new_asset_pair",         # 0/1 — first-seen src->dst connection for this identity
    "bytes_out_zscore",       # outbound volume vs this asset's historical baseline
    "process_count_zscore",   # process-spawn rate vs baseline
    "privilege_level",        # ordinal: 0=user, 1=power-user, 2=admin, 3=system
    "session_duration_zscore",
]


def extract_features(raw: dict[str, float]) -> np.ndarray:
    """Map an arbitrary TelemetryEvent.features dict onto the fixed vector.

    Missing keys default to 0.0 (i.e. "nothing unusual observed").
    """
    return np.array(
        [float(raw.get(name, 0.0)) for name in FEATURE_NAMES], dtype=float
    )
