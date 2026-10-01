"""
Prediction Data Contracts
=========================
Pydantic v2 schemas for CV model inference results.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    is_pothole: bool = Field(..., description="Whether the model confidently classified the defect as a pothole")
    confidence: float = Field(..., description="Classification probability score [0.0 - 1.0]")
    model_version: str = Field(..., description="Model artifact version identifier")
    estimated_severity: str = Field(..., description="Estimated visual severity heuristic (LOW, MEDIUM, HIGH, CRITICAL)")
    severity_breakdown: Optional[Dict[str, Any]] = Field(None, description="Detailed components of heuristic computation")
    heatmap_preview_base64: Optional[str] = Field(None, description="Optional Grad-CAM visual overlay for immediate UI review")
