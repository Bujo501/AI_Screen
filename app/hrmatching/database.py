# ============================
# backend/hrmatching/database.py
# ============================
from __future__ import annotations
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "hrmatching.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def init_db() -> None:
    from . import models  # ensure models are registered
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    with Session(engine) as session:
        yield session
