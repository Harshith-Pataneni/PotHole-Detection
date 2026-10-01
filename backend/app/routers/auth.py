"""
Authentication Router
=====================
Admin login and profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_admin
from app.models.user import AdminUser
from app.schemas.user import LoginRequest, TokenResponse, AdminUserResponse
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    query = select(AdminUser).where(AdminUser.email == credentials.email.lower())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account has been deactivated"
        )

    token = create_access_token(data={
        "sub": user.email,
        "role": user.role,
        "name": user.full_name
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_email=user.email,
        user_name=user.full_name,
        role=user.role
    )


@router.get("/me", response_model=AdminUserResponse)
async def get_me(
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(AdminUser).where(AdminUser.email == current_admin["email"])
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
