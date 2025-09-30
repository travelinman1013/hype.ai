"""
Spotify OAuth2 Client.

Handles Spotify OAuth2 authentication flow with automatic token refresh.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client
from config import settings
from shared.exceptions import TokenExpiredError, TokenRefreshError

logger = logging.getLogger(__name__)


class SpotifyOAuthClient:
    """
    Spotify OAuth2 client with automatic token refresh.

    Handles the complete OAuth2 authorization code flow for Spotify.
    """

    # Spotify OAuth2 endpoints
    AUTHORIZATION_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        scopes: str | None = None,
        update_token_callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ):
        """
        Initialize Spotify OAuth2 client.

        Args:
            client_id: Spotify client ID (defaults to settings)
            client_secret: Spotify client secret (defaults to settings)
            redirect_uri: OAuth redirect URI (defaults to settings)
            scopes: Space-separated OAuth scopes (defaults to settings)
            update_token_callback: Async callback to persist updated tokens
        """
        self.client_id = client_id or settings.spotify_client_id
        self.client_secret = client_secret or settings.spotify_client_secret
        self.redirect_uri = redirect_uri or settings.spotify_redirect_uri
        self.scopes = scopes or settings.spotify_scopes
        self.update_token_callback = update_token_callback

        self._client: AsyncOAuth2Client | None = None
        self._token: dict[str, Any] | None = None

    async def __aenter__(self):
        """Enter async context manager."""
        self._client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_endpoint=self.TOKEN_URL,
            update_token=self._update_token_wrapper,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager and cleanup."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _update_token_wrapper(
        self,
        token: dict[str, Any],
        refresh_token: str | None = None,
        access_token: str | None = None
    ):
        """
        Internal wrapper for update_token callback.

        Args:
            token: Token dictionary from OAuth2 provider
            refresh_token: Refresh token (if provided separately)
            access_token: Access token (if provided separately)
        """
        # Store token internally
        self._token = token

        # Call user-provided callback if exists
        if self.update_token_callback:
            try:
                await self.update_token_callback(token)
                logger.info("Token updated via callback")
            except Exception as e:
                logger.error(f"Failed to persist token via callback: {e}")

    def get_authorization_url(self, state: str | None = None) -> str:
        """
        Get Spotify authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL

        Example:
            >>> client = SpotifyOAuthClient()
            >>> auth_url = client.get_authorization_url(state="random-state")
            >>> # Redirect user to auth_url
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
        }

        if state:
            params["state"] = state

        # Build URL with query parameters
        from urllib.parse import urlencode
        query_string = urlencode(params)
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    async def fetch_token(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token dictionary with access_token, refresh_token, expires_in, etc.

        Raises:
            TokenRefreshError: If token exchange fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.info("Exchanging authorization code for token...")
            token = await self._client.fetch_token(
                self.TOKEN_URL,
                grant_type="authorization_code",
                code=code,
                redirect_uri=self.redirect_uri,
            )

            # Add issued_at timestamp for expiration tracking
            token["issued_at"] = datetime.utcnow().timestamp()

            # Store token internally
            self._token = token

            logger.info("Successfully exchanged code for token")
            return token

        except Exception as e:
            logger.error(f"Failed to fetch token: {e}")
            raise TokenRefreshError(f"Failed to exchange authorization code: {e}")

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token dictionary

        Raises:
            TokenRefreshError: If refresh fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        try:
            logger.info("Refreshing access token...")
            token = await self._client.refresh_token(
                self.TOKEN_URL,
                refresh_token=refresh_token,
            )

            # Add issued_at timestamp
            token["issued_at"] = datetime.utcnow().timestamp()

            # Spotify sometimes doesn't return a new refresh token
            # Keep the old one if not provided
            if "refresh_token" not in token and refresh_token:
                token["refresh_token"] = refresh_token

            # Store token internally
            self._token = token

            # Call persistence callback
            if self.update_token_callback:
                try:
                    await self.update_token_callback(token)
                except Exception as e:
                    logger.error(f"Failed to persist refreshed token: {e}")

            logger.info("Successfully refreshed access token")
            return token

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise TokenRefreshError(f"Failed to refresh token: {e}")

    @staticmethod
    def is_token_expired(token: dict[str, Any], buffer_seconds: int | None = None) -> bool:
        """
        Check if token is expired or near expiration.

        Args:
            token: Token dictionary
            buffer_seconds: Refresh token this many seconds before expiry (defaults to settings)

        Returns:
            True if token is expired or near expiration
        """
        if not token:
            return True

        buffer = buffer_seconds if buffer_seconds is not None else settings.token_refresh_buffer_seconds

        # Check if expires_at exists (absolute timestamp)
        if "expires_at" in token:
            expires_at = datetime.fromtimestamp(token["expires_at"])
            buffer_time = timedelta(seconds=buffer)
            return datetime.utcnow() + buffer_time >= expires_at

        # Check if expires_in and issued_at exist
        if "expires_in" in token and "issued_at" in token:
            issued_at = datetime.fromtimestamp(token["issued_at"])
            expires_at = issued_at + timedelta(seconds=token["expires_in"])
            buffer_time = timedelta(seconds=buffer)
            return datetime.utcnow() + buffer_time >= expires_at

        # If no expiration info, consider expired to force refresh
        return True

    async def get_valid_token(self, current_token: dict[str, Any]) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            current_token: Current token dictionary

        Returns:
            Valid access token string

        Raises:
            TokenExpiredError: If no refresh token available
            TokenRefreshError: If refresh fails
        """
        if not current_token:
            raise TokenExpiredError("No token available")

        # Check if token needs refresh
        if self.is_token_expired(current_token):
            if "refresh_token" not in current_token:
                raise TokenExpiredError("Token expired and no refresh token available")

            logger.info("Token expired or near expiration, refreshing...")
            refreshed_token = await self.refresh_token(current_token["refresh_token"])
            return refreshed_token["access_token"]

        return current_token["access_token"]

    async def revoke_token(self, token: str):
        """
        Revoke an access token.

        Note: Spotify doesn't have a public token revocation endpoint.
        This method is a placeholder for future implementation.

        Args:
            token: Access token to revoke
        """
        logger.warning("Spotify doesn't support token revocation via API")
        # User must revoke access through Spotify account settings
        pass
