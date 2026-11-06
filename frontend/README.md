# NeuroSentry Console — Frontend

React 18 + TypeScript + Vite + Tailwind.

## Development

```bash
npm install
npm run dev    # → http://localhost:5173
```

The dev server proxies `/api` and `/ws` to `http://localhost:8000`, so run the
backend side-by-side:

```bash
cd ../backend
uvicorn app.main:app --reload --port 8000
```

## Build

```bash
npm run build
```

The production bundle lands in `dist/`. The backend serves it from `/` when
`frontend/dist/` exists.

## Structure

```
src/
  main.tsx          # entry point
  App.tsx           # top-level layout, keyboard shortcuts, data fetching
  components/       # all UI pieces
  hooks/            # useStream — WebSocket client
  lib/
    types.ts        # shared TypeScript types
    api.ts          # REST/WS client helpers
    store.ts        # Zustand global state
  styles/
    globals.css     # Tailwind directives + panel theme
```

## Styling

Hospital-monitor-inspired dark theme:
- Backgrounds use radial-gradient navy with subtle brand-accent glow
- Signal states colour-coded: `#22d3a0` interictal, `#ffb020` preictal,
  `#ff3360` ictal — with matching glow shadows on active badges
- Typography: Inter for UI, JetBrains Mono for numeric readouts
- EEG scope is Canvas-rendered at device-pixel-ratio for sharpness

All colours and animation timings live in `tailwind.config.js` and
`src/styles/globals.css`.
