"""Precomputed test-set metrics served as JSON.

These mirror the actual numbers reported in the parent repo's evaluation output.
"""
from __future__ import annotations

HYBRID_METRICS = {
    "model": "hybrid",
    "test": {
        "accuracy": 0.9742,
        "macro_f1": 0.9682,
        "confusion_matrix": [[240, 4, 0], [0, 163, 7], [0, 2, 88]],
        "auc_per_class": {
            "interictal": 1.000,
            "preictal": 0.9932,
            "ictal": 0.9922,
        },
        "false_alarm_per_hour": 59.02,
        "median_warning_horizon_s": 1.0,
        "n_alarms": 253,
        "physics_residual_mean": 1.3571,
        "support_per_class": {"interictal": 244, "preictal": 170, "ictal": 90},
    },
    "params": 72554,
    "training": {
        "epochs": 10,
        "batch_size": 32,
        "optimizer": "Adam",
        "lr": 1e-3,
    },
}

BASELINE_METRICS = {
    "model": "baseline",
    "test": {
        "accuracy": 0.9683,
        "macro_f1": 0.9571,
        "auc_per_class": {
            "interictal": 1.000,
            "preictal": 0.9926,
            "ictal": 0.9913,
        },
        "false_alarm_per_hour": 14.75,
        "median_warning_horizon_s": 1.0,
    },
    "params": 63844,
}


def all_metrics() -> dict:
    return {
        "hybrid": HYBRID_METRICS,
        "baseline": BASELINE_METRICS,
        "delta": {
            "accuracy": round(
                HYBRID_METRICS["test"]["accuracy"] - BASELINE_METRICS["test"]["accuracy"], 4),
            "macro_f1": round(
                HYBRID_METRICS["test"]["macro_f1"] - BASELINE_METRICS["test"]["macro_f1"], 4),
        },
    }


__all__ = ["HYBRID_METRICS", "BASELINE_METRICS", "all_metrics"]
