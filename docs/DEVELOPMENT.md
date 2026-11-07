# Developer Guide

Day-to-day commands for working on the console.

## Quick commands

All the common operations have `make` targets. Run `make` with no arguments to see them:

```bash
make install        # install both backends' dependencies
make dev-backend    # FastAPI with auto-reload on :8000
make dev-frontend   # Vite dev server on :5173 (proxies to :8000)
make test           # run the backend pytest suite
make build          # produce a production frontend bundle
make docker-up      # bring up the full stack via docker-compose
make docker-down    # tear it down
make clean          # remove caches and build artefacts
```

## Project layout

```
neurosentry-console/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory + SPA mount
│   │   ├── config.py          # pydantic Settings
│   │   ├── core/              # Jansen-Rit sim, models, training, inference, cache
│   │   └── api/               # REST + WebSocket routes, middleware
│   ├── tests/                 # pytest suite (29/29 passing)
│   ├── checkpoints/           # populated on first boot (gitignored)
│   └── data/patients/         # populated on first boot (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # top-level layout
│   │   ├── main.tsx           # entry point + ErrorBoundary
│   │   ├── components/        # all UI pieces
│   │   ├── hooks/             # useStream, useLatencyBuffer
│   │   └── lib/               # types, api client, zustand store
│   └── dist/                  # built bundle (gitignored)
├── docs/                      # architecture, deployment, API, model
├── .github/
│   ├── workflows/ci.yml       # pytest + vite build + docker build
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── Dockerfile                 # multi-stage: node build → python runtime
├── docker-compose.yml         # single-service compose for self-hosting
├── railway.toml               # Railway deploy config
├── render.yaml                # Render blueprint
├── fly.toml                   # Fly.io config
└── Makefile
```

## Adding a new API endpoint

1. Create a route module in `backend/app/api/routes/` (e.g. `annotations.py`)
2. Define `router = APIRouter(prefix="/api/annotations", tags=["annotations"])`
3. Add handlers with Pydantic request/response models for schema documentation
4. Register the router in `backend/app/main.py` with `app.include_router(...)`
5. Add tests in `backend/tests/test_annotations.py`
6. Document the endpoint in `docs/API.md`

## Adding a new UI panel

1. Create the component in `frontend/src/components/YourPanel.tsx`
2. Wrap its outer element in `className="panel"` for consistent styling
3. Use `panel-header` for the title row
4. Subscribe to store state with `useApp((s) => s.whatever)` — select only what you need to minimise re-renders
5. For canvas visualisations, follow the pattern in `EEGWaveform.tsx` (DPR-scaled canvas, `requestAnimationFrame` render loop)
6. Mount it in `App.tsx` either in the sidebar or main workspace column

## Styling conventions

- All colours live in `tailwind.config.js` under the `ink`, `signal`, and `trace` palettes
- Prefer Tailwind utility classes over custom CSS; drop to CSS only for complex selectors (scrollbars, pseudo-elements)
- Hospital-monitor dark theme — no light mode planned; backgrounds are always dark
- Animated signals use `animate-pulse` (interictal/calm) or `animate-pulseFast` (critical/ictal)

## Debugging the stream

If the WebSocket keeps disconnecting:
- Check the browser Network tab → WS section for the close code
- Inspect server logs for the matching `X-Request-ID`
- `curl http://localhost:8000/api/system` to check cache stats and uptime
- `/api/infer/patient/<pid>/window/<i>` to isolate inference problems from streaming problems

## Running a single test

```bash
cd backend
.venv/bin/python -m pytest tests/test_cache.py -v
.venv/bin/python -m pytest tests/test_models.py::test_hybrid_backprop -v
```

## Rebuilding after a model change

If you change `backend/app/core/models.py`, the existing checkpoint may no longer load. Delete it to force a rebuild:

```bash
rm backend/checkpoints/hybrid.pt
# then restart the server — it'll bootstrap a fresh checkpoint
```

## Environment variables

See `backend/.env.example`. All `NEUROSENTRY_*` prefixed vars override pydantic Settings values.
