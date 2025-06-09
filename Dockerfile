# -------- Build stage --------
FROM python:3.12-slim AS base

# 1. System deps you usually need for ML + ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc build-essential git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 2. Faster installs & security
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 3. Install Python deps first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 4. Copy source
COPY backend ./backend
ENV PYTHONPATH="/app/backend:${PYTHONPATH}"

# 5. Gunicorn + Uvicorn default command
CMD ["gunicorn", "backend.app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "0"]
