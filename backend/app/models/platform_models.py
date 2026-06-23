import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    inference_requests = relationship("InferenceRequest", back_populates="hospital")

class InferenceRequest(Base):
    __tablename__ = "inference_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hospital_id: Mapped[int] = mapped_column(Integer, ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False)
    image_s3_uri: Mapped[str] = mapped_column(String(512), nullable=False) # Direct link to MinIO storage bucket
    prediction_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uncertainty_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    hospital = relationship("Hospital", back_populates="inference_requests")
    drift_logs = relationship("DriftLog", back_populates="request")
    feedback_log = relationship(
        "FeedbackLog", 
        back_populates="inference_request", 
        uselist=False, 
        cascade="all, delete-orphan"
    )

class DriftLog(Base):
    __tablename__ = "drift_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_requests.id", ondelete="CASCADE"), nullable=False)
    drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'Normal', 'Warning', 'Critical'
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    request = relationship("InferenceRequest", back_populates="drift_logs")

class FeedbackLog(Base):
    __tablename__ = "feedback_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_requests.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_agreed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    corrected_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Physicians corrective entry
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    request = relationship("InferenceRequest", back_populates="feedback_log")