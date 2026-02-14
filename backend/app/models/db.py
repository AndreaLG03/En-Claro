import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from ..config import settings

# --- Database Config ---
# Use SQLite for now. In production (Render), this should be Postgres.
# Render provides a DATABASE_URL env var.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./enclaro.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    history = relationship("AnalysisHistory", back_populates="user")

class AnalysisHistory(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"))
    module = Column(String)  # 'roleplay', 'decoder', etc.
    input_text = Column(Text)
    result_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default={}) # Store extra info like scenario name

    # Relationship
    user = relationship("User", back_populates="history")

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Init DB ---
def init_db():
    Base.metadata.create_all(bind=engine)
