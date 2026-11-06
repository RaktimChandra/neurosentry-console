"""Health and system-info endpoints."""
from __future__ import annotations

from fastapi import APIRouter
import torch

from ... import __version__
from ...config import settings

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/system")
def system() -> dict:
    return {
        "version": __version__,
        "torch": torch.__version__,
        "device": "cpu",
        "fs": settings.fs,
        "window_sec": settings.window_sec,
        "stride_sec": settings.stride_sec,
    }
