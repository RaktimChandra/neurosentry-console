"""Health and system-info endpoints."""
from __future__ import annotations

import platform
import time

from fastapi import APIRouter
import torch

from ... import __version__
from ...config import settings
from ...core.cache import inference_cache

router = APIRouter(prefix="/api", tags=["system"])

_START = time.time()


@router.get("/health")
def health() -> dict:
    """Liveness probe. Always returns 200 if the process is running."""
    return {"status": "ok", "version": __version__}


@router.get("/system")
def system() -> dict:
    """Detailed system info — torch version, config, uptime, cache stats."""
    return {
        "version": __version__,
        "torch": torch.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "device": "cpu",
        "fs": settings.fs,
        "window_sec": settings.window_sec,
        "stride_sec": settings.stride_sec,
        "uptime_s": round(time.time() - _START, 1),
        "cache": inference_cache.stats(),
    }
