# Architecture

NeuroSentry Clinical Console is a single-service full-stack application. One
FastAPI process loads the trained hybrid TCN + PINN model, maintains a cache of
synthesised EEG recordings, exposes a REST + WebSocket API, and serves the
pre-built React SPA from its static-file routes.

```
                 ┌───────────────────────────────────────────────┐
                 │               FastAPI process                 │
                 │                                               │
    ┌────────┐   │   ┌──────────────┐   ┌────────────────────┐   │
    │ Client │◀──┼───│  REST  /api  │   │ HybridForecaster   │   │
    │ (React)│   │   │  WS   /ws    │──▶│  TCN + PINN heads  │   │
    └────────┘   │   └──────────────┘   └────────┬───────────┘   │
         ▲       │                                │               │
         │       │                                ▼               │
         │       │                     ┌──────────────────────┐   │
         └───────┼────  GET /  ◀───────│ Static SPA bundle    │   │
                 │                     │ (built with Vite)    │   │
                 │                     └──────────────────────┘   │
                 │                                                │
                 │        ┌────────────────────────┐              │
                 │        │ PatientStore           │              │
                 │        │  - synth JR recordings │              │
                 │        │  - cached on disk      │              │
                 │        └────────────────────────┘              │
                 └───────────────────────────────────────────────┘
```

## Backend layers

### `app.core.jansen_rit`
Pure NumPy implementation of the Jansen-Rit six-dimensional neural-mass model:
- Three parameter presets for the interictal, preictal and ictal regimes
- Explicit fourth-order Runge-Kutta integrator at 1 kHz
- Anti-aliased downsampling to 128 Hz for storage and model input
- `simulate_recording(duration, target_hz, seed, schedule)` builds a full
  multi-regime recording with per-sample ground-truth labels

### `app.core.models`
PyTorch implementation of the hybrid model, binary-compatible with the parent
research repo's checkpoints:
- `TCNEncoder` — four residual temporal blocks, dilations [1, 2, 4, 8],
  channels [32, 32, 64, 64], weight-norm + dropout + ReLU, strictly causal
- `PINNHead` — two-layer MLP with tanh output, physiologically scaled to the
  Jansen-Rit state space, 0.1-gain final layer for stable initialisation
- `HybridForecaster` — shared encoder + three parallel heads
  (classifier, horizon regressor, PINN state). Total: 72,554 parameters.
- `jr_rhs_torch` — batched, autograd-enabled Jansen-Rit RHS for the physics
  loss term

### `app.core.training`
Bootstrap trainer. On first boot (no checkpoint on disk), synthesises a mini
dataset of 24 recordings, trains the hybrid model for 6 epochs with the
composite four-term loss (cross-entropy + Huber + normalised physics residual +
reconstruction MSE), and saves the resulting weights. Subsequent boots just
load the cached checkpoint.

### `app.core.inference`
Thin runtime wrapper around the trained model. Z-scores each window, runs a
single forward pass (~5–50 ms on CPU), and returns:
- Three-class softmax probabilities and confidence
- Seconds-to-seizure horizon
- Six-dimensional inferred Jansen-Rit state at every timestep
- PINN-decoded EEG reconstruction (y1 − y2)

### `app.core.patients`
Catalogue of six synthetic patient recordings with distinct regime schedules.
Generated lazily on first startup, cached to disk as compressed `.npz`, loaded
on demand.

### `app.api.routes`
REST and WebSocket endpoints:
- `GET /api/health`, `GET /api/system`
- `GET /api/patients` — list recordings
- `GET /api/patients/{pid}` — metadata
- `GET /api/patients/{pid}/signal` — raw samples
- `POST /api/infer/window` — one-off window inference
- `GET /api/infer/patient/{pid}/window/{i}` — indexed inference
- `GET /api/infer/patient/{pid}/summary` — full recording summary
- `GET /api/metrics` — pre-computed test-set metrics (hybrid + baseline)
- `WS /ws/stream/{pid}` — streaming window-by-window inference

### `app.main`
FastAPI app factory. Mounts routers, enables CORS, and serves the Vite-built
frontend from `/` (with SPA fallback routing).

## Frontend

React 18 + TypeScript + Vite + Tailwind. Key modules:
- `src/lib/store.ts` — Zustand global state (patients list, selected pid,
  streaming frame, playback state, metrics)
- `src/lib/api.ts` — typed REST + WebSocket client
- `src/hooks/useStream.ts` — opens the WebSocket, dispatches inbound frames
  to the store, syncs playback commands outbound
- `src/components/TopBar.tsx` — connection status, latency, patient ID
- `src/components/PatientSelector.tsx` — recording list
- `src/components/StateIndicator.tsx` — large state badge + probability bars
- `src/components/EEGWaveform.tsx` — canvas-based scrolling scope with
  dual-trace rendering (observed EEG + PINN reconstruction) at 128 Hz
- `src/components/LatentStatePanel.tsx` — 2×3 grid of per-component Jansen-Rit
  state sparklines
- `src/components/Timeline.tsx` — recording-wide regime schedule with cursor
- `src/components/Controls.tsx` — play/pause, scrub, speed selector
- `src/components/MetricsPanel.tsx` — test-set KPIs, confusion matrix,
  hybrid-vs-baseline ablation

## Dataflow for a live playback session

1. Client loads `/` → SPA bundle served
2. Client calls `GET /api/patients` and `GET /api/metrics` on mount
3. Client selects a patient → opens `WS /ws/stream/{pid}`
4. Server sends one `{type: "meta"}` message with the schedule and total windows
5. Server enters a loop: for each window (4 s at 128 Hz = 512 samples,
   stride 1 s = 128 samples), run the hybrid model forward and push a
   `{type: "frame"}` message with the predicted class, confidence, inferred
   state, reconstruction, and ground-truth label
6. Client ingests frames into a rolling 10-second buffer and repaints the
   canvas at display refresh rate (60 fps via `requestAnimationFrame`)
7. Client can send `{cmd: "pause" | "resume" | "seek" | "speed"}` to control
   the server-side playback rate (1×–32× real-time)

## Deployment

The entire application is a single Docker image. The multi-stage Dockerfile:
1. Builds the frontend bundle with Node 20
2. Installs CPU-only PyTorch and backend dependencies on Python 3.11-slim
3. Copies the bundle into `/app/frontend/dist`, from where FastAPI serves it

Target platforms include Railway (via `railway.toml`), Render (via
`render.yaml`), Fly.io (via `fly.toml`), or any docker-compose host.
