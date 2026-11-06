# NeuroSentry Clinical Console

Real-time clinical visualization dashboard for the NeuroSentry physics-informed deep learning seizure prediction system. Loads EEG recordings, streams them through a trained hybrid TCN + PINN model, and renders per-window state classification, 6-D Jansen-Rit latent state, and PINN-decoded reconstruction in an interactive hospital-monitor style interface.

## Live Demo

Dashboard: [https://neurosentry-console.up.railway.app](https://neurosentry-console.up.railway.app)
Source model: [RaktimChandra/neurosentry](https://github.com/RaktimChandra/neurosentry)

## What it does

The console is the clinical-facing counterpart to the research model in the parent neurosentry repo. Where the research code produces checkpoints and metric JSONs, this console turns those into something a clinician or non-technical reviewer can actually interact with:

- Plays back any held-out EEG recording at adjustable speed (1x to 32x)
- Runs the trained hybrid model on each 4-second window as it scrolls past
- Shows a live three-state classification banner (interictal / preictal / ictal) with confidence
- Visualizes the model's inferred six-dimensional Jansen-Rit neural-mass state at every timestep
- Overlays the PINN-decoded reconstruction on the observed signal — the key interpretability moment
- Displays the test-set metrics (97.42% accuracy, 0.968 macro-F1) and a live-updating confusion matrix
- Supports scrubbing, pausing, playback speed control, and recording switching
- Renders in a dark hospital-monitor aesthetic optimized for projector display

## Architecture

Single FastAPI service that embeds the inference pipeline and serves the pre-built React frontend from `/`. One Docker image, one deploy target.

- **Backend** (Python 3.11+, FastAPI, PyTorch): loads checkpoint, exposes REST API + WebSocket streaming
- **Frontend** (React 18 + TypeScript + Vite, D3, Tailwind): client-side state, WebSocket client, canvas-based waveform renderer
- **Deploy**: Railway, Render, or Fly.io via Dockerfile. Local dev via docker-compose.

## Quick start (local)

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd frontend
npm install
npm run dev

# Open http://localhost:5173
```

Or docker-compose:

```bash
docker-compose up --build
# Open http://localhost:8000
```

## Features

- Scrolling EEG waveform at hospital-monitor fidelity, 128 Hz rendering
- Real-time state classification with confidence meter and sustained-alarm logic
- 6-D Jansen-Rit latent state animated in a small-multiples panel
- PINN reconstruction overlay with configurable transparency
- Recording selector, playback speed (1x/2x/4x/8x/16x/32x), scrub bar, pause
- Confusion matrix, ROC curves, per-class metrics panel
- Dark theme, projector-friendly, keyboard shortcuts
- Mobile-responsive for tablet demos

## Attribution

Authors: Raktim Chandra (RA2311033010038), Juhi Hai (RA2311033010027). Guide: Dr. Amudha S., Department of Computational Intelligence, SRM Institute of Science and Technology.

This console was built as a visualization layer for the research code in [RaktimChandra/neurosentry](https://github.com/RaktimChandra/neurosentry). See that repo for the model training code, methodology, IEEE paper, and SRM project report.

## License

MIT.
