# Deployment

## Railway (one-click, recommended)

1. Push this repo to GitHub.
2. Go to <https://railway.app>, click **New Project** → **Deploy from GitHub repo**.
3. Pick `RaktimChandra/neurosentry-console`.
4. Railway auto-detects the `Dockerfile` and `railway.toml`.
5. Click **Generate Domain** under **Settings → Networking**.
6. First boot takes ~2 minutes while the model trains itself from scratch
   (one-time, cached to the attached volume after that).

That's it. No environment variables required; defaults work out of the box.

## Render

Click **New → Blueprint**, point at the repo, and Render reads `render.yaml`.
The 1 GB disk persists the bootstrapped checkpoint across restarts.

## Fly.io

```bash
fly launch --copy-config --name neurosentry-console --region sin
fly volumes create data --size 1
fly deploy
```

## Docker-compose (self-host)

```bash
docker-compose up --build -d
# Open http://localhost:8000
```

The two named volumes (`checkpoints`, `patient-data`) preserve the bootstrapped
state across container restarts so the 45-second cold start only happens once.

## Local development without Docker

Two terminals: FastAPI (hot reload) + Vite (HMR).

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                       # Opens http://localhost:5173
```

The Vite dev server proxies `/api` and `/ws` to `http://localhost:8000`.

## Environment variables

All settings override via `NEUROSENTRY_*` env vars. Common ones:

| Variable                        | Default   | Purpose                                     |
|---------------------------------|-----------|---------------------------------------------|
| `NEUROSENTRY_HOST`              | `0.0.0.0` | Bind host                                   |
| `NEUROSENTRY_PORT`              | `8000`    | Bind port (Railway/Render inject `$PORT`)   |
| `NEUROSENTRY_FS`                | `128`     | Sampling frequency (Hz)                     |
| `NEUROSENTRY_WINDOW_SEC`        | `4.0`     | Analysis window length                      |
| `NEUROSENTRY_STRIDE_SEC`        | `1.0`     | Sliding window stride                       |
| `NEUROSENTRY_EPOCHS`            | `6`       | Bootstrap training epochs                   |
| `NEUROSENTRY_N_RECORDINGS`      | `24`      | Bootstrap training recording count          |
| `NEUROSENTRY_LR`                | `5e-4`    | Bootstrap training learning rate            |

## Dropping in a real trained checkpoint

If you already have a `hybrid.pt` from the parent research repo, drop it into
`backend/checkpoints/hybrid.pt` before first boot. The inference engine will
load it instead of training a new one. The checkpoint format matches: the
training code saves `{"model_state": state_dict, "config": {...}}`.

## Health & monitoring

- Liveness: `GET /api/health` returns `{"status": "ok", "version": "1.0.0"}`
- System info: `GET /api/system` returns torch version, device, config
- The Dockerfile's HEALTHCHECK uses `/api/health` with a 120-second
  start-period so Railway/Render don't mark the container unhealthy during
  the cold-start model-training phase.
