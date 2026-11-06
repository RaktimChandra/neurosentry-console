"""Centralized configuration for the NeuroSentry Clinical Console backend."""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration. Everything is overridable via environment variables."""

    # Paths
    data_dir: Path = ROOT / "data"
    checkpoint_dir: Path = ROOT / "checkpoints"
    frontend_dist: Path = ROOT.parent / "frontend" / "dist"

    # Signal
    fs: int = 128              # Hz
    window_sec: float = 4.0    # s
    stride_sec: float = 1.0    # s

    # Model
    tcn_channels: tuple[int, ...] = (32, 32, 64, 64)
    tcn_kernel: int = 3
    tcn_dilations: tuple[int, ...] = (1, 2, 4, 8)
    tcn_dropout: float = 0.1
    pinn_hidden: int = 64
    state_dim: int = 6

    # Training (used only when bootstrapping a fresh checkpoint)
    n_recordings: int = 24
    recording_seconds: int = 60
    batch_size: int = 32
    lr: float = 5e-4
    epochs: int = 6
    seed: int = 1337

    # Loss weights (physics intentionally small — stability over strict enforcement)
    lambda_cls: float = 1.0
    lambda_hor: float = 0.2
    lambda_phys: float = 0.01
    lambda_rec: float = 0.1

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: tuple[str, ...] = ("*",)

    model_config = SettingsConfigDict(
        env_prefix="NEUROSENTRY_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def window_samples(self) -> int:
        return int(self.window_sec * self.fs)

    @property
    def stride_samples(self) -> int:
        return int(self.stride_sec * self.fs)


settings = Settings()
