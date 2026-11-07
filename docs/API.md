# API Reference

Base URL: the service root (`http://localhost:8000` locally, your Railway domain in production).

All REST endpoints return JSON. The WebSocket endpoint uses newline-delimited JSON messages.

## REST

### `GET /api/health`

Liveness probe. Always returns 200 if the process is up. No payload required.

```json
{ "status": "ok", "version": "1.0.0" }
```

### `GET /api/system`

Detailed system info — torch version, Python, platform, uptime, inference-cache stats.

```json
{
  "version": "1.0.0",
  "torch": "2.14.0",
  "python": "3.11.10",
  "platform": "Linux-6.1.0-x86_64",
  "device": "cpu",
  "fs": 128,
  "window_sec": 4.0,
  "stride_sec": 1.0,
  "uptime_s": 342.5,
  "cache": {
    "entries": 128,
    "maxsize": 1024,
    "hits": 940,
    "misses": 128,
    "hit_rate": 0.880
  }
}
```

### `GET /api/patients`

List all available recordings.

```json
{
  "patients": [
    {
      "id": "p01",
      "label": "Case A — Slow buildup",
      "description": "Extended interictal, gradual preictal transition, short ictal event.",
      "duration_s": 90.0,
      "fs": 128
    },
    ...
  ]
}
```

### `GET /api/patients/{pid}`

Patient metadata including the ground-truth regime schedule.

```json
{
  "id": "p05",
  "meta": {
    "id": "p05",
    "label": "...",
    "duration_s": 90.0,
    "fs": 128,
    "n_samples": 11454,
    "seed": 55,
    "schedule": [
      { "regime": "interictal", "start_s": 0.0, "end_s": 25.0 },
      ...
    ]
  },
  "n_samples": 11454
}
```

### `GET /api/patients/{pid}/signal?start=&end=`

Raw EEG samples with per-sample ground-truth labels. Optional `start` and `end`
sample indices.

### `POST /api/infer/window`

Run inference on a single arbitrary window. Body:

```json
{ "samples": [...]  }
```

Response includes probabilities per class, confidence, horizon (s),
inferred 6-D Jansen-Rit state over all 512 timesteps, decoded EEG
reconstruction, and inference latency (ms).

### `GET /api/infer/patient/{pid}/window/{index}`

Run inference on a specific sliding window of a stored patient. Response
additionally includes `ground_truth`, `window_index`, `window_start_s`,
`window_end_s`. Repeat hits are served from the LRU cache.

### `GET /api/infer/patient/{pid}/summary`

Run inference over **all** sliding windows for one patient and return the
full confusion matrix, overall accuracy, and per-window predictions. Takes
2–5 seconds on CPU.

### `GET /api/metrics`

Precomputed test-set metrics from the parent research repo
(`RaktimChandra/neurosentry`) — hybrid vs baseline with delta.

### `GET /api/metrics/hybrid` and `/api/metrics/baseline`

Individual model metrics.

## WebSocket

### `WS /ws/stream/{pid}`

Streams window-by-window inferences for a patient at adjustable playback
rate. Server pushes JSON messages:

- `{ "type": "meta", "patient_id", "meta", "n_windows", "window_samples", "stride_samples" }`
  (first message)
- `{ "type": "frame", "i", "t0", "t1", "eeg", "labels", "probs", "class_index",
     "class_name", "confidence", "horizon_s", "ground_truth", "state", "recon",
     "latency_ms" }` (one per window)
- `{ "type": "done", "last_index" }` (when the recording ends)
- `{ "type": "error", "detail" }` (on error)

### Client-to-server commands

Send as JSON text:

- `{ "cmd": "pause" }`
- `{ "cmd": "resume" }`
- `{ "cmd": "seek", "index": <int> }`
- `{ "cmd": "speed", "x": 1|2|4|8|16|32 }`
- `{ "cmd": "close" }`

## Response headers

All REST responses include:
- `X-Request-ID` — 12-char hex for log correlation
- `X-Response-Time-ms` — server-side processing time

## Error codes

- `400` — invalid request (bad window shape, out-of-range index)
- `404` — unknown patient id
- `5xx` — server error (see server logs)

## Rate limiting

Not enforced at the application level. Use a reverse-proxy (nginx, Railway
built-in, Cloudflare) if exposing to the public internet.
