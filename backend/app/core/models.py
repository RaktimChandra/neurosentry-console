"""NeuroSentry hybrid TCN + PINN model, PyTorch implementation.

Mirrors the architecture from the parent research repo so trained checkpoints are
load-compatible. Three heads share a causal dilated TCN encoder:

  - classifier head  → {interictal, preictal, ictal} softmax
  - horizon head     → seconds-to-seizure regression
  - PINN head        → 6-D Jansen-Rit state at every timestep
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .jansen_rit import A_RATE, B_RATE, C1, C2, C3, C4, E0, R, V0


# ---------------------------------------------------------------------- TCN


class Chomp1d(nn.Module):
    """Removes the padding added for causal convolution."""

    def __init__(self, chomp_size: int) -> None:
        super().__init__()
        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[:, :, : -self.chomp_size].contiguous()


class TemporalBlock(nn.Module):
    """One residual block: two dilated causal convs + ReLU + dropout + skip."""

    def __init__(self, in_c: int, out_c: int, kernel: int,
                 dilation: int, dropout: float) -> None:
        super().__init__()
        padding = (kernel - 1) * dilation
        self.conv1 = nn.utils.parametrizations.weight_norm(
            nn.Conv1d(in_c, out_c, kernel, padding=padding, dilation=dilation)
        )
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.ReLU()
        self.drop1 = nn.Dropout(dropout)

        self.conv2 = nn.utils.parametrizations.weight_norm(
            nn.Conv1d(out_c, out_c, kernel, padding=padding, dilation=dilation)
        )
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.ReLU()
        self.drop2 = nn.Dropout(dropout)

        self.down = nn.Conv1d(in_c, out_c, 1) if in_c != out_c else None
        self.out_relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.drop1(self.relu1(self.chomp1(self.conv1(x))))
        out = self.drop2(self.relu2(self.chomp2(self.conv2(out))))
        res = x if self.down is None else self.down(x)
        return self.out_relu(out + res)


class TCNEncoder(nn.Module):
    """Stacked residual temporal blocks with exponentially growing dilations."""

    def __init__(self, channels: tuple[int, ...], kernel: int,
                 dilations: tuple[int, ...], dropout: float) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        in_c = 1
        for out_c, d in zip(channels, dilations):
            layers.append(TemporalBlock(in_c, out_c, kernel, d, dropout))
            in_c = out_c
        self.net = nn.Sequential(*layers)
        self.out_channels = channels[-1]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 1, T) → (B, C, T)."""
        return self.net(x)


# ---------------------------------------------------------------------- PINN head


class PINNHead(nn.Module):
    """Maps latent z(t) to a physiologically-constrained 6-D Jansen-Rit state."""

    def __init__(self, in_c: int, hidden: int = 64, state_dim: int = 6) -> None:
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_c, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, state_dim),
        )
        # 0.1 gain on the last layer stabilises the physics residual at init
        with torch.no_grad():
            self.mlp[-1].weight.mul_(0.1)
            self.mlp[-1].bias.zero_()

        # Physiologically plausible per-component ranges
        self.register_buffer("state_scale",
                             torch.tensor([20., 20., 20., 500., 500., 500.]))
        self.register_buffer("state_bias",
                             torch.tensor([5., 10., 5., 0., 0., 0.]))

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """z: (B, C, T) → s_hat: (B, 6, T)."""
        raw = self.mlp(z.transpose(1, 2))         # (B, T, 6)
        s = torch.tanh(raw) * self.state_scale + self.state_bias
        return s.transpose(1, 2)                   # (B, 6, T)


# ---------------------------------------------------------------------- Hybrid model


class HybridForecaster(nn.Module):
    """Hybrid TCN + PINN with three parallel heads."""

    def __init__(self, cfg) -> None:
        super().__init__()
        self.cfg = cfg
        self.encoder = TCNEncoder(cfg.tcn_channels, cfg.tcn_kernel,
                                  cfg.tcn_dilations, cfg.tcn_dropout)
        c = self.encoder.out_channels

        # Classifier head: temporal avg pool → 3 logits
        self.cls_head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1), nn.Flatten(),
            nn.Linear(c, 64), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(64, 3),
        )
        # Horizon head: temporal max pool → scalar
        self.hor_head = nn.Sequential(
            nn.AdaptiveMaxPool1d(1), nn.Flatten(),
            nn.Linear(c, 64), nn.ReLU(),
            nn.Linear(64, 1),
        )
        # PINN head
        self.pinn_head = PINNHead(c, hidden=cfg.pinn_hidden,
                                  state_dim=cfg.state_dim)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        """x: (B, T) or (B, 1, T) → dict of head outputs."""
        if x.dim() == 2:
            x = x.unsqueeze(1)
        z = self.encoder(x)                           # (B, C, T)
        logits = self.cls_head(z)                     # (B, 3)
        horizon = self.hor_head(z).squeeze(-1)        # (B,)
        state = self.pinn_head(z)                     # (B, 6, T)
        recon = state[:, 1, :] - state[:, 2, :]       # EEG proxy from PINN
        return dict(logits=logits, horizon=horizon,
                    state=state, recon=recon, latent=z)


# --------------------------------------------- PyTorch Jansen-Rit RHS (for loss)


def sigmoid_torch(v: torch.Tensor) -> torch.Tensor:
    return 2.0 * E0 / (1.0 + torch.exp(R * (V0 - v)))


def jr_rhs_torch(state: torch.Tensor, p: torch.Tensor, A: float, B: float,
                 a: float = A_RATE, b: float = B_RATE) -> torch.Tensor:
    """Jansen-Rit RHS, batched over (B, 6, T).

    state: (B, 6, T), p: (B, T) stochastic drive.
    """
    y0, y1, y2 = state[:, 0], state[:, 1], state[:, 2]
    y3, y4, y5 = state[:, 3], state[:, 4], state[:, 5]
    sigm_ex = sigmoid_torch(y1 - y2)
    sigm_py = sigmoid_torch(C1 * y0)
    sigm_in = sigmoid_torch(C3 * y0)
    d_y0 = y3
    d_y3 = A * a * sigm_ex - 2.0 * a * y3 - a * a * y0
    d_y1 = y4
    d_y4 = A * a * (p + C2 * sigm_py) - 2.0 * a * y4 - a * a * y1
    d_y2 = y5
    d_y5 = B * b * C4 * sigm_in - 2.0 * b * y5 - b * b * y2
    return torch.stack([d_y0, d_y1, d_y2, d_y3, d_y4, d_y5], dim=1)


__all__ = ["HybridForecaster", "TCNEncoder", "PINNHead", "jr_rhs_torch"]
