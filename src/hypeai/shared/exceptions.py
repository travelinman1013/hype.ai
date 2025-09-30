"""
Custom Exception Classes.

Defines custom exceptions for different error scenarios in the application.
"""



class HypeAIException(Exception):
    """Base exception for all HypeAI errors."""

    def __init__(self, message: str, status_code: int | None = None):
        """
        Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SpotifyAPIError(HypeAIException):
    """Exception raised for Spotify API errors."""

    def __init__(self, message: str, status_code: int | None = None, retry_after: int | None = None):
        """
        Initialize Spotify API error.

        Args:
            message: Error message
            status_code: HTTP status code from Spotify API
            retry_after: Seconds to wait before retrying (for 429 errors)
        """
        super().__init__(message, status_code)
        self.retry_after = retry_after


class TokenExpiredError(HypeAIException):
    """Exception raised when OAuth token has expired."""

    def __init__(self, message: str = "OAuth token has expired"):
        """
        Initialize token expired error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=401)


class TokenRefreshError(HypeAIException):
    """Exception raised when token refresh fails."""

    def __init__(self, message: str = "Failed to refresh OAuth token"):
        """
        Initialize token refresh error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=401)


class RateLimitError(HypeAIException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class WebSocketError(HypeAIException):
    """Exception raised for WebSocket errors."""

    def __init__(self, message: str):
        """
        Initialize WebSocket error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=None)


class AuthenticationError(HypeAIException):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize authentication error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=401)


class AuthorizationError(HypeAIException):
    """Exception raised for authorization errors."""

    def __init__(self, message: str = "Insufficient permissions"):
        """
        Initialize authorization error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=403)


class ResourceNotFoundError(HypeAIException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str, resource_type: str | None = None, resource_id: str | None = None):
        """
        Initialize resource not found error.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., "User", "Workout")
            resource_id: ID of resource
        """
        super().__init__(message, status_code=404)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(HypeAIException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str | None = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
        """
        super().__init__(message, status_code=422)
        self.field = field


class DatabaseError(HypeAIException):
    """Exception raised for database errors."""

    def __init__(self, message: str = "Database operation failed"):
        """
        Initialize database error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=500)
