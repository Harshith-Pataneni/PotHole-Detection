"""
Authentication Data Contracts
=============================
Pydantic v2 schemas for login credentials, token payloads, and user profiles.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_email: str
    user_name: str
    role: str


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
