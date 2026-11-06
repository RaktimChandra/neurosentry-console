"""Inference service: loads checkpoint, runs model on windows."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .models import HybridForecaster
from ..config import Settings, settings as default_settings


CLASS_NAMES = ["interictal", "preictal", "ictal"]


class InferenceEngine:
    """Thin wrapper around the trained hybrid model."""

    def __init__(self, cfg: Settings = default_settings,
                 checkpoint_path: Path | None = None) -> None:
        self.cfg = cfg
        self.device = torch.device("cpu")
        self.model = HybridForecaster(cfg).to(self.device)
        self.checkpoint_path = checkpoint_path or (cfg.checkpoint_dir / "hybrid.pt")
        self._load_or_train()
        self.model.eval()

    def _load_or_train(self) -> None:
        """Load an existing checkpoint, or train one if missing."""
        if self.checkpoint_path.exists():
            payload = torch.load(self.checkpoint_path, map_location=self.device,
                                 weights_only=False)
            self.model.load_state_dict(payload["model_state"])
            print(f"[infer] loaded checkpoint {self.checkpoint_path}")
        else:
            print(f"[infer] no checkpoint found; bootstrapping a fresh one...")
            from .training import train_fresh_checkpoint
            train_fresh_checkpoint(self.cfg, out_path=self.checkpoint_path)
            payload = torch.load(self.checkpoint_path, map_location=self.device,
                                 weights_only=False)
            self.model.load_state_dict(payload["model_state"])

    @torch.no_grad()
    def infer_window(self, window: np.ndarray) -> dict[str, Any]:
        """Run the model on one 4-second window.

        Parameters
        ----------
        window : np.ndarray, shape (T,)
            Raw EEG window, any scale. Will be z-scored internally.

        Returns
        -------
        dict with: probs (3,), predicted class str, confidence float,
                   horizon float (s), state (6, T), recon (T,), latency ms.
        """
        t0 = time.perf_counter()
        T = self.cfg.window_samples
        if len(window) != T:
            # Pad or truncate
            w = np.zeros(T, dtype=np.float32)
            n = min(T, len(window))
            w[:n] = window[:n]
            window = w

        mu = float(window.mean())
        sd = float(window.std() + 1e-6)
        x = torch.from_numpy((window - mu) / sd).float().unsqueeze(0).unsqueeze(0)

        out = self.model(x)
        probs = torch.softmax(out["logits"], dim=-1)[0].cpu().numpy()
        pred = int(probs.argmax())
        conf = float(probs[pred])
        horizon = float(out["horizon"][0].item())
        state = out["state"][0].cpu().numpy()        # (6, T)
        recon = out["recon"][0].cpu().numpy()        # (T,)
        # Un-normalise reconstruction for display parity with input
        recon_raw = recon * sd + mu

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "probs": probs.tolist(),
            "class_name": CLASS_NAMES[pred],
            "class_index": pred,
            "confidence": conf,
            "horizon_s": max(0.0, horizon),
            "state": state.tolist(),                 # list of 6 lists of T floats
            "recon": recon_raw.tolist(),
            "latency_ms": latency_ms,
        }


# Lazily initialised singleton
_engine: InferenceEngine | None = None


def get_engine(cfg: Settings | None = None) -> InferenceEngine:
    global _engine
    if _engine is None:
        _engine = InferenceEngine(cfg or default_settings)
    return _engine


__all__ = ["InferenceEngine", "get_engine", "CLASS_NAMES"]
