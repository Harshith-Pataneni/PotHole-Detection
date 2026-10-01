"""
Model Evaluation & Telemetry Router
===================================
Exposes the versioned ML model evaluation metrics, confusion matrix, ROC curves,
and sample hold-out predictions for administrative audit and interview defense.
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.core.security import get_current_admin
from app.config import settings

router = APIRouter(prefix="/api/v1/model", tags=["Model Telemetry"])


@router.get("/metrics")
async def get_model_metrics(admin: dict = Depends(get_current_admin)):
    """Returns official hold-out evaluation metrics from model metadata.json."""
    meta_path = Path(settings.MODEL_METADATA_PATH)
    if not meta_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Model evaluation metadata artifact has not yet been exported."
        )

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    return metadata


@router.get("/confusion-matrix.png")
async def get_confusion_matrix_plot():
    """Serves the test set confusion matrix plot."""
    plot_path = Path("./ml/models/v1/confusion_matrix.png")
    if not plot_path.exists():
        raise HTTPException(status_code=404, detail="Confusion matrix plot not found")
    return FileResponse(plot_path, media_type="image/png")


@router.get("/roc-curve.png")
async def get_roc_curve_plot():
    """Serves the test set ROC curve plot."""
    plot_path = Path("./ml/models/v1/roc_curve.png")
    if not plot_path.exists():
        raise HTTPException(status_code=404, detail="ROC curve plot not found")
    return FileResponse(plot_path, media_type="image/png")
