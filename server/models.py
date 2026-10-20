from sqlalchemy import Column, String, Integer, DateTime, Text, Float
from datetime import datetime
from .db import Base


class Archive(Base):
    __tablename__ = "archives"
    id            = Column(String, primary_key=True)
    filename      = Column(String, nullable=False)
    size_orig     = Column(Integer, nullable=False)
    size_comp     = Column(Integer, nullable=False)
    sha256_orig   = Column(String(64), nullable=False, index=True)
    storage_path  = Column(String, nullable=False)
    mode          = Column(String, default="lossless")
    created_at    = Column(DateTime, default=datetime.utcnow)
    status        = Column(String, default="ready")


class Job(Base):
    __tablename__ = "jobs"
    id            = Column(String, primary_key=True)
    kind          = Column(String, nullable=False)
    archive_id    = Column(String, nullable=True)
    status        = Column(String, default="queued")
    progress      = Column(Float, default=0.0)
    message       = Column(Text, default="")
    result_json   = Column(Text, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)