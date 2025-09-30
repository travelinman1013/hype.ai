"""
Authentication Business Logic Services.

Service layer for user authentication and token management.
"""

import logging
from datetime import datetime, timedelta

from shared.exceptions import TokenExpiredError, TokenRefreshError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import OAuthToken, User
from .spotify_client import SpotifyOAuthClient

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication-related operations."""

    @staticmethod
    async def create_or_update_user(
        session: AsyncSession,
        spotify_user_id: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> User:
        """
        Create a new user or update existing one.

        Args:
            session: Database session
            spotify_user_id: Spotify user ID
            email: User email
            display_name: User display name

        Returns:
            User object
        """
        # Check if user exists
        result = await session.execute(
            select(User).where(User.spotify_user_id == spotify_user_id)
        )
        user = result.scalars().first()

        if user:
            # Update existing user
            if email:
                user.email = email
            if display_name:
                user.display_name = display_name
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                spotify_user_id=spotify_user_id,
                email=email,
                display_name=display_name,
            )
            session.add(user)

        await session.flush()
        await session.refresh(user)

        return user

    @staticmethod
    async def save_tokens(
        session: AsyncSession,
        user_id: int,
        token_dict: dict,
    ) -> OAuthToken:
        """
        Save OAuth tokens to database with encryption.

        Args:
            session: Database session
            user_id: User ID
            token_dict: Token dictionary from OAuth provider

        Returns:
            OAuthToken object
        """
        # Delete existing tokens for user
        result = await session.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id)
        )
        existing_tokens = result.scalars().all()
        for token in existing_tokens:
            await session.delete(token)

        # Calculate expires_at
        expires_in = token_dict.get("expires_in", 3600)
        issued_at = datetime.fromtimestamp(token_dict.get("issued_at", datetime.utcnow().timestamp()))
        expires_at = issued_at + timedelta(seconds=expires_in)

        # Create new token record
        oauth_token = OAuthToken(
            user_id=user_id,
            access_token_encrypted=OAuthToken.encrypt_access_token(token_dict["access_token"]),
            refresh_token_encrypted=OAuthToken.encrypt_refresh_token(token_dict["refresh_token"]),
            expires_at=expires_at,
            issued_at=issued_at,
            scope=token_dict.get("scope", ""),
            token_type=token_dict.get("token_type", "Bearer"),
        )

        session.add(oauth_token)
        await session.flush()
        await session.refresh(oauth_token)

        return oauth_token

    @staticmethod
    async def get_user_token(
        session: AsyncSession,
        user_id: int,
    ) -> OAuthToken | None:
        """
        Get user's OAuth token.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            OAuthToken if found, None otherwise
        """
        result = await session.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_valid_access_token(
        session: AsyncSession,
        user_id: int,
    ) -> str:
        """
        Get valid access token for user, refreshing if necessary.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Valid access token string

        Raises:
            TokenExpiredError: If no token found or refresh fails
        """
        # Get user's token
        oauth_token = await AuthService.get_user_token(session, user_id)

        if not oauth_token:
            raise TokenExpiredError("No OAuth token found for user")

        # Decrypt tokens
        access_token = oauth_token.decrypt_access_token()
        refresh_token = oauth_token.decrypt_refresh_token()

        # Check if token needs refresh
        token_dict = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": oauth_token.expires_at.timestamp(),
            "issued_at": oauth_token.issued_at.timestamp(),
            "expires_in": int((oauth_token.expires_at - oauth_token.issued_at).total_seconds()),
        }

        if SpotifyOAuthClient.is_token_expired(token_dict):
            logger.info(f"Token expired for user {user_id}, refreshing...")

            # Refresh token
            async with SpotifyOAuthClient() as spotify_client:
                try:
                    new_token_dict = await spotify_client.refresh_token(refresh_token)

                    # Save new tokens
                    await AuthService.save_tokens(session, user_id, new_token_dict)
                    await session.commit()

                    return new_token_dict["access_token"]

                except Exception as e:
                    logger.error(f"Failed to refresh token for user {user_id}: {e}")
                    raise TokenRefreshError(f"Failed to refresh token: {e}")

        return access_token

    @staticmethod
    async def revoke_tokens(
        session: AsyncSession,
        user_id: int,
    ) -> bool:
        """
        Revoke user's OAuth tokens.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if tokens were revoked, False if no tokens found
        """
        result = await session.execute(
            select(OAuthToken).where(OAuthToken.user_id == user_id)
        )
        tokens = result.scalars().all()

        if not tokens:
            return False

        for token in tokens:
            await session.delete(token)

        await session.flush()

        logger.info(f"Revoked tokens for user {user_id}")
        return True
