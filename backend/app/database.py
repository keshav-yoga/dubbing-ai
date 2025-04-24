"""
Central SQLAlchemy + Pydantic settings wrapper
Works unchanged on:
  • local `uvicorn` runs  
  • Google Colab notebooks  
  • Docker / AWS EC2 / ECS / Lambda  

✓ 100 % blocking-safe (no async engine required)  
✓ Automatic DB-URL fallback order:  
    1. env var DATABASE_URL  
    2. dotenv file `.env` in backend/  
    3. SQLite `./dubbing.db` (ideal for Colab)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Generator

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ───────────────────────────────────── settings ──────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]   # backend/

class Settings(BaseSettings):
    """Global config resolved once then cached."""
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8")

    DATABASE_URL: str | None = None          # e.g. postgresql://user:pass@host:5432/db

    @property
    def safe_db_url(self) -> str:
        """Return valid SQLAlchemy URL or fallback to file-based SQLite."""
        if self.DATABASE_URL:                       # env var wins
            return self.DATABASE_URL
        # default local SQLite = ./dubbing.db
        return f"sqlite:///{ROOT_DIR / 'dubbing.db'}"

@lru_cache
def get_settings() -> Settings:
    return Settings()          # read once, then cache


# ──────────────────────────────────── SQLAlchemy ────────────────────────────────────
settings = get_settings()

# echo=True for SQL debugging when needed
engine = create_engine(settings.safe_db_url, echo=False, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db() -> Generator:
    """
    Usage (FastAPI dependency):

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
