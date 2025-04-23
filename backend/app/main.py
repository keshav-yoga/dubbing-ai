# backend/app/main.py
from fastapi import FastAPI
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import (
    upload, asr, script_processing,
    tts, lip_sync, mixing, final_output
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION
)

app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(asr.router, prefix="/api/asr", tags=["ASR"])
app.include_router(script_processing.router, prefix="/api/script_process", tags=["ScriptProcessing"])
app.include_router(tts.router, prefix="/api/tts", tags=["TTS"])
app.include_router(lip_sync.router, prefix="/api/lip_sync", tags=["LipSync"])
app.include_router(mixing.router, prefix="/api/mixing", tags=["AudioMixing"])
app.include_router(final_output.router, prefix="/api/final_output", tags=["FinalOutput"])

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "message": "Dubbing AI system is running."}
