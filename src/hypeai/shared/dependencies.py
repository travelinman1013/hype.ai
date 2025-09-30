"""
Common FastAPI Dependencies.

Reusable dependencies for authentication, authorization, and database sessions.
"""


from auth.models import User
from database import get_session
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from users.models import Subscription


async def get_current_user_id(user_id: str | None = None) -> str:
    """
    Get current user ID from request context.

    This is a placeholder - in production, extract from JWT token or session.

    Args:
        user_id: User ID from token/session

    Returns:
        User ID

    Raises:
        HTTPException: If user is not authenticated
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> User:
    """
    Get current authenticated user.

    Args:
        session: Database session
        user_id: User ID from authentication

    Returns:
        User object

    Raises:
        HTTPException: If user not found
    """
    result = await session.execute(
        select(User).where(User.spotify_user_id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


async def require_premium(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Require user to have premium subscription.

    Args:
        user: Current user
        session: Database session

    Returns:
        User object if premium

    Raises:
        HTTPException: If user doesn't have premium subscription
    """
    result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.tier == "premium"
        )
    )
    subscription = result.scalars().first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )

    return user
