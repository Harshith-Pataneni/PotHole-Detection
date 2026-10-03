"""
Report Database Model
=====================
Defines the schema for civic pothole and road-defect submissions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    
    # Storage URLs
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)
    heatmap_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # Location (WGS84 GPS)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address_text: Mapped[str] = mapped_column(String(255), nullable=True)

    # User Input
    user_priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")

    # CV Model Output
    model_prediction: Mapped[str] = mapped_column(String(30), nullable=False)
    model_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(30), nullable=False)
    estimated_severity: Mapped[str] = mapped_column(String(20), nullable=False)

    # Administrative Status
    # Status: PENDING | UNDER_REVIEW | VERIFIED | REJECTED | RESOLVED
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", index=True)
    admin_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Deduplication & Redundancy Tracking
    confirmations_count: Mapped[int] = mapped_column(default=1, nullable=False)
    image_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


# Compound indices for fast map coordinate queries and dashboard filters
Index("idx_reports_coords", Report.latitude, Report.longitude)
Index("idx_reports_status_created", Report.status, Report.created_at.desc())
