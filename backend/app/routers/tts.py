# backend/app/routers/tts.py

import os
import uuid
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProcessedScript, ProcessedSegment, TTSGeneration, TTSSegment
from app.utils.tts_pipeline import TTSProcessor
from app.config import settings

router = APIRouter()

# Create a TTSProcessor instance with some local model paths or pass them from config
tts_processor = TTSProcessor(
    model_path=settings.COQUI_MODEL_PATH if hasattr(settings, "COQUI_MODEL_PATH") else None,
    vocoder_path=settings.COQUI_VOCODER_PATH if hasattr(settings, "COQUI_VOCODER_PATH") else None,
    use_gpu=True
)

@router.post("/generate/{processed_script_id}")
def generate_tts(
    processed_script_id: int,
    voice_name: str = "local_coqui_default",
    db: Session = Depends(get_db)
):
    """
    1) Look up the ProcessedScript (which has text segments).
    2) For each segment, generate TTS audio.
    3) Store TTS results in TTSGeneration & TTSSegment in DB.
    4) Return references to the audio files.
    """
    processed_script = db.query(ProcessedScript).filter(
        ProcessedScript.id == processed_script_id
    ).first()

    if not processed_script:
        raise HTTPException(status_code=404, detail="ProcessedScript not found.")

    segments = processed_script.processed_segments
    if not segments:
        raise HTTPException(status_code=400, detail="No processed segments found.")

    # Create a TTSGeneration record
    existing_generation = db.query(TTSGeneration).filter(
        TTSGeneration.processed_script_id == processed_script_id,
        TTSGeneration.voice_name == voice_name
    ).first()

    # Remove old data if re-generating
    if existing_generation:
        db.query(TTSSegment).filter(TTSSegment.tts_generation_id == existing_generation.id).delete()
        db.delete(existing_generation)
        db.commit()

    new_generation = TTSGeneration(
        processed_script_id=processed_script_id,
        voice_name=voice_name
    )
    db.add(new_generation)
    db.flush()

    output_info = []
    for seg in segments:
        # Build an output file path
        audio_name = f"{uuid.uuid4()}.wav"
        local_folder = settings.LOCAL_STORAGE_PATH if hasattr(settings, "LOCAL_STORAGE_PATH") else "/tmp"
        output_path = os.path.join(local_folder, audio_name)

        # Synthesize
        try:
            tts_processor.synthesize_text(
                text=seg.processed_text,
                output_path=output_path,
                voice_name=voice_name,
                speaker_label=seg.speaker_label
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

        # If you want, you can store audio on S3:
        # s3_url = upload_to_s3(output_path, "some-bucket", f"tts_segments/{audio_name}")
        # For brevity, we'll keep it local.

        # Record TTSSegment
        tts_segment = TTSSegment(
            tts_generation_id=new_generation.id,
            processed_segment_id=seg.id,
            start_time=seg.start_time,
            end_time=seg.end_time,
            speaker_label=seg.speaker_label,
            audio_file_path=output_path  # or s3_url if you upload to S3
        )
        db.add(tts_segment)

        output_info.append({
            "segment_id": seg.id,
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "speaker": seg.speaker_label,
            "audio_file_path": output_path
        })

    db.commit()

    return {
        "tts_generation_id": new_generation.id,
        "voice_name": voice_name,
        "segments": output_info
    }
