"""Spotify Web API Client."""

import logging

import httpx
from shared.exceptions import RateLimitError, SpotifyAPIError

logger = logging.getLogger(__name__)


class SpotifyAPI:
    """Client for Spotify Web API."""

    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, access_token: str):
        """
        Initialize Spotify API client.

        Args:
            access_token: Spotify access token
        """
        self.access_token = access_token
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()

    async def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and errors."""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                message="Spotify rate limit exceeded",
                retry_after=retry_after
            )

        if response.status_code >= 400:
            raise SpotifyAPIError(
                message=f"Spotify API error: {response.status_code}",
                status_code=response.status_code
            )

        return response.json()

    async def search_tracks(self, query: str, limit: int = 20) -> dict:
        """
        Search for tracks.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            Search results dictionary
        """
        response = await self._client.get(
            "/search",
            params={"q": query, "type": "track", "limit": limit}
        )
        return await self._handle_response(response)

    async def get_audio_features(self, track_id: str) -> dict:
        """
        Get audio features for a track.

        Args:
            track_id: Spotify track ID

        Returns:
            Audio features dictionary
        """
        response = await self._client.get(f"/audio-features/{track_id}")
        return await self._handle_response(response)

    async def queue_track(self, track_uri: str) -> None:
        """
        Add track to user's playback queue.

        Args:
            track_uri: Spotify track URI (e.g., spotify:track:...)
        """
        response = await self._client.post(
            "/me/player/queue",
            params={"uri": track_uri}
        )

        if response.status_code not in (200, 204):
            await self._handle_response(response)

    async def get_current_playback(self) -> dict | None:
        """
        Get user's current playback state.

        Returns:
            Playback state dictionary or None if not playing
        """
        response = await self._client.get("/me/player")

        if response.status_code == 204:
            return None

        return await self._handle_response(response)
