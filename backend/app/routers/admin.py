"""
Admin Dashboard Aggregate Statistics
====================================
Protected aggregate endpoints for municipal decision makers.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.report import Report

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Portal"])


@router.get("/stats")
async def get_admin_stats(
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Total reports
    total_query = select(func.count(Report.id))
    total_reports = (await db.execute(total_query)).scalar() or 0

    # Counts by status
    status_query = select(Report.status, func.count(Report.id)).group_by(Report.status)
    status_results = (await db.execute(status_query)).all()
    status_counts = {status: count for status, count in status_results}

    # Counts by severity
    sev_query = select(Report.estimated_severity, func.count(Report.id)).group_by(Report.estimated_severity)
    sev_results = (await db.execute(sev_query)).all()
    severity_counts = {sev: count for sev, count in sev_results}

    # Average confidence
    avg_conf_query = select(func.avg(Report.model_confidence))
    avg_conf = (await db.execute(avg_conf_query)).scalar() or 0.0

    # Recent 5 reports
    recent_query = select(Report).order_by(desc(Report.created_at)).limit(5)
    recent_reports = (await db.execute(recent_query)).scalars().all()

    return {
        "total_reports": total_reports,
        "status_breakdown": {
            "pending": status_counts.get("PENDING", 0),
            "under_review": status_counts.get("UNDER_REVIEW", 0),
            "verified": status_counts.get("VERIFIED", 0),
            "rejected": status_counts.get("REJECTED", 0),
            "resolved": status_counts.get("RESOLVED", 0)
        },
        "severity_breakdown": {
            "critical": severity_counts.get("CRITICAL", 0),
            "high": severity_counts.get("HIGH", 0),
            "medium": severity_counts.get("MEDIUM", 0),
            "low": severity_counts.get("LOW", 0)
        },
        "average_confidence": round(float(avg_conf), 3),
        "recent_reports": [
            {
                "id": r.id,
                "public_id": r.public_id,
                "status": r.status,
                "user_priority": r.user_priority,
                "estimated_severity": r.estimated_severity,
                "model_confidence": r.model_confidence,
                "created_at": r.created_at,
                "address_text": r.address_text
            }
            for r in recent_reports
        ]
    }
