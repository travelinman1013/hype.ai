"""
User Request/Response Schemas.

Demonstrates Pydantic models for API contracts:
- Separation of database models and API schemas
- Request validation
- Response serialization
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
            }
        }
    )

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    full_name: str | None = Field(None, max_length=255, description="User's full name")


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Updated Doe",
                "is_active": True,
            }
        }
    )

    full_name: str | None = Field(None, max_length=255, description="User's full name")
    is_active: bool | None = Field(None, description="Whether user is active")


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_premium": False,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        }
    )

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: str | None = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether user is active")
    is_premium: bool = Field(..., description="Whether user has premium subscription")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "username": "user1",
                        "full_name": "User One",
                        "is_active": True,
                        "is_premium": False,
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T10:30:00Z",
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20,
            }
        }
    )

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., ge=0, description="Total number of users")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
