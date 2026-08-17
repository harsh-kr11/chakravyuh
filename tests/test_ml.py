"""Tests for the unsupervised UEBA detector (chakravyuh.ml)."""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("sklearn")

from chakravyuh.ml.model import reset_cache, train  # noqa: E402
from chakravyuh.ml.synthetic import generate_training_set  # noqa: E402


def test_model_separates_benign_from_malicious_on_held_out_data():
    model = train()
    x, y = generate_training_set(seed=99)  # different seed: held-out set
    scores = np.array([model.score(row) for row in x])
    predicted = scores >= 0.5

    tp = int(((predicted == 1) & (y == 1)).sum())
    fp = int(((predicted == 1) & (y == 0)).sum())
    fn = int(((predicted == 0) & (y == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    # Genuinely unsupervised (fit without labels) but should still separate
    # the synthetic malicious cluster well on held-out data.
    assert precision > 0.7
    assert recall > 0.9


def test_score_is_bounded_and_fitting_is_unlabelled():
    model = train()
    x, _y = generate_training_set(seed=1)
    for row in x[:20]:
        s = model.score(row)
        assert 0.0 <= s <= 1.0


def test_get_model_persists_and_reloads(tmp_path, monkeypatch):
    from chakravyuh.ml import model as model_mod

    reset_cache()
    path = str(tmp_path / "ueba.joblib")
    m1 = model_mod.get_model(path)
    assert m1 is not None
    assert (tmp_path / "ueba.joblib").exists()

    reset_cache()
    m2 = model_mod.get_model(path)
    x = np.array([1, 4, 1, 1.2, 2.5, 2, 1.5], dtype=float)
    assert m1.score(x) == pytest.approx(m2.score(x))
    reset_cache()


def test_get_model_save_failure_keeps_in_memory(tmp_path, monkeypatch):
    from chakravyuh.ml import model as model_mod

    reset_cache()

    def boom(self, path):
        raise OSError("disk full")

    monkeypatch.setattr(model_mod.UEBAModel, "save", boom)
    path = str(tmp_path / "ueba.joblib")
    m = model_mod.get_model(path)
    assert m is not None
    x = np.array([1, 4, 1, 1.2, 2.5, 2, 1.5], dtype=float)
    assert 0.0 <= m.score(x) <= 1.0
    reset_cache()
