from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from uuid import UUID
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address
from llmsync.database import get_db
from llmsync.models import User
from llmsync.auth import create_access_token, create_refresh_token, decode_refresh_token
from llmsync.services.redis_client import redis_client
from llmsync.services.email import send_magic_link_email
from llmsync.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

class MagicLinkRequest(BaseModel):
    email: EmailStr

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/login/magic-link")
@limiter.limit("10/minute")
async def login_magic_link(
    request: MagicLinkRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """Send magic link to email."""
    # Get or create user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=request.email,
            encrypted_master_key_backup="",
            salt=b""
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate magic link token
    token = secrets.token_urlsafe(32)

    # Store in Redis with 30-minute expiration
    await redis_client.set_with_expiry(
        f"magic_link:{token}",
        str(user.id),
        expire_seconds=30 * 60
    )

    # Send email
    await send_magic_link_email(request.email, token)

    return {"message": "Check your email for login link"}

@router.get("/verify")
async def verify_magic_link(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify magic link token and create session."""
    # Get user_id from Redis
    user_id_str = await redis_client.get(f"magic_link:{token}")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Delete token (one-time use)
    await redis_client.delete(f"magic_link:{token}")

    # Get user
    user_id = UUID(user_id_str)
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Store session in Redis
    await redis_client.set_with_expiry(
        f"session:{access_token}",
        str(user.id),
        expire_seconds=7 * 24 * 60 * 60  # 7 days
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )

@router.post("/refresh")
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = decode_refresh_token(request.refresh_token)
    user_id = UUID(payload["user_id"])

    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new access token
    access_token = create_access_token(user.id)

    # Store session
    await redis_client.set_with_expiry(
        f"session:{access_token}",
        str(user.id),
        expire_seconds=7 * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout (invalidate session)."""
    token = credentials.credentials
    await redis_client.delete(f"session:{token}")

    return {"message": "Logged out successfully"}
