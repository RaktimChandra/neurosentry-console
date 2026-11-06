"""WebSocket streaming endpoint for live-playback inference."""
from __future__ import annotations

import asyncio
import json

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...config import settings
from ...core.inference import get_engine
from ...core.patients import get_patient_store

router = APIRouter(tags=["stream"])


@router.websocket("/ws/stream/{pid}")
async def stream_patient(ws: WebSocket, pid: str) -> None:
    """Stream sliding-window inferences for a patient at adjustable speed.

    Protocol
    --------
    Server pushes one JSON message per window containing:
      { "i": int, "t0": float, "t1": float, "probs": [3], "class_index": int,
        "class_name": str, "confidence": float, "horizon_s": float,
        "ground_truth": int, "state": [[...], ... 6], "recon": [T], "eeg": [T] }

    Client can send control messages:
      { "cmd": "pause" }
      { "cmd": "resume" }
      { "cmd": "seek", "index": int }
      { "cmd": "speed", "x": 1|2|4|8|16|32 }
      { "cmd": "close" }
    """
    await ws.accept()

    try:
        payload = get_patient_store().load(pid)
    except FileNotFoundError:
        await ws.send_json({"type": "error",
                            "detail": f"patient {pid} not found"})
        await ws.close()
        return

    eeg = payload["eeg"]
    labels = payload["labels"]
    T = settings.window_samples
    S = settings.stride_samples
    n_windows = max(0, (len(eeg) - T) // S + 1)
    engine = get_engine()

    state = {"idx": 0, "paused": False, "speed": 4}

    async def receiver():
        try:
            while True:
                msg = await ws.receive_text()
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue
                cmd = data.get("cmd")
                if cmd == "pause":
                    state["paused"] = True
                elif cmd == "resume":
                    state["paused"] = False
                elif cmd == "seek":
                    idx = int(data.get("index", 0))
                    state["idx"] = max(0, min(n_windows - 1, idx))
                elif cmd == "speed":
                    x = int(data.get("x", 4))
                    state["speed"] = max(1, min(32, x))
                elif cmd == "close":
                    break
        except WebSocketDisconnect:
            pass

    recv_task = asyncio.create_task(receiver())

    await ws.send_json({
        "type": "meta",
        "patient_id": pid,
        "meta": payload["meta"],
        "n_windows": n_windows,
        "window_samples": T,
        "stride_samples": S,
    })

    try:
        while state["idx"] < n_windows:
            if state["paused"]:
                await asyncio.sleep(0.05)
                continue

            i = state["idx"]
            start = i * S
            end = start + T
            window = eeg[start:end]
            result = engine.infer_window(window)
            true_label = int(np.bincount(labels[start:end], minlength=3).argmax())

            await ws.send_json({
                "type": "frame",
                "i": i,
                "t0": round(start / settings.fs, 3),
                "t1": round(end / settings.fs, 3),
                "eeg": window.tolist(),
                "labels": labels[start:end].tolist(),
                "probs": result["probs"],
                "class_index": result["class_index"],
                "class_name": result["class_name"],
                "confidence": result["confidence"],
                "horizon_s": result["horizon_s"],
                "ground_truth": true_label,
                # Send only key state components to keep payload light; downsample
                "state": [s[::4] for s in result["state"]],  # 6 x T/4
                "recon": result["recon"][::2],               # T/2
                "latency_ms": result["latency_ms"],
            })

            state["idx"] = i + 1
            # Playback cadence: one window per stride-second / speed
            delay = settings.stride_sec / float(state["speed"])
            await asyncio.sleep(delay)

        await ws.send_json({"type": "done", "last_index": n_windows - 1})
    except WebSocketDisconnect:
        pass
    finally:
        recv_task.cancel()
        try:
            await ws.close()
        except Exception:
            pass
