"""
Quick Prediction Router
=======================
Direct CV inference endpoint for fast client verification without database side-effects.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.storage import storage_service
from app.services.inference import inference_service
from app.schemas.prediction import PredictionResponse

router = APIRouter(prefix="/api/v1/predict", tags=["Inference"])


@router.post("", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    # Validate and decode in memory without saving to permanent storage
    try:
        _, _, pil_image = await storage_service.validate_and_save_upload(file)
        prediction_result, _ = inference_service.predict(pil_image)
        return prediction_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference pipeline error: {str(e)}"
        )
