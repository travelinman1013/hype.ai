"""
Token Manager Example Pattern.

Demonstrates OAuth2 token management with:
- Automatic token refresh before expiration
- Async token persistence callback
- Integration with Authlib's AsyncOAuth2Client
- Thread-safe token operations
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages OAuth2 tokens with automatic refresh.

    Example usage:
        async def save_token(token_dict):
            # Save to database
            await db.save_token(token_dict)

        manager = TokenManager(
            client_id="your_client_id",
            client_secret="your_client_secret",
            token_endpoint="https://api.example.com/oauth/token",
            update_token=save_token
        )

        # Set initial token
        await manager.set_token({
            "access_token": "...",
            "refresh_token": "...",
            "expires_in": 3600,
            "token_type": "Bearer"
        })

        # Get valid token (auto-refreshes if needed)
        token = await manager.get_valid_token()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        update_token: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
        refresh_buffer_seconds: int = 300,
    ):
        """
        Initialize token manager.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_endpoint: OAuth2 token endpoint URL
            update_token: Async callback to persist updated tokens
            refresh_buffer_seconds: Refresh token this many seconds before expiry
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.update_token_callback = update_token
        self.refresh_buffer_seconds = refresh_buffer_seconds

        # Token state
        self._token: dict[str, Any] | None = None
        self._token_lock = asyncio.Lock()

        # OAuth2 client
        self._client: AsyncOAuth2Client | None = None

    async def __aenter__(self):
        """Enter async context manager."""
        self._client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_endpoint=self.token_endpoint,
            update_token=self._update_token_wrapper,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager and cleanup."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _update_token_wrapper(self, token: dict[str, Any], refresh_token: str | None = None, access_token: str | None = None):
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
            except Exception as e:
                logger.error(f"Failed to persist token via callback: {e}")

    async def set_token(self, token: dict[str, Any]):
        """
        Set the current token.

        Args:
            token: Token dictionary with access_token, refresh_token, expires_in, etc.
        """
        async with self._token_lock:
            self._token = token
            if self._client:
                self._client.token = token

    async def get_token(self) -> dict[str, Any] | None:
        """
        Get current token without validation.

        Returns:
            Token dictionary or None if not set
        """
        async with self._token_lock:
            return self._token

    def _is_token_expired(self, token: dict[str, Any]) -> bool:
        """
        Check if token is expired or near expiration.

        Args:
            token: Token dictionary

        Returns:
            True if token is expired or near expiration
        """
        if not token:
            return True

        # Check if expires_at exists (absolute timestamp)
        if "expires_at" in token:
            expires_at = datetime.fromtimestamp(token["expires_at"])
            buffer = timedelta(seconds=self.refresh_buffer_seconds)
            return datetime.now() + buffer >= expires_at

        # Check if expires_in exists (relative seconds)
        if "expires_in" in token:
            # If no issued_at timestamp, assume token was just issued
            issued_at = token.get("issued_at", datetime.now().timestamp())
            expires_at = datetime.fromtimestamp(issued_at + token["expires_in"])
            buffer = timedelta(seconds=self.refresh_buffer_seconds)
            return datetime.now() + buffer >= expires_at

        # If no expiration info, consider expired to force refresh
        return True

    async def refresh_token(self) -> dict[str, Any]:
        """
        Refresh the access token using refresh token.

        Returns:
            New token dictionary

        Raises:
            ValueError: If no refresh token available
            Exception: If refresh fails
        """
        async with self._token_lock:
            if not self._token or "refresh_token" not in self._token:
                raise ValueError("No refresh token available")

            if not self._client:
                raise RuntimeError("Client not initialized. Use 'async with' context manager.")

            refresh_token = self._token["refresh_token"]

            try:
                logger.info("Refreshing access token...")
                new_token = await self._client.refresh_token(
                    self.token_endpoint,
                    refresh_token=refresh_token,
                )

                # Update internal state
                self._token = new_token

                # Call persistence callback
                if self.update_token_callback:
                    try:
                        await self.update_token_callback(new_token)
                    except Exception as e:
                        logger.error(f"Failed to persist refreshed token: {e}")

                logger.info("Successfully refreshed access token")
                return new_token

            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise

    async def get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token string

        Raises:
            ValueError: If no token is set or refresh fails
        """
        async with self._token_lock:
            if not self._token:
                raise ValueError("No token set. Call set_token() first.")

            # Check if token needs refresh
            if self._is_token_expired(self._token):
                logger.info("Token expired or near expiration, refreshing...")
                # Release lock during refresh to avoid deadlock
                self._token_lock.release()
                try:
                    await self.refresh_token()
                finally:
                    await self._token_lock.acquire()

            return self._token["access_token"]

    async def revoke_token(self, revocation_endpoint: str):
        """
        Revoke the current token.

        Args:
            revocation_endpoint: OAuth2 revocation endpoint URL

        Raises:
            ValueError: If no token to revoke
        """
        async with self._token_lock:
            if not self._token:
                raise ValueError("No token to revoke")

            if not self._client:
                raise RuntimeError("Client not initialized. Use 'async with' context manager.")

            try:
                logger.info("Revoking token...")
                await self._client.revoke_token(
                    revocation_endpoint,
                    token=self._token.get("access_token"),
                )

                # Clear internal state
                self._token = None

                logger.info("Successfully revoked token")

            except Exception as e:
                logger.error(f"Failed to revoke token: {e}")
                raise


class OAuthTokenWithRefresh:
    """
    Simple OAuth2 token with automatic refresh for API calls.

    Example usage:
        oauth = OAuthTokenWithRefresh(
            client_id="...",
            client_secret="...",
            token_endpoint="https://api.example.com/oauth/token",
            initial_token={...}
        )

        async with oauth:
            # Will automatically refresh if needed
            headers = await oauth.get_auth_headers()
            # Use headers for API requests
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        initial_token: dict[str, Any],
        update_token: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ):
        """
        Initialize OAuth token manager.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_endpoint: Token endpoint URL
            initial_token: Initial token dictionary
            update_token: Callback to persist updated tokens
        """
        self.manager = TokenManager(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=token_endpoint,
            update_token=update_token,
        )
        self.initial_token = initial_token

    async def __aenter__(self):
        """Enter async context manager."""
        await self.manager.__aenter__()
        await self.manager.set_token(self.initial_token)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.manager.__aexit__(exc_type, exc_val, exc_tb)

    async def get_auth_headers(self) -> dict[str, str]:
        """
        Get authorization headers with valid token.

        Returns:
            Dictionary with Authorization header
        """
        token = await self.manager.get_valid_token()
        return {"Authorization": f"Bearer {token}"}
