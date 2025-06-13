from sqlalchemy import Column, Integer, String, DateTime, func
from pgvector.sqlalchemy import Vector
from .db import Base

class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    embedding = Column(Vector(768))  # pgvector extension
    created_at = Column(DateTime(timezone=True), server_default=func.now())