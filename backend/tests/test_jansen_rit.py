"""Tests for the Jansen-Rit simulator."""
import numpy as np
import pytest

from app.core.jansen_rit import (
    JansenRitParams, REGIMES, sigmoid, rhs, simulate, simulate_recording,
)


def test_sigmoid_monotone_and_bounded():
    v = np.linspace(-20, 40, 200)
    s = sigmoid(v)
    assert s.shape == v.shape
    assert np.all(s >= 0) and np.all(s <= 5.001)
    assert np.all(np.diff(s) >= 0)


def test_rhs_shape():
    state = np.zeros(6)
    p = REGIMES["interictal"]
    out = rhs(state, p_t=200.0, params=p)
    assert out.shape == (6,)


def test_simulate_runs():
    eeg, traj = simulate(1.0, REGIMES["interictal"], dt=1e-3,
                         rng=np.random.default_rng(0))
    assert eeg.shape == (1000,)
    assert traj.shape == (1000, 6)
    assert np.isfinite(eeg).all()


def test_regimes_differ():
    """Interictal and ictal regimes should produce signals with different variance."""
    e1, _ = simulate(2.0, REGIMES["interictal"], rng=np.random.default_rng(0))
    e2, _ = simulate(2.0, REGIMES["ictal"], rng=np.random.default_rng(0))
    # Skip transient
    e1 = e1[500:]; e2 = e2[500:]
    assert not np.allclose(e1.std(), e2.std(), rtol=0.3)


def test_simulate_recording():
    eeg, labels = simulate_recording(duration_s=10.0, target_hz=128, seed=42)
    assert eeg.shape == labels.shape
    # decimation ratio 1000//128 = 7 so ~142 samples/sec, not exactly 128
    assert 1200 <= len(eeg) <= 1500
    assert set(np.unique(labels)).issubset({0, 1, 2})


def test_simulate_recording_schedule():
    eeg, labels = simulate_recording(
        duration_s=6.0, target_hz=128, seed=1,
        schedule=[("interictal", 0, 2), ("preictal", 2, 4), ("ictal", 4, 6)],
    )
    # Each regime should appear
    assert set(np.unique(labels)) == {0, 1, 2}
