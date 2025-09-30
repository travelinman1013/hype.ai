"""
Common FastAPI Dependencies.

Reusable dependencies for authentication, authorization, and database sessions.
"""


from auth.models import User
from database import get_session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.jwt import get_user_id_from_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from users.models import Subscription

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    Get current user ID from JWT token in Authorization header.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid or user ID cannot be extracted
    """
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    return user_id


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        session: Database session
        user_id: User ID from JWT token

    Returns:
        User object

    Raises:
        HTTPException: If user not found
    """
    result = await session.execute(
        select(User).where(User.id == user_id)
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
