from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from . import jobs
from .config import get_settings
from .db import SessionLocal
from .intake.pipeline import run_intake_pipeline, run_intake_ocr
from .routers import admin, auth as auth_router, chat, dashboard, intake, processes, public
from .sync import sync_registry
from .ws import router as ws_router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as db:
        await sync_registry(db)
    jobs.register_handler("intake_pipeline", run_intake_pipeline)
    jobs.register_handler("intake_ocr", run_intake_ocr)
    await jobs.start()
    yield
    await jobs.stop()


app = FastAPI(title="PraxisDoktor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(dashboard.router)
app.include_router(processes.router)
app.include_router(chat.router)
app.include_router(intake.router)
app.include_router(admin.router)
app.include_router(public.router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"ok": True, "env": _settings.environment}


# --- Production: serve the built SvelteKit frontend ---
# In dev, the frontend runs separately on :5173. In prod, the installer copies
# the static build to ./web_build (relative to server/) and we serve it here.
_WEB_BUILD = Path(__file__).resolve().parents[2] / "web_build"

if _WEB_BUILD.exists():
    app.mount("/_app", StaticFiles(directory=_WEB_BUILD / "_app"), name="static_app")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # API/WS already handled by their routers since they're registered first.
        target = _WEB_BUILD / full_path
        if target.is_file():
            return FileResponse(target)
        index = _WEB_BUILD / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"detail": "frontend not built"}
else:
    @app.get("/")
    async def root():
        return {
            "service": "PraxisDoktor",
            "ui": "http://localhost:5173 (run `bun run dev` in web/)",
            "health": "/health",
        }
