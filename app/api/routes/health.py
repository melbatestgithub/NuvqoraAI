
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "success": True,
        "application": "Nuvqora AI",
        "status": "running"
    }


@router.get("/health/database")
async def database_health(
    db: AsyncSession = Depends(get_db)
):
    try:
        await db.execute(text("SELECT 1"))

        return {
            "success": True,
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
