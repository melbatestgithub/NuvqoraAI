
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from app.core.dependencies import get_current_user
from app.core.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(User).where(
            User.email == payload.email.lower()
        )
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Email is already registered.",
        )

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)

    except Exception:
        await db.rollback()
        raise

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(User).where(
            User.email == payload.email.lower()
        )
    )

    user = result.scalar_one_or_none()

    if (
        user is None
        or not user.hashed_password
        or not verify_password(
            payload.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive.",
        )

    token = create_access_token(str(user.id))

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
