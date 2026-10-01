"""
Civic Reports Router
====================
Handles submission, CV verification, filtering, detail retrieval, and administrative updates.
"""

from typing import List, Optional
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_admin
from app.core.logging import logger
from app.models.report import Report
from app.schemas.report import (
    ReportDetail, ReportPublicItem, ReportSubmissionResponse, ReportStatusUpdate
)
from app.services.storage import storage_service
from app.services.inference import inference_service
from app.services.notification import notification_service
from app.services.geocoding import geocoding_service
from app.config import settings

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


async def generate_public_id(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    query = select(func.count(Report.id))
    result = await db.execute(query)
    count = result.scalar() or 0
    return f"PH-{year}-{(count + 1):06d}"


@router.post("", response_model=ReportSubmissionResponse)
async def submit_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    user_priority: str = Form("MEDIUM"),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a suspected pothole report:
    1. Validates and decodes image.
    2. Runs PyTorch ResNet50 inference + Grad-CAM.
    3. Evaluates against POTHOLE_CONFIDENCE_THRESHOLD.
    4. If verified: creates DB record, saves images, triggers admin notification.
    5. If unverified: rejects from official DB, returns friendly guidance to citizen.
    """
    logger.info(f"Received report submission at ({latitude:.4f}, {longitude:.4f})")

    # 1. Image upload validation
    image_rel_url, thumb_rel_url, pil_image = await storage_service.validate_and_save_upload(file)

    # 2. Run CV Model Inference
    try:
        prediction, heatmap_img = inference_service.predict(pil_image)
    except Exception as e:
        logger.error(f"Inference execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )

    confidence = prediction["confidence"]
    is_pothole = prediction["is_pothole"]
    severity = prediction["estimated_severity"]

    # 3. Check Confidence Threshold (Configurable, Section 9 & 10)
    if not is_pothole or confidence < settings.POTHOLE_CONFIDENCE_THRESHOLD:
        logger.info(f"Report rejected by CV model (Confidence: {confidence:.2f} < Threshold {settings.POTHOLE_CONFIDENCE_THRESHOLD:.2f})")
        return ReportSubmissionResponse(
            success=False,
            message="We could not confidently verify this image as a road defect.",
            verified=False,
            confidence=confidence,
            estimated_severity=severity,
            guidance=(
                f"We could not confidently verify this image as a road pothole (Confidence: {confidence * 100:.1f}%). "
                f"Please ensure the camera is aimed directly at the road surface in daylight and retry."
            )
        )

    # 4. Save Grad-CAM Heatmap overlay
    report_uuid = str(uuid.uuid4())
    heatmap_url = storage_service.save_heatmap_overlay(heatmap_img, report_uuid)

    # 5. Reverse Geocode (Keyless, background-friendly)
    address_text = await geocoding_service.reverse_geocode(latitude, longitude)

    # 6. Generate Clean Sequential Public ID
    public_id = await generate_public_id(db)

    # 7. Persist to Database
    report = Report(
        id=report_uuid,
        public_id=public_id,
        image_url=image_rel_url,
        thumbnail_url=thumb_rel_url,
        heatmap_url=heatmap_url,
        latitude=latitude,
        longitude=longitude,
        address_text=address_text,
        user_priority=user_priority.upper(),
        model_prediction="pothole",
        model_confidence=confidence,
        model_version=prediction["model_version"],
        estimated_severity=severity,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    # 8. Asynchronous Admin Notification
    report_data = {
        "public_id": public_id,
        "latitude": latitude,
        "longitude": longitude,
        "address_text": address_text,
        "user_priority": user_priority.upper(),
        "model_confidence": confidence,
        "estimated_severity": severity,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    background_tasks.add_task(notification_service.send_pothole_alert, report_data)

    logger.info(f"Verified report created successfully: {public_id}")

    return ReportSubmissionResponse(
        success=True,
        message="Pothole verified and report successfully registered.",
        verified=True,
        confidence=confidence,
        estimated_severity=severity,
        report=ReportDetail.model_validate(report),
        guidance="Pothole verified by computer vision model and queued for administrative review."
    )


@router.get("", response_model=List[ReportPublicItem])
async def list_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Public report list for map markers and recent defect feed."""
    query = select(Report).order_by(desc(Report.created_at)).limit(limit)
    if status_filter:
        query = query.where(Report.status == status_filter.upper())
    if severity:
        query = query.where(Report.estimated_severity == severity.upper())

    result = await db.execute(query)
    reports = result.scalars().all()
    return reports


@router.get("/{id_or_public_id}", response_model=ReportDetail)
async def get_report(id_or_public_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch individual report details."""
    query = select(Report).where(
        (Report.id == id_or_public_id) | (Report.public_id == id_or_public_id)
    )
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{id_or_public_id}", response_model=ReportDetail)
async def update_report_status(
    id_or_public_id: str,
    update_data: ReportStatusUpdate,
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only endpoint to transition report status and append notes."""
    query = select(Report).where(
        (Report.id == id_or_public_id) | (Report.public_id == id_or_public_id)
    )
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = update_data.status
    if update_data.admin_notes is not None:
        report.admin_notes = update_data.admin_notes
    report.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(report)

    logger.info(f"Report {report.public_id} status updated to {report.status} by admin {admin.get('email')}")
    return report
