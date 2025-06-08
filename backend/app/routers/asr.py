# backend/app/routers/asr.py

import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, UploadedFile, Transcription, TranscriptionSegment
try:
    from app.utils.asr_pipeline import ASRPipeline
except Exception as e:  # pragma: no cover - optional heavy deps
    ASRPipeline = None
    _asr_import_error = e
else:
    _asr_import_error = None

router = APIRouter()
asr_pipeline = ASRPipeline(use_gpu=True) if ASRPipeline else None  # lazy if deps missing

@router.post("/process/{project_id}")
def process_asr(project_id: int, db: Session = Depends(get_db)):␊
    """
    1. Fetch the Project & audio file (file_type="audio").
    2. Run the ASR pipeline (speaker diarization, language ID, transcription).
    3. Store the results in DB.
    4. Return the final JSON array of segments.
    """
      if asr_pipeline is None:
        msg = f"ASR pipeline unavailable: {_asr_import_error}" if _asr_import_error else "ASR pipeline not initialised"
        raise HTTPException(status_code=500, detail=msg)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the audio file. This assumes we've stored it as "file_type='audio'"
    audio_file = None
    for f in project.uploaded_files:
        if f.file_type == "audio":
            audio_file = f
            break

    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file found for this project.")

    # 1) Build the absolute local path for the audio
    local_path = audio_file.file_path
    if local_path.startswith("s3://"):
        # If it's on S3, we'd need to download it or stream it locally
        # We'll skip that for brevity; see the previous upload pipeline for example S3 usage.
        raise HTTPException(status_code=501, detail="Downloading from S3 not implemented here.")

    # 2) Run ASR pipeline
    segments_result = asr_pipeline.run_asr_pipeline(local_path)

    # 3) Store transcription in DB
    # If a transcription record already exists, we might overwrite or create a new one.
    existing_transcription = db.query(Transcription).filter(Transcription.project_id == project_id).first()
    if existing_transcription:
        # Remove old segments
        db.query(TranscriptionSegment).filter(TranscriptionSegment.transcription_id == existing_transcription.id).delete()
        db.delete(existing_transcription)
        db.commit()

    new_transcription = Transcription(project_id=project_id)
    db.add(new_transcription)
    db.flush()

    for seg in segments_result:
        segment_model = TranscriptionSegment(
            transcription_id=new_transcription.id,
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            speaker_label=seg["speaker"],
            language_detected=seg["language_detected"],
            text=seg["text"]
        )
        db.add(segment_model)

    db.commit()
    db.refresh(new_transcription)

    return {
        "project_id": project_id,
        "transcription_id": new_transcription.id,
        "segments": segments_result
    }
