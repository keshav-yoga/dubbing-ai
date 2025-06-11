# backend/app/routers/upload.py␊
␊
import os␊
import uuid␊
import shutil␊
import ffmpeg␊
from fastapi import APIRouter, UploadFile, File, Depends, Form␊
from sqlalchemy.orm import Session␊
␊
from app.database import get_db␊
from app.models import Project, UploadedFile␊
from app.config import settings␊
import boto3␊
␊
router = APIRouter()␊
␊
@router.post("/")␊
def upload_video(␊
    db: Session = Depends(get_db),␊
    title: str = Form(...),␊
    file: UploadFile = File(...)␊
):␊
    """␊
    1. Create a new Project record in DB with a title.␊
    2. Store the uploaded video (locally or in S3).␊
    3. Extract audio from the video with FFmpeg.␊
    4. Store references in DB (both video and audio).␊
    """␊
    # 1) Create project␊
    new_project = Project(title=title)␊
    db.add(new_project)␊
    db.commit()␊
    db.refresh(new_project)␊
␊
    # 2) Handle file storage␊
    # Generate a unique filename␊
    original_filename = file.filename␊
    file_ext = os.path.splitext(original_filename)[1]␊
    unique_name = f"{uuid.uuid4()}{file_ext}"␊
␊
    # Decide local or S3:␊
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.S3_BUCKET_NAME:␊
        # Upload to S3␊
        s3 = boto3.client(␊
            "s3",␊
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,␊
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,␊
            region_name=settings.AWS_DEFAULT_REGION␊
        )␊
        s3_key = f"uploads/videos/{unique_name}"␊
        s3.upload_fileobj(file.file, settings.S3_BUCKET_NAME, s3_key)␊
        video_path = f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"  # or an HTTP URL if you configure it␊
    else:␊
        # Store locally␊
        local_folder = settings.LOCAL_STORAGE_PATH␊
        if not os.path.exists(local_folder):␊
            os.makedirs(local_folder, exist_ok=True)␊
␊
        video_path = os.path.join(local_folder, unique_name)␊
        with open(video_path, "wb") as buffer:␊
            shutil.copyfileobj(file.file, buffer)␊
␊
    # Store DB record for the video␊
    video_record = UploadedFile(␊
        project_id=new_project.id,␊
        file_type="video",␊
        file_path=video_path␊
    )␊
    db.add(video_record)␊
    db.commit()␊
    db.refresh(video_record)␊
␊
    # 3) Extract audio from the video␊
    audio_unique_name = f"{uuid.uuid4()}.wav"␊
    audio_path = os.path.join(settings.LOCAL_STORAGE_PATH, audio_unique_name)␊
␊
    # We need the actual local file path for ffmpeg␊
    # If using S3, first you’d download it or stream it to a local temp file.␊
    local_video_path = video_path␊
    if video_path.startswith("s3://"):␊
        # Example: download from S3 to local temp. In production, stream or handle more robustly␊
        s3_url_parts = video_path.replace("s3://", "").split("/", 1)␊
        bucket_name = s3_url_parts[0]␊
        s3_key_file = s3_url_parts[1]␊
        temp_local_file = os.path.join(settings.LOCAL_STORAGE_PATH, f"temp_{unique_name}")␊
        s3.download_file(bucket_name, s3_key_file, temp_local_file)␊
        local_video_path = temp_local_file␊
␊
    # Use ffmpeg-python to extract audio␊
    (␊
        ffmpeg␊
        .input(local_video_path)␊
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')␊
        .overwrite_output()␊
        .run()␊
    )␊
␊
    # 4) (Optional) If you want to separate vocals from music,␊
    #    you'll need a separate pipeline (like Spleeter or demucs).␊
    #    We’re omitting that here for brevity.␊
␊
    # 5) Store the audio file in DB (local or push to S3)␊
    audio_record = UploadedFile(␊
        project_id=new_project.id,␊
        file_type="audio",␊
        file_path=audio_path␊
    )␊
    db.add(audio_record)␊
    db.commit()␊
    db.refresh(audio_record)␊
␊
    return {␊
        "message": "Video uploaded and audio extracted successfully.",␊
        "project_id": new_project.id,␊
        "video_file_path": video_record.file_path,␊
        "audio_file_path": audio_record.file_path␊
    }␊
