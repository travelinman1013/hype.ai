"""User Management API Routes."""

from auth.models import User
from database import get_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Subscription, WorkoutSession

router = APIRouter()


@router.get("/me")
async def get_user_profile(
    user_id: int = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_session),
):
    """Get user profile."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": user.id,
        "spotify_user_id": user.spotify_user_id,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": user.created_at,
    }


@router.get("/me/subscription")
async def get_subscription(
    user_id: int = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_session),
):
    """Get user subscription."""
    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = result.scalars().first()

    if not subscription:
        # Return default free subscription
        return {"tier": "free", "status": "active"}

    return {
        "tier": subscription.tier,
        "status": subscription.status,
        "started_at": subscription.started_at,
        "expires_at": subscription.expires_at,
    }


@router.get("/me/workouts")
async def get_workout_history(
    user_id: int = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_session),
):
    """Get workout session history (premium only)."""
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id)
        .order_by(WorkoutSession.started_at.desc())
        .limit(50)
    )
    workouts = result.scalars().all()

    return {
        "workouts": [
            {
                "id": w.id,
                "started_at": w.started_at,
                "ended_at": w.ended_at,
                "avg_heart_rate": w.avg_heart_rate,
                "max_heart_rate": w.max_heart_rate,
                "duration_minutes": w.duration_minutes,
            }
            for w in workouts
        ]
    }
