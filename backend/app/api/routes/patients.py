"""Patient-list and recording-data endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...core.patients import get_patient_store

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("")
def list_patients() -> dict:
    """List all available recordings."""
    return {"patients": get_patient_store().list_patients()}


@router.get("/{pid}")
def get_patient(pid: str) -> dict:
    """Return patient metadata (schedule, duration) WITHOUT the signal data."""
    try:
        store = get_patient_store()
        payload = store.load(pid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"patient {pid} not found")
    return {
        "id": pid,
        "meta": payload["meta"],
        "n_samples": int(len(payload["eeg"])),
    }


@router.get("/{pid}/signal")
def get_patient_signal(pid: str, start: int = 0, end: int | None = None) -> JSONResponse:
    """Return raw EEG samples in [start, end). Omit end to return the rest."""
    try:
        payload = get_patient_store().load(pid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"patient {pid} not found")
    eeg = payload["eeg"]
    labels = payload["labels"]
    if end is None:
        end = len(eeg)
    start = max(0, int(start))
    end = min(len(eeg), int(end))
    return JSONResponse({
        "id": pid,
        "start": start,
        "end": end,
        "fs": int(payload["meta"]["fs"]),
        "eeg": eeg[start:end].tolist(),
        "labels": labels[start:end].tolist(),
    })
