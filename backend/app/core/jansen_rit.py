"""Jansen-Rit neural mass model.

Implements the 1995 Jansen-Rit cortical column as six coupled ordinary differential
equations. Used both for synthesizing patient EEG recordings and for computing the
physics residual in the PINN loss. See:

  B. H. Jansen and V. G. Rit (1995). Electroencephalogram and visual evoked
  potential generation in a mathematical model of coupled cortical columns.
  Biological Cybernetics, 73(4): 357-366.

  F. Wendling et al. (2000). Relevance of nonlinear lumped-parameter models in
  the analysis of depth-EEG epileptic signals. Biological Cybernetics 83: 367-378.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


# Canonical parameter values from Jansen-Rit (1995). Units: mV, s^-1.
A_DEFAULT = 3.25           # excitatory PSP amplitude (mV)
B_DEFAULT = 22.0           # inhibitory PSP amplitude (mV)
A_RATE = 100.0             # excitatory time constant (s^-1)
B_RATE = 50.0              # inhibitory time constant (s^-1)
E0 = 2.5                   # max firing rate (s^-1)
R = 0.56                   # sigmoid slope (mV^-1)
V0 = 6.0                   # sigmoid midpoint (mV)
C = 135.0                  # base connectivity
C1, C2, C3, C4 = C, 0.8 * C, 0.25 * C, 0.25 * C


@dataclass
class JansenRitParams:
    """Jansen-Rit model parameters. B and p_mu are the regime-controlling variables."""
    A: float = A_DEFAULT
    B: float = B_DEFAULT
    a: float = A_RATE
    b: float = B_RATE
    p_mu: float = 220.0
    p_sigma: float = 22.0


# Three regime presets (interictal/preictal/ictal) following Wendling 2000.
REGIMES = {
    "interictal": JansenRitParams(B=22.0, p_mu=220.0),
    "preictal":   JansenRitParams(B=17.0, p_mu=260.0),
    "ictal":      JansenRitParams(B=14.0, p_mu=300.0),
}


def sigmoid(v: np.ndarray) -> np.ndarray:
    """Jansen-Rit sigmoidal firing rate."""
    return 2.0 * E0 / (1.0 + np.exp(R * (V0 - v)))


def rhs(state: np.ndarray, p_t: float, params: JansenRitParams) -> np.ndarray:
    """Right-hand side of the Jansen-Rit ODE at one instant.

    state = [y0, y1, y2, y3, y4, y5] with y3..y5 the time derivatives of y0..y2.
    """
    y0, y1, y2, y3, y4, y5 = state
    A, B, a, b = params.A, params.B, params.a, params.b

    sigm_ex = sigmoid(y1 - y2)
    sigm_py = sigmoid(C1 * y0)
    sigm_in = sigmoid(C3 * y0)

    d_y0 = y3
    d_y3 = A * a * sigm_ex - 2.0 * a * y3 - a * a * y0

    d_y1 = y4
    d_y4 = A * a * (p_t + C2 * sigm_py) - 2.0 * a * y4 - a * a * y1

    d_y2 = y5
    d_y5 = B * b * C4 * sigm_in - 2.0 * b * y5 - b * b * y2

    return np.array([d_y0, d_y1, d_y2, d_y3, d_y4, d_y5], dtype=np.float64)


def simulate(duration_s: float, params: JansenRitParams, *,
             dt: float = 1e-3, rng: np.random.Generator | None = None,
             initial: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the Jansen-Rit ODE with explicit fourth-order Runge-Kutta.

    Returns
    -------
    eeg : np.ndarray, shape (n,)   observable EEG proxy y1 - y2 at `dt` resolution
    traj : np.ndarray, shape (n, 6)  full 6D state trajectory
    """
    if rng is None:
        rng = np.random.default_rng(0)
    n = int(duration_s / dt)
    state = initial if initial is not None else np.zeros(6, dtype=np.float64)
    # stochastic drive p(t) ~ N(p_mu, p_sigma)
    p = rng.normal(params.p_mu, params.p_sigma, size=n)

    traj = np.empty((n, 6), dtype=np.float64)
    for t in range(n):
        p_t = p[t]
        k1 = rhs(state,              p_t, params)
        k2 = rhs(state + 0.5 * dt * k1, p_t, params)
        k3 = rhs(state + 0.5 * dt * k2, p_t, params)
        k4 = rhs(state + dt * k3,       p_t, params)
        state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[t] = state

    eeg = traj[:, 1] - traj[:, 2]
    return eeg, traj


def downsample(x: np.ndarray, from_hz: int, to_hz: int) -> np.ndarray:
    """Anti-aliased downsample from `from_hz` to `to_hz`."""
    from scipy.signal import decimate
    q = from_hz // to_hz
    if q <= 1:
        return x
    return decimate(x, q, ftype="fir", zero_phase=True)


def simulate_recording(duration_s: float = 90.0, *,
                       target_hz: int = 128,
                       seed: int | None = None,
                       schedule: list[tuple[str, float, float]] | None = None
                       ) -> tuple[np.ndarray, np.ndarray]:
    """Simulate a multi-regime recording and return (eeg, per_sample_labels).

    `schedule` is a list of (regime_name, start_s, end_s) tuples. If None, a
    random three-regime schedule is used: interictal → preictal → ictal → interictal.
    `labels` is 0=interictal, 1=preictal, 2=ictal.
    """
    rng = np.random.default_rng(seed)
    dt = 1e-3
    internal_hz = int(1.0 / dt)

    if schedule is None:
        # Random schedule with at least one preictal→ictal transition
        t0 = 0.0
        t1 = rng.uniform(20.0, 35.0)
        t2 = t1 + rng.uniform(5.0, 12.0)
        t3 = t2 + rng.uniform(4.0, 10.0)
        t4 = duration_s
        schedule = [
            ("interictal", t0, t1),
            ("preictal", t1, t2),
            ("ictal", t2, t3),
            ("interictal", t3, t4),
        ]

    # Simulate each segment with continuous initial state
    n_internal = int(duration_s * internal_hz)
    eeg_internal = np.zeros(n_internal, dtype=np.float64)
    labels_internal = np.zeros(n_internal, dtype=np.int64)
    state = np.zeros(6, dtype=np.float64)
    name_to_idx = {"interictal": 0, "preictal": 1, "ictal": 2}

    for (name, s, e) in schedule:
        seg_dur = max(0.0, e - s)
        if seg_dur <= 0:
            continue
        seg_eeg, seg_traj = simulate(seg_dur, REGIMES[name], dt=dt, rng=rng,
                                     initial=state)
        state = seg_traj[-1].copy()
        i0 = int(s * internal_hz)
        i1 = i0 + len(seg_eeg)
        if i1 > n_internal:
            i1 = n_internal
            seg_eeg = seg_eeg[: i1 - i0]
        eeg_internal[i0:i1] = seg_eeg
        labels_internal[i0:i1] = name_to_idx[name]

    # Downsample EEG; subsample labels
    eeg = downsample(eeg_internal, internal_hz, target_hz).astype(np.float32)
    q = internal_hz // target_hz
    labels = labels_internal[::q][: len(eeg)].astype(np.int64)
    return eeg, labels


__all__ = [
    "JansenRitParams",
    "REGIMES",
    "sigmoid",
    "rhs",
    "simulate",
    "simulate_recording",
    "downsample",
    "C1", "C2", "C3", "C4", "E0", "R", "V0",
]
