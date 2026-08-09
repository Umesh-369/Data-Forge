from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False, default="csv")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    parent_version_id = Column(String(36), ForeignKey("dataset_versions.id"), nullable=True)
    file_path = Column(Text, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    col_count = Column(Integer, nullable=False, default=0)
    transformation_op = Column(JSON, nullable=True)  # Operation that produced this version
    profile_json = Column(JSON, nullable=True)      # Cached profiling stats (Invariant I8)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="versions")
    parent = relationship("DatasetVersion", remote_side=[id])

class EditLog(Base):
    __tablename__ = "edit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("dataset_versions.id"), nullable=False)
    user_prompt = Column(Text, nullable=False)
    operations_json = Column(JSON, nullable=False)
    diff_summary_json = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending") # pending, applied, rejected
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MLJob(Base):
    __tablename__ = "ml_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("dataset_versions.id"), nullable=False)
    target_column = Column(String(255), nullable=False)
    problem_type = Column(String(50), nullable=False) # classification / regression
    recommendation_json = Column(JSON, nullable=True)
    model_results_json = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending") # pending, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
