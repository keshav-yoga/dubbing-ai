# backend/app/config.py

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dubbing-AI"
    API_VERSION: str = "v1"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dubbing_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # AWS (Optional) - for S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "my-dubbing-bucket"

    # Storage local folder
    LOCAL_STORAGE_PATH: str = "/tmp/dubbing_ai"

    class Config:
        env_file = ".env"

settings = Settings()
