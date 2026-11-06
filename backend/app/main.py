"""NeuroSentry Clinical Console — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import settings
from .api.middleware import RequestTimingMiddleware
from .api.routes import health, patients, inference, metrics, stream
from .core.logging_config import configure_logging, get_logger

configure_logging("INFO")
log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: bootstrap patient store + inference engine."""
    log.info("starting NeuroSentry Clinical Console v%s", __version__)
    # Patient store generates recordings on first run
    from .core.patients import get_patient_store
    get_patient_store()
    # Inference engine loads checkpoint (or trains one)
    from .core.inference import get_engine
    get_engine()
    log.info("ready — listening on %s:%s", settings.host, settings.port)
    yield
    log.info("shutdown")


app = FastAPI(
    title="NeuroSentry Clinical Console",
    description=(
        "Real-time clinical dashboard for the NeuroSentry physics-informed deep "
        "learning seizure prediction system."
    ),
    version=__version__,
    lifespan=lifespan,
)


app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-ms"],
)


# API routes
app.include_router(health.router)
app.include_router(patients.router)
app.include_router(inference.router)
app.include_router(metrics.router)
app.include_router(stream.router)


# -------------------------- Static frontend (SPA) --------------------------

_frontend_dist = settings.frontend_dist


def _mount_frontend() -> None:
    if not _frontend_dist.exists():
        # Frontend not built yet; add a friendly placeholder
        @app.get("/")
        def _placeholder() -> JSONResponse:
            return JSONResponse({
                "message": "NeuroSentry Clinical Console API is running.",
                "docs": "/docs",
                "note": (
                    "Frontend bundle not found at " + str(_frontend_dist) +
                    ". Build it with `cd frontend && npm run build` or run the "
                    "dev server (`npm run dev`) separately."
                ),
            })
        return

    # Mount bundled assets
    app.mount("/assets",
              StaticFiles(directory=_frontend_dist / "assets"),
              name="assets")

    # Serve favicon and other root-level static files explicitly
    for extra in ("favicon.svg", "favicon.ico", "robots.txt"):
        f = _frontend_dist / extra
        if f.exists():
            # Need to bind to the current value, hence a factory
            def _factory(path: Path, name: str):
                async def _serve() -> FileResponse:
                    return FileResponse(path)
                _serve.__name__ = f"serve_{name}"
                return _serve
            app.add_api_route(f"/{extra}", _factory(f, extra), methods=["GET"])

    @app.get("/")
    async def root_index() -> FileResponse:
        return FileResponse(_frontend_dist / "index.html")

    # Catch-all for SPA client-side routing (must be AFTER /api and /ws)
    @app.get("/{full_path:path}")
    async def spa_catchall(full_path: str) -> FileResponse:
        target = _frontend_dist / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(_frontend_dist / "index.html")


_mount_frontend()
