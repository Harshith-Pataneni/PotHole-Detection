"""
Application Configuration
=========================
Type-safe application configuration loaded from environment variables and .env file.
"""

from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent.parent / 'pothole_platform.db'}"

    # Security & Auth
    AUTH_SECRET: str = "default_insecure_secret_key_change_in_production_32chars"
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_INITIAL_EMAIL: str = "admin@civicworks.org"
    ADMIN_INITIAL_PASSWORD: str = "admin_secure_change_me_123"

    # Model & Inference
    MODEL_VERSION: str = "v1"
    MODEL_WEIGHTS_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "v1" / "model.pt")
    MODEL_METADATA_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "v1" / "metadata.json")
    POTHOLE_CONFIDENCE_THRESHOLD: float = 0.75
    DEVICE: str = "cpu"

    # Storage
    STORAGE_PROVIDER: str = "local"
    LOCAL_UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads" / "potholes")
    MAX_UPLOAD_SIZE_MB: int = 10

    # Email Notifications
    EMAIL_PROVIDER: str = "console"  # 'console' | 'smtp' | 'resend'
    EMAIL_FROM: str = "alerts@civicworks.org"
    ADMIN_ALERT_EMAIL: str = "admin@civicworks.org"
    SMTP_HOST: str = "smtp.mailtrap.io"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    RESEND_API_KEY: str = ""

    # Reverse Geocoding
    REVERSE_GEOCODING_ENABLED: bool = True


settings = Settings()
