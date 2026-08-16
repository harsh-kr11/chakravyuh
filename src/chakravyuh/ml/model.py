"""Unsupervised UEBA model: an IsolationForest over behavioural features.

Fit on unlabelled data only — no attack signatures, no labels used at fit
time. This is the reference detector; swap ``synthetic.generate_training_set``
for a real-dataset loader (OpTC/HAI — see docs/DATASETS.md) without touching
anything downstream (``DetectionAgent`` only ever calls ``get_model().score``).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

DEFAULT_MODEL_PATH = "data/models/ueba_isolation_forest.joblib"


@dataclass
class UEBAModel:
    estimator: object
    raw_threshold: float   # raw anomaly score at the fitted inlier/outlier boundary
    raw_scale: float       # spread used to map that boundary onto 0.5

    def score(self, x: np.ndarray) -> float:
        """Return a normalised 0..1 anomaly score (higher = more anomalous).

        Centred via a logistic transform on the estimator's own
        contamination-derived decision boundary, so a downstream
        ``anomaly_threshold=0.5`` roughly matches the model's fitted notion
        of "outlier" rather than an arbitrary min-max stretch.
        """
        raw = float(-self.estimator.score_samples(x.reshape(1, -1))[0])
        if self.raw_scale <= 0:
            return 0.0
        z = (raw - self.raw_threshold) / self.raw_scale
        return float(1.0 / (1.0 + np.exp(-z)))

    def save(self, path: str) -> None:
        import joblib

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> UEBAModel:
        import joblib

        return joblib.load(path)


def train(contamination: float = 0.05, seed: int = 13) -> UEBAModel:
    from sklearn.ensemble import IsolationForest

    from .synthetic import generate_training_set

    x, _y = generate_training_set(seed=seed)
    estimator = IsolationForest(
        n_estimators=200, contamination=contamination, random_state=seed
    )
    estimator.fit(x)
    raw = -estimator.score_samples(x)
    raw_threshold = float(-estimator.offset_)   # contamination-derived boundary
    raw_scale = float((np.percentile(raw, 90) - np.percentile(raw, 10)) / 4) or 1.0
    return UEBAModel(
        estimator=estimator, raw_threshold=raw_threshold, raw_scale=raw_scale
    )


_cached: UEBAModel | None = None


def get_model(model_path: str = DEFAULT_MODEL_PATH) -> UEBAModel | None:
    """Return a trained model, training + persisting one on first use.

    Returns None if scikit-learn (the ``[detect]`` extra) is not installed,
    so ``DetectionAgent`` can fall back to its deterministic heuristic — the
    core pipeline stays zero-dependency by default.
    """
    global _cached
    if _cached is not None:
        return _cached
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return None

    if Path(model_path).exists():
        try:
            _cached = UEBAModel.load(model_path)
            return _cached
        except Exception:
            pass  # corrupt/incompatible cache — retrain below

    model = train()
    try:
        model.save(model_path)
    except Exception:
        pass  # in-memory model is enough; disk is optional
    _cached = model
    return model


def reset_cache() -> None:
    """Testing hook: forget the in-process cached model."""
    global _cached
    _cached = None
