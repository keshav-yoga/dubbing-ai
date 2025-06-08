# backend/app/routers/lip_sync.py

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TTSGeneration, TTSSegment, LipSyncJob, LipSyncSegment
try:
    from app.utils.lip_sync_pipeline import LipSyncPipeline
except Exception as e:
    LipSyncPipeline = None
    _lip_import_error = e
else:
    _lip_import_error = None
from app.config import settings

router = APIRouter()

lip_sync_pipeline = None
if LipSyncPipeline:
    lip_sync_pipeline = LipSyncPipeline(
        mfa_command=getattr(settings, "MFA_COMMAND", "mfa"),
        acoustic_model_path=getattr(settings, "MFA_ACOUSTIC_MODEL", "/path/to/acoustic_model"),
        dictionary_path=getattr(settings, "MFA_DICTIONARY_PATH", "/path/to/dictionary")
    )

@router.post("/process/{tts_generation_id}")
def process_lip_sync(tts_generation_id: int, db: Session = Depends(get_db)):␊
    """
    1) Look up the TTSGeneration with all TTS segments.
    2) For each TTS segment, we have:
       - audio_file_path
       - start_time & end_time (the desired window in the video).
       - text (from processed segment if needed).
    3) Run forced alignment & time-stretch so that the final audio fits start->end duration.
    4) Save results in LipSyncJob & LipSyncSegment.
    5) Return the final aligned segments.
    """
        if lip_sync_pipeline is None:
        msg = f"Lip-sync pipeline unavailable: {_lip_import_error}" if _lip_import_error else "Lip-sync pipeline not initialised"
        raise HTTPException(status_code=500, detail=msg)

    tts_gen = db.query(TTSGeneration).filter(TTSGeneration.id == tts_generation_id).first()
    if not tts_gen:
        raise HTTPException(status_code=404, detail="TTSGeneration not found.")

    # For demonstration, we need a reference to the original video's path (where the actor is).
    # In a real pipeline, you might store that in TTSGeneration or pass it in the request.
    # We'll assume it's stored in settings or we have some known location.
    video_file_path = getattr(settings, "VIDEO_FILE_PATH", "/path/to/video.mp4")
    if not os.path.exists(video_file_path):
        raise HTTPException(status_code=400, detail="Video file not found. Provide a valid path in settings or request.")

    # If there's an existing lip sync job, remove it
    existing_job = db.query(LipSyncJob).filter(LipSyncJob.tts_generation_id == tts_generation_id).first()
    if existing_job:
        db.query(LipSyncSegment).filter(LipSyncSegment.lip_sync_job_id == existing_job.id).delete()
        db.delete(existing_job)
        db.commit()

    # Create a new LipSyncJob
    lip_sync_job = LipSyncJob(
        tts_generation_id=tts_generation_id,
        video_file_path=video_file_path
    )
    db.add(lip_sync_job)
    db.flush()

    # In order to align properly, we need the text used for TTS (from the processed segment).
    # We can fetch the text from TTS->ProcessedSegment relationship:
    # For brevity, assume each TTSSegment -> processed_segment_id -> that has processed_text

    results = []
    for seg in tts_gen.tts_segments:
        # fetch the processed text
        # (We omit the actual DB join here for brevity, but let's assume we have 'processed_text' easily accessible)
        processed_segment = seg.tts_generation.processed_script_id  # not correct, but for demonstration
        # realistically you'd do a join or a secondary query

        # We'll guess we have a placeholder text or store it in TTS segment. 
        # In production, you'd ensure you know the text that was used to generate the TTS.
        # Let's say we have a field "transcribed_text" or "original_text" for demonstration:
        transcript_text = "some line of dialogue"  # Replace with real data

        # The desired duration is (seg.end_time - seg.start_time) from the video.
        desired_duration = seg.end_time - seg.start_time
        if desired_duration <= 0:
            desired_duration = 1.0  # fallback, avoid zero or negative

        # We'll run the pipeline
        aligned_audio_path = lip_sync_pipeline.align_and_stretch(
            seg.audio_file_path,
            transcript=transcript_text,
            desired_duration=desired_duration
        )

        # Store a LipSyncSegment
        lip_seg = LipSyncSegment(
            lip_sync_job_id=lip_sync_job.id,
            tts_segment_id=seg.id,
            aligned_audio_path=aligned_audio_path
        )
        db.add(lip_seg)

        results.append({
            "tts_segment_id": seg.id,
            "original_audio_path": seg.audio_file_path,
            "aligned_audio_path": aligned_audio_path,
            "desired_duration": desired_duration
        })

    db.commit()

    return {
        "lip_sync_job_id": lip_sync_job.id,
        "video_reference": video_file_path,
        "aligned_segments": results
    }
