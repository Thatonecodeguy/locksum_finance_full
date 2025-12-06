from __future__ import annotations
import os
from urllib.parse import quote, urlparse, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

def _normalize_db_url() -> str:
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if not raw:
        return "sqlite:///./dev.db"
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
    if "postgresql+psycopg2://" in raw and "sslmode=" not in raw and not any(h in raw for h in ("localhost", "127.0.0.1")):
        raw += ("&" if "?" in raw else "?") + "sslmode=require"
    return raw

DATABASE_URL = _normalize_db_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
