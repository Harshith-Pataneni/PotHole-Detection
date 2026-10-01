"""
Main FastAPI Application Entrypoint
====================================
Integrates routers, CORS, static uploads mounting, database migrations, and initial seed.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.logging import setup_logging, logger
from app.models.user import AdminUser
from app.models.report import Report
from app.routers import auth, reports, predict, admin, telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing Pothole Detection & Civic Reporting Platform Backend...")

    # Create database schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema verified.")

    # Seed initial admin if none exists
    async with AsyncSessionLocal() as session:
        query = select(AdminUser).where(AdminUser.email == settings.ADMIN_INITIAL_EMAIL.lower())
        result = await session.execute(query)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            initial_admin = AdminUser(
                email=settings.ADMIN_INITIAL_EMAIL.lower(),
                hashed_password=get_password_hash(settings.ADMIN_INITIAL_PASSWORD),
                full_name="Municipal Operations Admin",
                role="ADMIN",
                is_active=True
            )
            session.add(initial_admin)
            await session.commit()
            logger.info(f"Initialized default administrator account: {settings.ADMIN_INITIAL_EMAIL}")

    # Ensure upload directory exists
    Path(settings.LOCAL_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Shutting down backend services...")
    await engine.dispose()


app = FastAPI(
    title="Pothole Detection & Civic Road-Defect Reporting API",
    description="Production-grade civic reporting platform backed by PyTorch ResNet-50 CV inference & Grad-CAM.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file storage for uploaded images
uploads_dir = Path(settings.LOCAL_UPLOAD_DIR).parent
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(predict.router)
app.include_router(admin.router)
app.include_router(telemetry.router)


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "model_version": settings.MODEL_VERSION,
        "confidence_threshold": settings.POTHOLE_CONFIDENCE_THRESHOLD
    }
