"""
Authentication API Routes.

FastAPI endpoints for Spotify OAuth2 authentication flow.
"""

import logging
import secrets

import httpx
from database import get_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import AuthSuccessResponse, LogoutResponse, SpotifyAuthURL, UserResponse
from .services import AuthService
from .spotify_client import SpotifyOAuthClient

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/spotify", response_model=SpotifyAuthURL)
async def get_spotify_auth_url():
    """
    Get Spotify authorization URL.

    Returns:
        Authorization URL for user to visit
    """
    state = secrets.token_urlsafe(32)
    spotify_client = SpotifyOAuthClient()
    auth_url = spotify_client.get_authorization_url(state=state)

    return SpotifyAuthURL(auth_url=auth_url, state=state)


@router.get("/spotify/callback", response_model=AuthSuccessResponse)
async def spotify_callback(
    code: str = Query(..., description="Authorization code from Spotify"),
    state: str | None = Query(None, description="State parameter"),
    session: AsyncSession = Depends(get_session),
):
    """
    Handle Spotify OAuth callback.

    Args:
        code: Authorization code from Spotify
        state: State parameter for CSRF protection
        session: Database session

    Returns:
        Authentication success response with user info

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Exchange code for tokens
        async with SpotifyOAuthClient() as spotify_client:
            token_dict = await spotify_client.fetch_token(code)

        # Get user info from Spotify
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token_dict['access_token']}"}
            response = await client.get("https://api.spotify.com/v1/me", headers=headers)
            response.raise_for_status()
            spotify_user_data = response.json()

        # Create or update user
        user = await AuthService.create_or_update_user(
            session=session,
            spotify_user_id=spotify_user_data["id"],
            email=spotify_user_data.get("email"),
            display_name=spotify_user_data.get("display_name"),
        )

        # Save tokens
        await AuthService.save_tokens(session, user.id, token_dict)
        await session.commit()

        return AuthSuccessResponse(
            message="Successfully authenticated with Spotify",
            user=UserResponse.model_validate(user)
        )

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    user_id: int = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_session),
):
    """
    Logout user by revoking tokens.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        Logout success response

    Raises:
        HTTPException: If logout fails
    """
    revoked = await AuthService.revoke_tokens(session, user_id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tokens found for user"
        )

    await session.commit()

    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: int = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current user information.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    from auth.models import User
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)
