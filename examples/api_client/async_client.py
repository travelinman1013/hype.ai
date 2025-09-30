"""
Async API Client Example Pattern.

Demonstrates best practices for building async HTTP clients with:
- Retry logic with exponential backoff
- Error handling with custom exceptions
- Context manager pattern for proper cleanup
- Rate limiting and timeout handling
"""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import httpx
from httpx import AsyncClient, Response

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Response | None = None):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if available
            response: HTTP response object if available
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None, **kwargs):
        """
        Initialize rate limit error.

        Args:
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments for APIError
        """
        self.retry_after = retry_after
        super().__init__(**kwargs)


class TokenExpiredError(APIError):
    """Exception raised when authentication token has expired."""

    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (httpx.RequestError, httpx.TimeoutException),
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise

                    # Add jitter to prevent thundering herd
                    jitter = asyncio.sleep(delay * 0.1 * asyncio.get_running_loop().time() % 1)
                    sleep_time = min(delay + jitter, max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {sleep_time:.2f}s. Error: {e}"
                    )

                    await asyncio.sleep(sleep_time)
                    delay *= exponential_base

        return wrapper

    return decorator


class AsyncAPIClient:
    """
    Base async HTTP client with retry logic and error handling.

    Example usage:
        async with AsyncAPIClient(base_url="https://api.example.com") as client:
            response = await client.get("/endpoint")
            data = response.json()
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
    ):
        """
        Initialize async API client.

        Args:
            base_url: Base URL for all API requests
            timeout: Request timeout in seconds
            headers: Default headers for all requests
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = headers or {}
        self._client: AsyncClient | None = None

    async def __aenter__(self):
        """Enter async context manager."""
        self._client = AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.default_headers,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager and cleanup."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> AsyncClient:
        """
        Ensure client is initialized.

        Returns:
            AsyncClient instance

        Raises:
            RuntimeError: If client is not initialized (not in context manager)
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    def _handle_response(self, response: Response) -> Response:
        """
        Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Response object if successful

        Raises:
            TokenExpiredError: If 401 Unauthorized
            RateLimitError: If 429 Too Many Requests
            APIError: For other error responses
        """
        if response.status_code == 401:
            raise TokenExpiredError(
                message="Authentication token expired or invalid",
                status_code=401,
                response=response,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(
                message="Rate limit exceeded",
                status_code=429,
                response=response,
                retry_after=retry_seconds,
            )

        if not response.is_success:
            raise APIError(
                message=f"API request failed: {response.status_code} {response.reason_phrase}",
                status_code=response.status_code,
                response=response,
            )

        return response

    @retry_with_backoff(max_retries=3)
    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Perform GET request with retry logic.

        Args:
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            headers: Additional headers for this request

        Returns:
            HTTP response object

        Raises:
            APIError: If request fails after all retries
        """
        client = self._ensure_client()
        response = await client.get(endpoint, params=params, headers=headers)
        return self._handle_response(response)

    @retry_with_backoff(max_retries=3)
    async def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Perform POST request with retry logic.

        Args:
            endpoint: API endpoint (relative to base_url)
            json: JSON body
            data: Form data
            headers: Additional headers for this request

        Returns:
            HTTP response object

        Raises:
            APIError: If request fails after all retries
        """
        client = self._ensure_client()
        response = await client.post(endpoint, json=json, data=data, headers=headers)
        return self._handle_response(response)

    @retry_with_backoff(max_retries=3)
    async def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Perform PUT request with retry logic.

        Args:
            endpoint: API endpoint (relative to base_url)
            json: JSON body
            headers: Additional headers for this request

        Returns:
            HTTP response object

        Raises:
            APIError: If request fails after all retries
        """
        client = self._ensure_client()
        response = await client.put(endpoint, json=json, headers=headers)
        return self._handle_response(response)

    @retry_with_backoff(max_retries=3)
    async def delete(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Perform DELETE request with retry logic.

        Args:
            endpoint: API endpoint (relative to base_url)
            headers: Additional headers for this request

        Returns:
            HTTP response object

        Raises:
            APIError: If request fails after all retries
        """
        client = self._ensure_client()
        response = await client.delete(endpoint, headers=headers)
        return self._handle_response(response)
