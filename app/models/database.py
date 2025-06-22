from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import hashlib

Base = declarative_base()

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    status = Column(String, default="pending")
    image_hash = Column(String, index=True)
    result_svg = Column(Text, nullable=True)
    mask_contours = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class ImageCache(Base):
    __tablename__ = "image_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    image_hash = Column(String, unique=True, index=True)
    svg_result = Column(Text)
    mask_contours = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Note: The get_db dependency function will be added later in app/core/dependencies.py