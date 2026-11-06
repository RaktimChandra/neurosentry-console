"""Bootstrap training: run once on fresh deployment to produce a checkpoint.

The idea is that the console must have a real trained model for inference, but we
don't want to ship a 300 MB checkpoint in the Docker image. So on first startup, if
no checkpoint exists, we synthesise a small dataset from the Jansen-Rit simulator
and train the hybrid model for a few epochs — takes ~45 seconds on CPU — and save
the resulting weights. Future starts just load the cached checkpoint.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from .jansen_rit import simulate_recording
from .models import HybridForecaster, jr_rhs_torch
from ..config import Settings, settings as default_settings


def _make_dataset(cfg: Settings) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Simulate a mini dataset and slice it into training windows."""
    rng = np.random.default_rng(cfg.seed)
    all_windows: list[np.ndarray] = []
    all_labels: list[int] = []
    all_horizons: list[float] = []

    for i in range(cfg.n_recordings):
        eeg, labels = simulate_recording(
            duration_s=float(cfg.recording_seconds),
            target_hz=cfg.fs,
            seed=int(rng.integers(0, 2**31 - 1)),
        )
        # Slide windows
        T, S = cfg.window_samples, cfg.stride_samples
        # Find ictal onset for horizon regression
        ictal_idx = np.where(labels == 2)[0]
        onset = int(ictal_idx[0]) if len(ictal_idx) else len(labels)

        for start in range(0, len(eeg) - T + 1, S):
            win = eeg[start:start + T]
            lab = int(np.bincount(labels[start:start + T], minlength=3).argmax())
            # Horizon: seconds from the END of this window to ictal onset
            end_sample = start + T - 1
            horizon = max(0.0, (onset - end_sample) / cfg.fs)
            # z-score per window
            mu = float(win.mean())
            sd = float(win.std() + 1e-6)
            all_windows.append(((win - mu) / sd).astype(np.float32))
            all_labels.append(lab)
            all_horizons.append(float(horizon))

    X = torch.tensor(np.stack(all_windows))
    y = torch.tensor(all_labels, dtype=torch.long)
    h = torch.tensor(all_horizons, dtype=torch.float32)
    return X, y, h


def _physics_loss(state: torch.Tensor, A: float, B: float,
                  fs: int, eps: float = 1e-3) -> torch.Tensor:
    """Normalised weak-form Jansen-Rit residual, per-component scaled."""
    dt = 1.0 / fs
    # state: (B, 6, T)
    ds_dt = torch.zeros_like(state)
    ds_dt[:, :, 1:-1] = (state[:, :, 2:] - state[:, :, :-2]) / (2 * dt)
    ds_dt[:, :, 0] = (state[:, :, 1] - state[:, :, 0]) / dt
    ds_dt[:, :, -1] = (state[:, :, -1] - state[:, :, -2]) / dt
    p = torch.full((state.shape[0], state.shape[2]), 260.0,
                   device=state.device, dtype=state.dtype)
    f = jr_rhs_torch(state, p, A=A, B=B)
    # Per-component normalisation (crucial — components span 4 orders of magnitude)
    # Normalise each component by its own RMS
    comp_scale = f.detach().pow(2).mean(dim=(0, 2)).sqrt().clamp(min=eps)  # (6,)
    residual = (ds_dt - f) / comp_scale.view(1, 6, 1)
    loss = residual.pow(2).mean()
    # Final guard — map to log scale and clamp to prevent explosion
    return torch.log1p(loss.clamp(max=1e6))


def train_fresh_checkpoint(cfg: Settings = default_settings,
                           out_path: Path | None = None,
                           verbose: bool = True) -> Path:
    """Train a hybrid model from scratch and save weights."""
    out_path = out_path or (cfg.checkpoint_dir / "hybrid.pt")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)

    if verbose:
        print(f"[train] synthesising dataset of {cfg.n_recordings} recordings...")
    t0 = time.perf_counter()
    X, y, h = _make_dataset(cfg)
    if verbose:
        print(f"[train] dataset shape: X={tuple(X.shape)} y={tuple(y.shape)} "
              f"({time.perf_counter() - t0:.1f}s)")

    # Class weights
    counts = torch.bincount(y, minlength=3).float()
    cls_w = (counts.sum() / (3.0 * counts.clamp(min=1.0)))

    model = HybridForecaster(cfg)
    optim = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=cfg.epochs)

    loader = DataLoader(TensorDataset(X, y, h), batch_size=cfg.batch_size,
                        shuffle=True, drop_last=False)

    model.train()
    for epoch in range(cfg.epochs):
        t_ep = time.perf_counter()
        losses, accs = [], []
        for xb, yb, hb in loader:
            xb_norm = (xb - xb.mean(dim=1, keepdim=True)) / (
                xb.std(dim=1, keepdim=True) + 1e-6)
            out = model(xb_norm)
            # classification
            loss_cls = F.cross_entropy(out["logits"], yb, weight=cls_w)
            # horizon (masked: only on preictal windows)
            mask = (yb == 1)
            if mask.any():
                loss_hor = F.smooth_l1_loss(
                    torch.log1p(out["horizon"][mask]),
                    torch.log1p(hb[mask]))
            else:
                loss_hor = torch.tensor(0.0)
            # physics (average of 3 regimes' A/B; we average over mini-batch)
            loss_phys = _physics_loss(out["state"], A=3.25, B=18.0, fs=cfg.fs)
            # reconstruction
            loss_rec = F.mse_loss(out["recon"], xb_norm)

            loss = (cfg.lambda_cls * loss_cls
                    + cfg.lambda_hor * loss_hor
                    + cfg.lambda_phys * loss_phys
                    + cfg.lambda_rec * loss_rec)
            # Guard against any NaN/Inf that would corrupt weights
            if not torch.isfinite(loss):
                continue
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            losses.append(float(loss.item()))
            accs.append(float((out["logits"].argmax(-1) == yb).float().mean().item()))
        sched.step()
        if verbose:
            print(f"[train] epoch {epoch+1:02d}/{cfg.epochs}  "
                  f"loss={np.mean(losses):.4f}  acc={np.mean(accs):.4f}  "
                  f"({time.perf_counter() - t_ep:.1f}s)")

    model.eval()
    torch.save({
        "model_state": model.state_dict(),
        "config": {
            "tcn_channels": list(cfg.tcn_channels),
            "tcn_kernel": cfg.tcn_kernel,
            "tcn_dilations": list(cfg.tcn_dilations),
            "tcn_dropout": cfg.tcn_dropout,
            "pinn_hidden": cfg.pinn_hidden,
            "state_dim": cfg.state_dim,
            "fs": cfg.fs,
            "window_sec": cfg.window_sec,
        },
    }, out_path)
    if verbose:
        print(f"[train] saved checkpoint to {out_path} "
              f"({out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


__all__ = ["train_fresh_checkpoint"]
