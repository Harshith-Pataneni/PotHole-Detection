"""
Report Data Contracts
=====================
Pydantic v2 schemas for civic report creation, public views, and admin updates.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ReportCreate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    user_priority: str = Field("MEDIUM", description="LOW | MEDIUM | HIGH | CRITICAL")
    address_text: Optional[str] = Field(None, max_length=255)

    @field_validator("user_priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid:
            raise ValueError(f"Priority must be one of {valid}")
        return upper_v


class ReportPublicItem(BaseModel):
    id: str
    public_id: str
    latitude: float
    longitude: float
    user_priority: str
    estimated_severity: str
    model_confidence: float
    status: str
    created_at: datetime
    image_url: str
    thumbnail_url: Optional[str] = None
    address_text: Optional[str] = None
    confirmations_count: int = 1
    image_hash: Optional[str] = None

    class Config:
        from_attributes = True


class ReportDetail(ReportPublicItem):
    model_prediction: str
    model_version: str
    heatmap_url: Optional[str] = None
    admin_notes: Optional[str] = None
    updated_at: datetime


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., description="PENDING | UNDER_REVIEW | VERIFIED | REJECTED | RESOLVED")
    admin_notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"PENDING", "UNDER_REVIEW", "VERIFIED", "REJECTED", "RESOLVED"}
        upper_v = v.upper()
        if upper_v not in valid:
            raise ValueError(f"Status must be one of {valid}")
        return upper_v


class ReportSubmissionResponse(BaseModel):
    success: bool
    message: str = "Report processed"
    verified: bool
    confidence: float
    estimated_severity: str
    is_duplicate: bool = False
    confirmations_count: int = 1
    report: Optional[ReportDetail] = None
    guidance: Optional[str] = None
