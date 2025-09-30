"""Rate Limiter for Spotify API Calls."""

import asyncio
import time
from collections import defaultdict, deque

from config import settings


class RateLimiter:
    """Sliding window rate limiter for API requests."""

    def __init__(self, max_requests: int = None, window_seconds: int = None):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests or settings.spotify_rate_limit_per_user
        self.window_seconds = window_seconds or settings.spotify_rate_limit_window
        self.requests: dict[str, deque] = defaultdict(deque)

    async def acquire(self, user_id: str):
        """
        Acquire rate limit slot, waiting if necessary.

        Args:
            user_id: User identifier for rate limiting
        """
        current_time = time.time()

        # Remove old requests outside window
        while self.requests[user_id] and self.requests[user_id][0] < current_time - self.window_seconds:
            self.requests[user_id].popleft()

        # Wait if at limit
        if len(self.requests[user_id]) >= self.max_requests:
            wait_time = self.requests[user_id][0] + self.window_seconds - current_time
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Recursively check again after waiting
                await self.acquire(user_id)
                return

        # Add current request
        self.requests[user_id].append(current_time)


# Global rate limiter instance
rate_limiter = RateLimiter()
