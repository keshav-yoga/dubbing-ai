# backend/app/routers/mixing.py

import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LipSyncJob, LipSyncSegment, AudioMixJob, AudioMixSegment
from app.utils.mix_pipeline import MixPipeline
from app.config import settings

router = APIRouter()

mix_pipeline = MixPipeline(
    target_lufs=getattr(settings, "MIX_TARGET_LUFS", -23.0)
)

@router.post("/process/{lip_sync_job_id}")
def mix_audio(
    lip_sync_job_id: int,
    background_audio_path: str = None,  # If user wants to override
    background_volume_db: float = 0.0,
    dialogue_volume_db: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    1) Find the LipSyncJob containing the aligned audio segments.
    2) Use the original background audio track or a user-provided track.
    3) Overlay the aligned segments at the correct time (in ms).
    4) Apply volume adjustments & loudness normalization.
    5) Store result in AudioMixJob & AudioMixSegment
    6) Return the final path
    """
    lip_sync_job = db.query(LipSyncJob).filter(LipSyncJob.id == lip_sync_job_id).first()
    if not lip_sync_job:
        raise HTTPException(status_code=404, detail="LipSyncJob not found.")

    # If no background audio path is provided, we might retrieve from the film's original track or a stored reference
    if not background_audio_path:
        # Possibly stored in lip_sync_job or elsewhere in your DB
        # We'll assume you have 'original_audio_path' in settings or from the video
        # For demonstration, let's just see if we have a fallback:
        background_audio_path = getattr(settings, "ORIGINAL_BG_AUDIO_PATH", None)

    if not background_audio_path or not os.path.isfile(background_audio_path):
        raise HTTPException(status_code=400, detail="No valid background audio found.")

    # If there's an existing AudioMixJob, remove it
    existing_mix = db.query(AudioMixJob).filter(
        AudioMixJob.lip_sync_job_id == lip_sync_job_id
    ).first()
    if existing_mix:
        db.query(AudioMixSegment).filter(AudioMixSegment.audio_mix_job_id == existing_mix.id).delete()
        db.delete(existing_mix)
        db.commit()

    new_mix = AudioMixJob(
        lip_sync_job_id=lip_sync_job_id,
        original_audio_path=background_audio_path
    )
    db.add(new_mix)
    db.flush()

    # Gather the aligned segments
    aligned_segments = db.query(LipSyncSegment).filter(LipSyncSegment.lip_sync_job_id == lip_sync_job_id).all()
    if not aligned_segments:
        raise HTTPException(status_code=400, detail="No aligned segments found for this LipSyncJob.")

    # We'll assume each segment is to be placed at the segment's original start_time (in seconds).
    # Convert to milliseconds for pydub overlay.
    dialogue_paths = []
    dialogue_starts = []

    for seg in aligned_segments:
        # We must retrieve the original start_time from the TTS segment or another reference
        # For demonstration, let's assume we have a method to get the start_time in ms:
        # e.g. if TTS segment or lip sync step stored it
        # If we only have the difference, let's guess we stored it as "start_time" in lip_sync job or the TTS segment
        # We'll just pretend we have a placeholder method here:

        # In practice, you'd join with TTS segment or the original transcription
        # to find the correct start_time. We'll assume  seg.tts_segment.start_time is in seconds:
        from app.models import TTSSegment
        tts_seg = db.query(TTSSegment).filter(TTSSegment.id == seg.tts_segment_id).first()
        if not tts_seg:
            continue

        start_ms = int(tts_seg.start_time * 1000.0)
        dialogue_paths.append(seg.aligned_audio_path)
        dialogue_starts.append(start_ms)

    # Create an output path
    local_folder = getattr(settings, "LOCAL_STORAGE_PATH", "/tmp")
    final_name = f"{uuid.uuid4()}_mixed.wav"
    output_path = os.path.join(local_folder, final_name)

    # Use mix_pipeline to combine background & dialogues
    final_track = mix_pipeline.combine_tracks(
        background_path=background_audio_path,
        dialogue_paths=dialogue_paths,
        dialogue_starts=dialogue_starts,
        output_path=output_path,
        background_volume_adj=background_volume_db,
        dialogue_volume_adj=dialogue_volume_db,
        apply_normalization=True
    )

    # Store result in AudioMixSegment
    mix_seg = AudioMixSegment(
        audio_mix_job_id=new_mix.id,
        output_audio_path=final_track,
        channel_info="Stereo"
    )
    db.add(mix_seg)
    db.commit()

    return {
        "audio_mix_job_id": new_mix.id,
        "final_track_path": final_track
    }
