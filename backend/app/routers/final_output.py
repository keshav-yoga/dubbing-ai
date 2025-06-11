# backend/app/routers/final_output.py␊
␊
import os␊
import uuid␊
from typing import List, Optional␊
from fastapi import APIRouter, Depends, HTTPException␊
from sqlalchemy.orm import Session␊
␊
from app.database import get_db␊
from app.models import (␊
    AudioMixJob, AudioMixSegment,␊
    FinalOutputJob, SubtitleFile,␊
    ProcessedScript, ProcessedSegment␊
)␊
try:␊
    from app.utils.final_output_pipeline import FinalOutputPipeline␊
except Exception as e:␊
    FinalOutputPipeline = None␊
    _final_import_error = e␊
else:␊
    _final_import_error = None␊
from app.config import settings␊
␊
router = APIRouter()
final_pipeline = FinalOutputPipeline() if FinalOutputPipeline else None␊
␊
@router.post("/generate/{audio_mix_job_id}")␊
def generate_final_output(
    audio_mix_job_id: int,␊
    include_subtitles: bool = True,␊
    subtitle_language_codes: Optional[List[str]] = None,␊
    db: Session = Depends(get_db)␊
):
    """␊
    1) Look up AudioMixJob -> get final mixed audio track␊
    2) Mux it with the original video␊
    3) Optionally generate subtitles (SRT) for specified language(s)␊
    4) Return final video path + any subtitle paths␊
    """␊
    if final_pipeline is None:
        msg = f"Final output pipeline unavailable: {_final_import_error}" if _final_import_error else "Final output pipeline not initialised"␊
        raise HTTPException(status_code=500, detail=msg)␊
␊
    mix_job = db.query(AudioMixJob).filter(AudioMixJob.id == audio_mix_job_id).first()␊
    if not mix_job:␊
        raise HTTPException(status_code=404, detail="AudioMixJob not found.")␊
␊
    # we expect one final output track in AudioMixSegment␊
    mix_segments = mix_job.audio_mix_segments␊
    if not mix_segments:␊
        raise HTTPException(status_code=400, detail="No mixed audio found for this job.")␊
␊
    final_audio_path = mix_segments[-1].output_audio_path␊
    if not final_audio_path or not os.path.isfile(final_audio_path):␊
        raise HTTPException(status_code=400, detail="Mixed audio path invalid or not found.")␊
␊
    # The original video can come from the lip_sync reference or some stored path␊
    # But let's say we have it in settings or we store it in AudioMixJob␊
    # For demonstration, let's assume we stored it in the lip_sync_job or a prior pipeline␊
    video_path = getattr(settings, "ORIGINAL_VIDEO_PATH", None)␊
    if not video_path or not os.path.isfile(video_path):␊
        # fallback to the mix_job referencing lip_sync_job -> ...␊
        # but let's keep it simple for demonstration␊
        raise HTTPException(status_code=400, detail="Could not locate the original video file.")␊
␊
    # If there's an existing final output job for this mix, remove it␊
    existing_final = db.query(FinalOutputJob).filter(FinalOutputJob.audio_mix_job_id == audio_mix_job_id).first()␊
    if existing_final:␊
        db.query(SubtitleFile).filter(SubtitleFile.final_output_job_id == existing_final.id).delete()␊
        db.delete(existing_final)␊
        db.commit()␊
␊
    final_output_job = FinalOutputJob(␊
        audio_mix_job_id=audio_mix_job_id,␊
        video_file_path=video_path␊
    )␊
    db.add(final_output_job)␊
    db.flush()␊
␊
    # Build a path for the final video␊
    local_folder = settings.LOCAL_STORAGE_PATH if hasattr(settings, "LOCAL_STORAGE_PATH") else "/tmp"␊
    final_video_name = f"{uuid.uuid4()}_final.mp4"␊
    final_video_path = os.path.join(local_folder, final_video_name)␊
␊
    # 1) Mux final audio with original video␊
    try:␊
        final_pipeline.mux_audio_video(video_path, final_audio_path, final_video_path)␊
    except Exception as e:␊
        raise HTTPException(status_code=500, detail=f"FFmpeg mux error: {str(e)}")␊
␊
    final_output_job.final_video_path = final_video_path␊
    db.add(final_output_job)␊
    db.commit()␊
    db.refresh(final_output_job)␊
␊
    # 2) Optionally generate subtitles␊
    subtitle_paths = []␊
    if include_subtitles and subtitle_language_codes:␊
        for lang_code in subtitle_language_codes:␊
            # We need to gather segments from the relevant processed script -> processed segments␊
            # ... or from TTS segments. For demonstration, let's do processed script approach:␊
            # We'll assume there's a single processed script for the entire film in the requested lang␊
            # You might do a more robust approach if you store multiple scripts␊
            pscript = db.query(ProcessedScript).filter(␊
                ProcessedScript.project_id == mix_job.lip_sync_job_id,␊
                ProcessedScript.target_language == lang_code␊
            ).first()␊
            # The above is hypothetical: you might store a direct reference from lip_sync -> processed_script␊
            # or something else. We'll keep it conceptual.␊
␊
            if not pscript:␊
                continue␊
␊
            # Convert segments to [start_time, end_time, text]␊
            # We'll assume each ProcessedSegment has start_time, end_time, and processed_text␊
            segments_data = []␊
            for pseg in pscript.processed_segments:␊
                segments_data.append({␊
                    "start_time": pseg.start_time,␊
                    "end_time": pseg.end_time,␊
                    "text": pseg.processed_text␊
                })␊
␊
            sub_file_ext = "srt"␊
            subtitle_file_name = f"{uuid.uuid4()}.{sub_file_ext}"␊
            subtitle_path = os.path.join(local_folder, subtitle_file_name)␊
            final_pipeline.create_subtitle_file(segments_data, subtitle_path, fmt=sub_file_ext)␊
␊
            # Store in DB␊
            subtitle_db = SubtitleFile(␊
                final_output_job_id=final_output_job.id,␊
                language_code=lang_code,␊
                subtitle_format=sub_file_ext,␊
                file_path=subtitle_path␊
            )␊
            db.add(subtitle_db)␊
            db.commit()␊
            subtitle_paths.append(subtitle_path)␊
␊
    db.refresh(final_output_job)␊
␊
    return {␊
        "final_output_job_id": final_output_job.id,␊
        "final_video_path": final_video_path,␊
        "subtitle_files": subtitle_paths␊
    }␊
