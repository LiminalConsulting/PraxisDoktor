from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import SessionLocal
from .routers import admin, auth as auth_router, chat, dashboard, intake, processes
from .sync import sync_registry
from .ws import router as ws_router

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as db:
        await sync_registry(db)
    yield


app = FastAPI(title="PraxisDoktor", lifespan=lifespan)

# CORS for local dev — frontend on :5173, backend on :8080
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
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"ok": True, "env": _settings.environment}


@app.get("/")
async def root():
    return {
        "service": "PraxisDoktor",
        "ui": "http://localhost:5173 (run `bun run dev` in web/)",
        "health": "/health",
    }
