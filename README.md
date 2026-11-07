# NeuroSentry Clinical Console

<p align="left">
  <img alt="CI" src="https://github.com/RaktimChandra/neurosentry-console/actions/workflows/ci.yml/badge.svg" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue" />
  <img alt="React" src="https://img.shields.io/badge/react-18-61dafb" />
  <img alt="FastAPI" src="https://img.shields.io/badge/fastapi-0.115-009688" />
  <img alt="PyTorch" src="https://img.shields.io/badge/pytorch-2.14-ee4c2c" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green" />
</p>

Real-time clinical visualization dashboard for the **NeuroSentry** physics-informed deep learning seizure prediction system. Loads EEG recordings, streams them through a trained hybrid TCN + PINN model, and renders per-window state classification, 6-D Jansen-Rit latent state, and PINN-decoded reconstruction in an interactive hospital-monitor style interface.

**Live demo:** https://neurosentry-console.onrender.com
**Research repository:** [RaktimChandra/neurosentry](https://github.com/RaktimChandra/neurosentry)

---

## What it does

The console is the clinical-facing counterpart to the research model in the parent `neurosentry` repo. Where the research code produces checkpoints and metric JSONs, this console turns those into something a clinician or non-technical reviewer can actually interact with:

- Plays back any held-out EEG recording at adjustable speed (1x to 32x)
- Runs the trained hybrid model on each 4-second window as it scrolls past
- Shows a live three-state classification banner (interictal / preictal / ictal) with confidence and probability bars
- Visualizes the model's inferred six-dimensional Jansen-Rit neural-mass state at every timestep
- Overlays the PINN-decoded reconstruction on the observed signal — the key interpretability moment
- Displays the test-set metrics (97.42% accuracy, 0.968 macro-F1) with ROC curves and a live-updating confusion matrix
- Supports scrubbing, pausing, playback speed control, recording switching
- Tracks running session accuracy, inference latency sparkline, and warning horizon countdown
- Dark hospital-monitor aesthetic, projector-friendly, keyboard shortcuts (space / 1–6 / arrows / ?)

## Architecture

Single FastAPI service that embeds the inference pipeline and serves the pre-built React frontend from `/`. One Docker image, one deploy target.

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
                 └───────────────────────────────────────────────┘
```

- **Backend** — FastAPI, PyTorch (CPU), Pydantic. Loads a trained `hybrid.pt`, serves REST + WebSocket.
- **Frontend** — React 18 + TypeScript + Vite + Tailwind. Canvas-based scrolling EEG scope at 128 Hz. Zustand state. D3 helpers.
- **Deploy** — single multi-stage Docker image. Compatible with Railway, Render, Fly.io, or any docker-compose host.

See `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/MODEL.md`, and `docs/DEVELOPMENT.md` for details.

## Quick start — local

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd frontend
npm install
npm run dev

# Open http://localhost:5173
```

Or via docker-compose:

```bash
docker-compose up --build
# Open http://localhost:8000
```

## Features

- Scrolling EEG waveform at hospital-monitor fidelity, 128 Hz rendering, real + reconstruction overlay
- Live three-state classification with sustained-alarm logic and warning horizon
- 6-component Jansen-Rit latent state animated in a small-multiples sparkline panel
- Hybrid-vs-baseline ablation panel using precomputed research test-set metrics
- One-vs-rest ROC curves per class
- Recording selector with regime schedule preview
- Playback speed 1x / 2x / 4x / 8x / 16x / 32x, scrub bar, pause/resume
- Keyboard shortcuts (space, 1-6, ←→, ?)
- Running session accuracy, inference latency sparkline
- Dark hospital-monitor aesthetic, projector-friendly
- Error boundary with graceful fallback
- Mobile-responsive layout

## Testing

```bash
cd backend && python -m pytest tests/ -v    # 29/29 passing in ~5s
cd frontend && npm run build                 # type-check + production bundle
```

## Deployment

See `docs/DEPLOYMENT.md`. One-click targets:

- **Render** — this project's `render.yaml` provisions a Docker web service with a 1 GB disk for persisted checkpoints
- **Railway** — `railway.toml` provisions a service with the Dockerfile
- **Fly.io** — `fly.toml` for the Singapore region
- **docker-compose** — single-command self-host

All deploys ship a pretrained `hybrid.pt` inside the image, so first boot is instant — no cold-start training needed.

## Project layout

```
neurosentry-console/
├── backend/          # FastAPI + PyTorch service
│   ├── app/
│   │   ├── core/     # Jansen-Rit sim, hybrid model, training, inference, cache
│   │   └── api/      # REST + WebSocket routes, middleware
│   ├── tests/        # 29 pytest tests
│   ├── checkpoints/  # shipped pretrained hybrid.pt
│   └── data/         # shipped synthesized patient recordings
├── frontend/         # React 18 + TypeScript + Vite
│   └── src/
│       ├── components/  # TopBar, StateIndicator, EEGWaveform, LatentStatePanel, …
│       ├── hooks/       # useStream, useLatencyBuffer
│       └── lib/         # types, api client, zustand store
├── docs/             # ARCHITECTURE, API, MODEL, DEVELOPMENT, DEPLOYMENT
├── .github/          # CI workflow, issue templates, dependabot
├── Dockerfile        # multi-stage: node build → python runtime
├── docker-compose.yml
├── railway.toml
├── render.yaml
├── fly.toml
└── Makefile
```

## Contributing

See `CONTRIBUTING.md` for coding conventions, PR workflow, and commit style.
Bug reports and feature requests use the GitHub issue templates.

## Attribution

Authors: **Raktim Chandra** (RA2311033010038), **Juhi Hai** (RA2311033010027).
Guide: Dr. Amudha S., Department of Computational Intelligence, SRM Institute of Science and Technology.

This console is a visualization layer for the research code in [RaktimChandra/neurosentry](https://github.com/RaktimChandra/neurosentry). See that repo for the model training code, methodology, IEEE paper, and SRM project report.

## License

[MIT](LICENSE).
