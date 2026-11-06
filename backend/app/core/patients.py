"""Patient-recording store.

A small, deterministically-seeded set of synthetic EEG recordings that the console
plays back. Each 'patient' corresponds to a different ground-truth regime schedule,
so a reviewer can switch between recordings to see the model handle different
transition patterns.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np

from .jansen_rit import simulate_recording
from ..config import Settings, settings as default_settings


@dataclass
class PatientMeta:
    id: str
    label: str
    description: str
    duration_s: float
    fs: int
    n_samples: int
    seed: int
    schedule: list[dict[str, Any]]


class PatientStore:
    """Generates and caches patient recordings on disk."""

    _CATALOG = [
        # id, label, description, duration, seed, schedule
        ("p01", "Case A — Slow buildup",
         "Extended interictal, gradual preictal transition, short ictal event.",
         90.0, 11, [
             ("interictal", 0.0, 30.0),
             ("preictal", 30.0, 50.0),
             ("ictal", 50.0, 62.0),
             ("interictal", 62.0, 90.0),
         ]),
        ("p02", "Case B — Rapid onset",
         "Short preictal window followed by a prolonged ictal episode.",
         80.0, 22, [
             ("interictal", 0.0, 20.0),
             ("preictal", 20.0, 26.0),
             ("ictal", 26.0, 50.0),
             ("interictal", 50.0, 80.0),
         ]),
        ("p03", "Case C — Multiple events",
         "Two separate seizure events separated by a resting period.",
         120.0, 33, [
             ("interictal", 0.0, 18.0),
             ("preictal", 18.0, 25.0),
             ("ictal", 25.0, 35.0),
             ("interictal", 35.0, 65.0),
             ("preictal", 65.0, 72.0),
             ("ictal", 72.0, 85.0),
             ("interictal", 85.0, 120.0),
         ]),
        ("p04", "Case D — Interictal only",
         "No seizure activity. Used to verify specificity (no false alarms).",
         75.0, 44, [
             ("interictal", 0.0, 75.0),
         ]),
        ("p05", "Case E — Classical presentation",
         "Standard three-phase pattern: baseline, buildup, seizure, recovery.",
         90.0, 55, [
             ("interictal", 0.0, 25.0),
             ("preictal", 25.0, 38.0),
             ("ictal", 38.0, 52.0),
             ("interictal", 52.0, 90.0),
         ]),
        ("p06", "Case F — Late onset",
         "Long interictal lead-in, abrupt transition near end of recording.",
         100.0, 66, [
             ("interictal", 0.0, 70.0),
             ("preictal", 70.0, 78.0),
             ("ictal", 78.0, 95.0),
             ("interictal", 95.0, 100.0),
         ]),
    ]

    def __init__(self, cfg: Settings = default_settings) -> None:
        self.cfg = cfg
        self.data_dir = cfg.data_dir / "patients"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}
        self._ensure_all()

    def _path(self, pid: str) -> Path:
        return self.data_dir / f"{pid}.npz"

    def _meta_path(self, pid: str) -> Path:
        return self.data_dir / f"{pid}.json"

    def _ensure_all(self) -> None:
        for (pid, label, desc, duration, seed, sched) in self._CATALOG:
            p = self._path(pid)
            if p.exists() and self._meta_path(pid).exists():
                continue
            print(f"[patients] generating {pid} ({label})...")
            eeg, labels = simulate_recording(
                duration_s=duration,
                target_hz=self.cfg.fs,
                seed=seed,
                schedule=sched,
            )
            np.savez_compressed(p, eeg=eeg.astype(np.float32),
                                labels=labels.astype(np.int64))
            meta = PatientMeta(
                id=pid,
                label=label,
                description=desc,
                duration_s=duration,
                fs=self.cfg.fs,
                n_samples=len(eeg),
                seed=seed,
                schedule=[
                    {"regime": name, "start_s": s, "end_s": e}
                    for (name, s, e) in sched
                ],
            )
            with open(self._meta_path(pid), "w") as f:
                json.dump(asdict(meta), f, indent=2)

    def list_patients(self) -> list[dict[str, Any]]:
        out = []
        for (pid, label, desc, duration, _, _) in self._CATALOG:
            out.append({
                "id": pid,
                "label": label,
                "description": desc,
                "duration_s": duration,
                "fs": self.cfg.fs,
            })
        return out

    def load(self, pid: str) -> dict[str, Any]:
        if pid in self._cache:
            return self._cache[pid]
        p = self._path(pid)
        if not p.exists():
            raise FileNotFoundError(pid)
        npz = np.load(p)
        with open(self._meta_path(pid)) as f:
            meta = json.load(f)
        payload = {
            "id": pid,
            "meta": meta,
            "eeg": npz["eeg"],      # (n,) float32
            "labels": npz["labels"],  # (n,) int64
        }
        self._cache[pid] = payload
        return payload


_store: PatientStore | None = None


def get_patient_store(cfg: Settings | None = None) -> PatientStore:
    global _store
    if _store is None:
        _store = PatientStore(cfg or default_settings)
    return _store


__all__ = ["PatientStore", "get_patient_store", "PatientMeta"]
