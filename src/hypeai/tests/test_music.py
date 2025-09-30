"""
Tests for Music Module.

Tests for rate limiter, Spotify API integration, and music routes.
"""

import asyncio
import time

import pytest

from music.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for Spotify API rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within limit are allowed immediately."""
        limiter = RateLimiter(max_requests=3, window_seconds=10)
        user_id = "user_1"

        start_time = time.time()

        # Make 3 requests (within limit)
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        elapsed = time.time() - start_time

        # Should complete almost instantly (< 0.1 seconds)
        assert elapsed < 0.1
        assert len(limiter.requests[user_id]) == 3

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_limit_exceeded(self):
        """Test that requests are blocked when limit is exceeded."""
        limiter = RateLimiter(max_requests=2, window_seconds=2)
        user_id = "user_2"

        # Make 2 requests (at limit)
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        start_time = time.time()

        # Third request should wait
        await limiter.acquire(user_id)

        elapsed = time.time() - start_time

        # Should have waited approximately window_seconds (2s), allow 0.5s margin
        assert 1.5 <= elapsed <= 2.5

    @pytest.mark.asyncio
    async def test_rate_limiter_sliding_window(self):
        """Test that rate limiter uses sliding window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        user_id = "user_3"

        # Make 2 requests
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        # Wait for 1.1 seconds (past window)
        await asyncio.sleep(1.1)

        start_time = time.time()

        # Next request should not wait (old requests expired)
        await limiter.acquire(user_id)

        elapsed = time.time() - start_time

        # Should complete quickly since old requests are outside window
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_requests(self):
        """Test that old requests are removed from tracking."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        user_id = "user_4"

        # Make 3 requests
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        assert len(limiter.requests[user_id]) == 3

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Make another request (should clean old ones)
        await limiter.acquire(user_id)

        # Should only have 1 request now (old 3 removed)
        assert len(limiter.requests[user_id]) == 1

    @pytest.mark.asyncio
    async def test_rate_limiter_different_users_independent(self):
        """Test that rate limits are independent per user."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        user_1 = "user_5"
        user_2 = "user_6"

        # Exhaust limit for user_1
        await limiter.acquire(user_1)
        await limiter.acquire(user_1)

        # user_2 should still be able to make requests immediately
        start_time = time.time()
        await limiter.acquire(user_2)
        await limiter.acquire(user_2)
        elapsed = time.time() - start_time

        # user_2 requests should not be delayed
        assert elapsed < 0.1

        # Verify tracking
        assert len(limiter.requests[user_1]) == 2
        assert len(limiter.requests[user_2]) == 2

    @pytest.mark.asyncio
    async def test_rate_limiter_default_settings(self):
        """Test rate limiter with default settings from config."""
        limiter = RateLimiter()

        # Should use settings from config
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 30

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter with concurrent requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        user_id = "user_7"

        async def make_request():
            await limiter.acquire(user_id)

        start_time = time.time()

        # Make 5 concurrent requests (within limit)
        await asyncio.gather(*[make_request() for _ in range(5)])

        elapsed = time.time() - start_time

        # All should complete quickly
        assert elapsed < 0.2
        assert len(limiter.requests[user_id]) == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_partial_window_expiry(self):
        """Test that only expired requests are removed."""
        limiter = RateLimiter(max_requests=5, window_seconds=2)
        user_id = "user_8"

        # Make 2 requests
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        # Wait 1 second
        await asyncio.sleep(1.0)

        # Make 2 more requests
        await limiter.acquire(user_id)
        await limiter.acquire(user_id)

        # Should have 4 requests tracked
        assert len(limiter.requests[user_id]) == 4

        # Wait another 1.1 seconds (total 2.1s from first requests)
        await asyncio.sleep(1.1)

        # Make one more request (should remove first 2)
        await limiter.acquire(user_id)

        # Should have 3 requests (removed first 2, kept last 3)
        assert len(limiter.requests[user_id]) == 3


class TestMusicRoutes:
    """Tests for music API routes."""

    @pytest.mark.asyncio
    async def test_search_tracks_no_auth(self, test_client):
        """Test searching tracks without authentication fails."""
        response = test_client.get("/music/search?query=test")

        # Should fail due to missing authentication
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_queue_track_no_auth(self, test_client):
        """Test queueing track without authentication fails."""
        response = test_client.post(
            "/music/queue",
            json={"track_uri": "spotify:track:test123"}
        )

        # Should fail due to missing authentication
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_get_playback_state_no_auth(self, test_client):
        """Test getting playback state without authentication fails."""
        response = test_client.get("/music/playback")

        # Should fail due to missing authentication
        assert response.status_code in [401, 422]


class TestSpotifyAPIIntegration:
    """Integration tests for Spotify API client (with mocking)."""

    @pytest.mark.asyncio
    async def test_spotify_api_rate_limiting(self, mock_spotify_api):
        """Test that Spotify API calls respect rate limiting."""
        from music.spotify_api import SpotifyAPI
        from music.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=2)
        user_id = "test_user"
        access_token = "test_token"

        async def make_api_call():
            await limiter.acquire(user_id)
            async with SpotifyAPI(access_token) as api:
                # Mock API call
                pass

        start_time = time.time()

        # Make 3 calls - third should be rate limited
        await make_api_call()
        await make_api_call()
        await make_api_call()

        elapsed = time.time() - start_time

        # Third call should have waited ~2 seconds
        assert elapsed >= 1.5

    @pytest.mark.asyncio
    async def test_spotify_api_client_context_manager(self):
        """Test SpotifyAPI can be used as async context manager."""
        from music.spotify_api import SpotifyAPI

        access_token = "test_token"

        async with SpotifyAPI(access_token) as api:
            assert api is not None
            assert hasattr(api, '_client')
            assert api._client is not None
