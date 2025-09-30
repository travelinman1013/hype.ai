"""
API Response Models Example Pattern.

Demonstrates Pydantic model best practices for API responses:
- Field validation with constraints
- Type hints and optional fields
- Custom validators
- JSON schema configuration
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class TokenResponse(BaseModel):
    """OAuth2 token response from provider."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1...",
                "refresh_token": "eyJhbGciOiJIUzI1...",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "read write",
            }
        }
    )

    access_token: str = Field(..., description="Access token for API requests")
    refresh_token: str = Field(..., description="Refresh token for getting new access token")
    expires_in: int = Field(..., gt=0, description="Token lifetime in seconds")
    token_type: str = Field(default="Bearer", description="Token type (usually Bearer)")
    scope: str = Field(..., description="Granted scopes as space-separated string")

    @field_validator("token_type")
    @classmethod
    def validate_token_type(cls, v: str) -> str:
        """
        Validate token type is Bearer.

        Args:
            v: Token type value

        Returns:
            Uppercased token type

        Raises:
            ValueError: If token type is not Bearer
        """
        if v.lower() != "bearer":
            raise ValueError("Only Bearer token type is supported")
        return "Bearer"


class APIErrorResponse(BaseModel):
    """Standard API error response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "invalid_request",
                "error_description": "The request is missing a required parameter",
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }
    )

    error: str = Field(..., description="Error code")
    error_description: str = Field(..., description="Human-readable error description")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "has_next": True,
                "has_previous": False,
            }
        }
    )

    items: list = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    @field_validator("items")
    @classmethod
    def validate_items_length(cls, v: list, info) -> list:
        """
        Validate items length doesn't exceed page_size.

        Args:
            v: Items list
            info: Validation context

        Returns:
            Validated items list

        Raises:
            ValueError: If items length exceeds page_size
        """
        page_size = info.data.get("page_size", 0)
        if page_size and len(v) > page_size:
            raise ValueError(f"Items length ({len(v)}) exceeds page_size ({page_size})")
        return v


class UserProfile(BaseModel):
    """Example user profile response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "user123",
                "email": "user@example.com",
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "created_at": "2025-01-01T00:00:00Z",
                "is_premium": True,
            }
        }
    )

    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    display_name: str | None = Field(None, description="User display name")
    avatar_url: HttpUrl | None = Field(None, description="User avatar image URL")
    created_at: datetime = Field(..., description="Account creation timestamp")
    is_premium: bool = Field(default=False, description="Whether user has premium subscription")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Validate email format.

        Args:
            v: Email value

        Returns:
            Validated email

        Raises:
            ValueError: If email format is invalid
        """
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()


class ResourceCreatedResponse(BaseModel):
    """Response for successful resource creation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "resource123",
                "message": "Resource created successfully",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
    )

    id: str = Field(..., description="ID of created resource")
    message: str = Field(default="Resource created successfully", description="Success message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
