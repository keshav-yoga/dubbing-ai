# backend/app/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to uploaded files
    uploaded_files = relationship("UploadedFile", back_populates="project")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_type = Column(String)       # e.g., "video" or "audio"
    file_path = Column(String)       # local path or S3 URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project = relationship("Project", back_populates="uploaded_files")



# NEW Models
class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="transcription")
    segments = relationship("TranscriptionSegment", back_populates="transcription")

class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"
    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker_label = Column(String)
    language_detected = Column(String)
    text = Column(String)

    transcription = relationship("Transcription", back_populates="segments")



class ProcessedScript(Base):
    __tablename__ = "processed_scripts"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    target_language = Column(String, nullable=False)  # e.g. "en", "ta", "te"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to segments
    processed_segments = relationship("ProcessedSegment", back_populates="processed_script")

class ProcessedSegment(Base):
    __tablename__ = "processed_segments"
    id = Column(Integer, primary_key=True, index=True)
    processed_script_id = Column(Integer, ForeignKey("processed_scripts.id"), nullable=False)
    transcription_segment_id = Column(Integer, ForeignKey("transcription_segments.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker_label = Column(String)
    processed_text = Column(String)

    processed_script = relationship("ProcessedScript", back_populates="processed_segments")
# NEW: TTS
class TTSGeneration(Base):
    """
    Represents a TTS run for a given ProcessedScript (and possibly a specific voice config).
    """
    __tablename__ = "tts_generations"
    id = Column(Integer, primary_key=True, index=True)
    processed_script_id = Column(Integer, ForeignKey("processed_scripts.id"), nullable=False)
    voice_name = Column(String, nullable=False)  # e.g., "en_male_1" or "google_ar_standard"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to TTS segments
    tts_segments = relationship("TTSSegment", back_populates="tts_generation")

class TTSSegment(Base):
    """
    Each TTS segment audio file for the processed text. 
    """
    __tablename__ = "tts_segments"
    id = Column(Integer, primary_key=True, index=True)
    tts_generation_id = Column(Integer, ForeignKey("tts_generations.id"), nullable=False)
    processed_segment_id = Column(Integer, ForeignKey("processed_segments.id"), nullable=False)

    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker_label = Column(String)
    audio_file_path = Column(String)  # local path or S3 URL

    tts_generation = relationship("TTSGeneration", back_populates="tts_segments")

# NEW: Lip Sync
class LipSyncJob(Base):
    __tablename__ = "lip_sync_jobs"
    id = Column(Integer, primary_key=True, index=True)
    tts_generation_id = Column(Integer, ForeignKey("tts_generations.id"), nullable=False)
    video_file_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lip_sync_segments = relationship("LipSyncSegment", back_populates="lip_sync_job")

class LipSyncSegment(Base):
    __tablename__ = "lip_sync_segments"
    id = Column(Integer, primary_key=True, index=True)
    lip_sync_job_id = Column(Integer, ForeignKey("lip_sync_jobs.id"), nullable=False)
    tts_segment_id = Column(Integer, ForeignKey("tts_segments.id"), nullable=False)

    # Path to the new "aligned" or time-stretched audio
    aligned_audio_path = Column(String)

    # We might store phoneme-level or word-level alignment data
    # For example, a JSON field with alignment details
    # If your DB supports JSON type:
    # alignment_json = Column(JSON)

    lip_sync_job = relationship("LipSyncJob", back_populates="lip_sync_segments")

# NEW: Audio mixing
class AudioMixJob(Base):
    __tablename__ = "audio_mix_jobs"
    id = Column(Integer, primary_key=True, index=True)
    lip_sync_job_id = Column(Integer, ForeignKey("lip_sync_jobs.id"), nullable=False)
    original_audio_path = Column(String, nullable=False)  # The original background track or film audio
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    audio_mix_segments = relationship("AudioMixSegment", back_populates="audio_mix_job")

class AudioMixSegment(Base):
    __tablename__ = "audio_mix_segments"
    id = Column(Integer, primary_key=True, index=True)
    audio_mix_job_id = Column(Integer, ForeignKey("audio_mix_jobs.id"), nullable=False)
    output_audio_path = Column(String)  # final or intermediate track
    channel_info = Column(String)  # e.g., "Stereo" or "5.1"

    audio_mix_job = relationship("AudioMixJob", back_populates="audio_mix_segments")


# NEW: FinalOutput
class FinalOutputJob(Base):
    __tablename__ = "final_output_jobs"
    id = Column(Integer, primary_key=True, index=True)
    audio_mix_job_id = Column(Integer, ForeignKey("audio_mix_jobs.id"), nullable=False)
    video_file_path = Column(String)     # Original video or final output path
    final_video_path = Column(String)    # The newly generated final video
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subtitles = relationship("SubtitleFile", back_populates="final_output_job")

class SubtitleFile(Base):
    __tablename__ = "subtitle_files"
    id = Column(Integer, primary_key=True, index=True)
    final_output_job_id = Column(Integer, ForeignKey("final_output_jobs.id"), nullable=False)
    language_code = Column(String)
    subtitle_format = Column(String)  # "srt" or "vtt"
    file_path = Column(String)        # path to the .srt/.vtt file
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    final_output_job = relationship("FinalOutputJob", back_populates="subtitles")