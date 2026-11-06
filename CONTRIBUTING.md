# Contributing

Thanks for your interest in NeuroSentry Clinical Console. This document covers how to get set up locally, the code-style conventions the project follows, and how to submit changes.

## Getting set up

See `docs/DEPLOYMENT.md` for the full local-dev instructions. Short version:

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Running tests

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm run build   # type-check + production build
```

All 19 backend tests should pass in under 10 seconds on CPU.

## Code style

### Python

- Target Python 3.11+
- Prefer `from __future__ import annotations` in every new module
- Type-hint everything; `dict[str, Any]` style (no `typing.Dict`)
- Keep modules focused — one concern per file; the `app.core.*` layout is the model
- Dataclasses over plain dicts for structured data (see `JansenRitParams`)
- No print statements in production paths; use `print("[module] message")` only in startup/bootstrap code, never in per-request paths

### TypeScript / React

- Functional components only
- Strict mode enabled in `tsconfig.json`; no `any` without a justifying comment
- Co-locate component-specific types; shared types live in `src/lib/types.ts`
- Zustand store slices stay small and composable
- Prefer canvas rendering over SVG for anything that updates more than once per second

### Commit style

Conventional-commits with these scopes:
- `feat(core|api|ui|backend|frontend)` — new capability
- `fix(scope)` — bug fix
- `test(scope)` — test coverage
- `docs(scope)` — docs change only
- `chore(scope)` — build/config/tooling
- `refactor(scope)` — no behaviour change

Keep the summary line under 80 chars. Body is optional but welcome for non-trivial changes.

## Pull requests

1. Fork + branch from `main`
2. Make your changes with tests
3. `pytest` must pass; `npm run build` must succeed
4. Open a PR describing the change, the motivation, and (if UI) a screenshot
5. One of the maintainers reviews within a few days

## Reporting issues

Use the GitHub issue templates at `.github/ISSUE_TEMPLATE/`. Include:
- OS and Python / Node versions
- Minimal steps to reproduce
- What you expected vs what happened
- Relevant logs (`/tmp/server.log` if deployed, console output if local)
