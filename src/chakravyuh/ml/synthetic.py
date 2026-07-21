"""Synthetic-but-statistically-realistic UEBA training data.

DARPA OpTC / HAI (see docs/DATASETS.md) are the real benchmarks, but OpTC is
~1TB on Google Drive with no bulk-download API — not something to pull in an
automated environment. This generator produces unlabelled behavioural feature
vectors with realistic separation between normal and anomalous behaviour, so
the detector trains on *something real to fit* out of the box. Swap this
module for a real-dataset loader later; ``model.py`` does not change.
"""
from __future__ import annotations

import numpy as np

from .features import FEATURE_NAMES

assert len(FEATURE_NAMES) == 7  # keep generators below in sync with the schema


def generate_benign(n: int, rng: np.random.Generator) -> np.ndarray:
    return np.column_stack([
        rng.binomial(1, 0.05, n).astype(float),     # off_hours: rare
        rng.poisson(0.2, n).astype(float),          # failed_logins_1h: low
        rng.binomial(1, 0.03, n).astype(float),     # new_asset_pair: rare
        rng.normal(0.0, 1.0, n),                    # bytes_out_zscore: baseline
        rng.normal(0.0, 1.0, n),                    # process_count_zscore: baseline
        rng.choice([0.0, 0.0, 0.0, 1.0], size=n),   # privilege_level: mostly user
        rng.normal(0.0, 1.0, n),                    # session_duration_zscore
    ])


def generate_malicious(n: int, rng: np.random.Generator) -> np.ndarray:
    return np.column_stack([
        rng.binomial(1, 0.55, n).astype(float),     # off_hours: common
        rng.poisson(3.5, n).astype(float),          # failed_logins_1h: elevated
        rng.binomial(1, 0.70, n).astype(float),     # new_asset_pair: common (lateral)
        rng.normal(2.5, 1.2, n),                    # bytes_out_zscore: elevated
        rng.normal(2.0, 1.3, n),                    # process_count_zscore: elevated
        rng.choice([1.0, 2.0, 2.0, 3.0], size=n),   # privilege_level: escalated
        rng.normal(1.8, 1.0, n),                    # session_duration_zscore: elevated
    ])


def generate_training_set(
    n_benign: int = 4000, n_malicious: int = 200, seed: int = 13
) -> tuple[np.ndarray, np.ndarray]:
    """Return (X, y). ``y`` is ground truth for *evaluation only* — the model
    is fit on X alone, unlabelled, as a genuine unsupervised detector must be.
    """
    rng = np.random.default_rng(seed)
    x_benign = generate_benign(n_benign, rng)
    x_mal = generate_malicious(n_malicious, rng)
    x = np.vstack([x_benign, x_mal])
    y = np.concatenate([np.zeros(n_benign), np.ones(n_malicious)])
    idx = rng.permutation(len(x))
    return x[idx], y[idx]
