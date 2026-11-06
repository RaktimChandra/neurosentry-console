"""Inference endpoints: run the model on a window or on a whole recording."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import numpy as np

from ...config import settings
from ...core.inference import get_engine
from ...core.patients import get_patient_store

router = APIRouter(prefix="/api/infer", tags=["inference"])


class InferenceRequest(BaseModel):
    """Raw window payload."""
    samples: list[float] = Field(..., description="EEG samples at 128 Hz")


@router.post("/window")
def infer_window(req: InferenceRequest) -> dict:
    """Run the hybrid model on one raw window."""
    if len(req.samples) == 0:
        raise HTTPException(status_code=400, detail="empty window")
    window = np.asarray(req.samples, dtype=np.float32)
    engine = get_engine()
    result = engine.infer_window(window)
    return result


@router.get("/patient/{pid}/window/{index}")
def infer_patient_window(pid: str, index: int) -> dict:
    """Run inference on a specific sliding window of a stored patient."""
    try:
        payload = get_patient_store().load(pid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"patient {pid} not found")

    T = settings.window_samples
    S = settings.stride_samples
    eeg = payload["eeg"]
    labels = payload["labels"]
    n_windows = max(0, (len(eeg) - T) // S + 1)
    if index < 0 or index >= n_windows:
        raise HTTPException(status_code=400,
                            detail=f"window index {index} out of [0, {n_windows})")
    start = index * S
    end = start + T
    window = eeg[start:end]
    engine = get_engine()
    result = engine.infer_window(window)
    # Majority ground-truth label in this window
    true_label = int(np.bincount(labels[start:end], minlength=3).argmax())
    result["ground_truth"] = true_label
    result["window_index"] = index
    result["window_start_s"] = round(start / settings.fs, 3)
    result["window_end_s"] = round(end / settings.fs, 3)
    return result


@router.get("/patient/{pid}/summary")
def summarise_patient(pid: str) -> dict:
    """Run inference over ALL sliding windows for one patient (cheap, cached)."""
    try:
        payload = get_patient_store().load(pid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"patient {pid} not found")

    T = settings.window_samples
    S = settings.stride_samples
    eeg = payload["eeg"]
    labels = payload["labels"]

    engine = get_engine()

    results = []
    cum_cm = np.zeros((3, 3), dtype=np.int64)
    for idx, start in enumerate(range(0, len(eeg) - T + 1, S)):
        window = eeg[start:start + T]
        out = engine.infer_window(window)
        true = int(np.bincount(labels[start:start + T], minlength=3).argmax())
        cum_cm[true, out["class_index"]] += 1
        results.append({
            "i": idx,
            "t0": round(start / settings.fs, 3),
            "t1": round((start + T) / settings.fs, 3),
            "true": true,
            "pred": out["class_index"],
            "probs": out["probs"],
            "confidence": out["confidence"],
        })
    diag = int(np.trace(cum_cm))
    total = int(cum_cm.sum())
    acc = (diag / total) if total else 0.0
    return {
        "id": pid,
        "n_windows": len(results),
        "accuracy": acc,
        "confusion_matrix": cum_cm.tolist(),
        "results": results,
    }
