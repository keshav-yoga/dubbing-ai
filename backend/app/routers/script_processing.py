# backend/app/routers/script_processing.py␊
from fastapi import APIRouter, Depends, HTTPException␊
from sqlalchemy.orm import Session␊
from typing import List␊
␊
from app.database import get_db␊
from app.models import Project, Transcription, TranscriptionSegment, ProcessedScript, ProcessedSegment␊
try:␊
    from app.utils.script_pipeline import ScriptProcessor␊
except Exception as e:␊
    ScriptProcessor = None␊
    _script_import_error = e␊
else:␊
    _script_import_error = None␊
␊
router = APIRouter()␊
script_processor = ScriptProcessor() if ScriptProcessor else None␊
␊
@router.post("/process/{project_id}")␊
def process_script(
    project_id: int,
    target_languages: List[str],  # e.g. ["en", "hi", "te", "ja"]
    db: Session = Depends(get_db)
):
    """␊
    1) Fetch the latest Transcription for the project.␊
    2) For each segment, do grammar cleaning & translation for each requested language.␊
    3) Save the processed results in DB (ProcessedScript & ProcessedSegment).␊
    4) Return a structured JSON of processed scripts.␊
    """␊
    if script_processor is None:
        msg = f"Script processor unavailable: {_script_import_error}" if _script_import_error else "Script processor not initialised"␊
        raise HTTPException(status_code=500, detail=msg)␊
␊
    # 1) Validate project & transcription␊
    project = db.query(Project).filter(Project.id == project_id).first()␊
    if not project:␊
        raise HTTPException(status_code=404, detail="Project not found.")␊
␊
    transcription = db.query(Transcription).filter(Transcription.project_id == project_id).first()␊
    if not transcription:␊
        raise HTTPException(status_code=400, detail="No transcription found for this project. Run ASR first.")␊
␊
    segments = transcription.segments␊
    if not segments:␊
        raise HTTPException(status_code=400, detail="Transcription has no segments.")␊
␊
    # 2) For each target language, create a new ProcessedScript␊
    response_data = []␊
    for tgt_lang in target_languages:␊
        # Create (or replace) a ProcessedScript record␊
        # Optional: check if one already exists for project_id + tgt_lang␊
        existing_ps = db.query(ProcessedScript).filter(␊
            ProcessedScript.project_id == project_id,␊
            ProcessedScript.target_language == tgt_lang␊
        ).first()␊
        if existing_ps:␊
            # Delete old segments␊
            db.query(ProcessedSegment).filter(ProcessedSegment.processed_script_id == existing_ps.id).delete()␊
            db.delete(existing_ps)␊
            db.commit()␊
␊
        processed_script = ProcessedScript(␊
            project_id=project_id,␊
            target_language=tgt_lang␊
        )␊
        db.add(processed_script)␊
        db.flush()␊
␊
        # 3) For each transcription segment, process text␊
        segment_data_list = []␊
        for seg in segments:␊
            source_lang = seg.language_detected if seg.language_detected else "en" ␊
            # or you might let the user specify the real source language␊
␊
            # run pipeline␊
            processed_text = script_processor.process_segment(␊
                segment_text=seg.text,␊
                source_lang=source_lang,␊
                target_lang=tgt_lang␊
            )␊
␊
            new_pseg = ProcessedSegment(␊
                processed_script_id=processed_script.id,␊
                transcription_segment_id=seg.id,␊
                start_time=seg.start_time,␊
                end_time=seg.end_time,␊
                speaker_label=seg.speaker_label,␊
                processed_text=processed_text␊
            )␊
            db.add(new_pseg)␊
␊
            segment_data_list.append({␊
                "start_time": seg.start_time,␊
                "end_time": seg.end_time,␊
                "speaker": seg.speaker_label,␊
                "text": processed_text␊
            })␊
␊
        db.commit()␊
        db.refresh(processed_script)␊
␊
        # Build the final JSON structure for this language␊
        language_script_json = {␊
            "target_language": tgt_lang,␊
            "segments": segment_data_list␊
        }␊
        response_data.append(language_script_json)␊
␊
    return {␊
        "project_id": project_id,␊
        "processed_scripts": response_data␊
    }␊
