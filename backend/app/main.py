"""Main entrypoint for the FastAPI backend of **dubbing‑ai**.
This file wires together the database, middleware, and individual
feature routers (upload, ASR, TTS, etc.).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import (
    upload,
    asr,
    script_processing,
    tts,
    lip_sync,
    mixing,
    final_output,
)

# ───────────────────────────── Database ──────────────────────────────
# Create tables if they don't exist. In production you may want
# migrations (e.g. Alembic) instead of `create_all`.
Base.metadata.create_all(bind=engine)

# ───────────────────────────── FastAPI App ────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
)

# ───────────────────────────── CORS setup ─────────────────────────────
# Adjust the origins list as needed for dev/prod front‑end URLs
origins = ["http://localhost:3000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────── Routers ────────────────────────────────
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(asr.router, prefix="/api/asr", tags=["ASR"])
app.include_router(script_processing.router, prefix="/api/script_process", tags=["ScriptProcessing"])
app.include_router(tts.router, prefix="/api/tts", tags=["TTS"])
app.include_router(lip_sync.router, prefix="/api/lip_sync", tags=["LipSync"])
app.include_router(mixing.router, prefix="/api/mixing", tags=["AudioMixing"])
app.include_router(final_output.router, prefix="/api/final_output", tags=["FinalOutput"])

# ───────────────────────────── Healthcheck ────────────────────────────
@app.get("/healthcheck", tags=["Health"])
def healthcheck():
    """Simple health‑check endpoint for container orchestration probes."""
    return {"status": "ok", "message": "Dubbing AI system is running."}
