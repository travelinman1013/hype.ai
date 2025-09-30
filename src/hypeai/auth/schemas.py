"""
Authentication Request/Response Schemas.

Pydantic models for authentication-related API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SpotifyAuthURL(BaseModel):
    """Response with Spotify authorization URL."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "auth_url": "https://accounts.spotify.com/authorize?client_id=...",
                "state": "random-state-string",
            }
        }
    )

    auth_url: HttpUrl = Field(..., description="Spotify authorization URL")
    state: str | None = Field(None, description="State parameter for CSRF protection")


class OAuthCallback(BaseModel):
    """OAuth callback query parameters."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "AQBx7H...",
                "state": "random-state-string",
            }
        }
    )

    code: str = Field(..., description="Authorization code from Spotify")
    state: str | None = Field(None, description="State parameter for CSRF protection")


class TokenResponse(BaseModel):
    """OAuth token response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "BQD4k...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "user-modify-playback-state user-read-playback-state user-read-email",
            }
        }
    )

    access_token: str = Field(..., description="Access token for Spotify API")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., gt=0, description="Token lifetime in seconds")
    scope: str = Field(..., description="Granted scopes")


class UserResponse(BaseModel):
    """User profile response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "spotify_user_id": "spotify_user_123",
                "email": "user@example.com",
                "display_name": "John Doe",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
    )

    id: int = Field(..., description="User ID")
    spotify_user_id: str = Field(..., description="Spotify user ID")
    email: str | None = Field(None, description="User email")
    display_name: str | None = Field(None, description="User display name")
    created_at: datetime = Field(..., description="Account creation timestamp")


class AuthSuccessResponse(BaseModel):
    """Successful authentication response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Successfully authenticated with Spotify",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "user": {
                    "id": 1,
                    "spotify_user_id": "spotify_user_123",
                    "email": "user@example.com",
                    "display_name": "John Doe",
                    "created_at": "2025-01-15T10:30:00Z",
                },
            }
        }
    )

    message: str = Field(default="Successfully authenticated", description="Success message")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")


class LogoutResponse(BaseModel):
    """Logout response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Successfully logged out",
            }
        }
    )

    message: str = Field(default="Successfully logged out", description="Success message")
