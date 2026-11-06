"""Serve the precomputed test-set metrics."""
from __future__ import annotations

from fastapi import APIRouter

from ...core.metrics import HYBRID_METRICS, BASELINE_METRICS, all_metrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def get_all() -> dict:
    return all_metrics()


@router.get("/hybrid")
def get_hybrid() -> dict:
    return HYBRID_METRICS


@router.get("/baseline")
def get_baseline() -> dict:
    return BASELINE_METRICS
