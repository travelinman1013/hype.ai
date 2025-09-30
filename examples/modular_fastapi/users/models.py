"""
User Database Models.

Demonstrates SQLModel usage for database models:
- Table definition with SQLModel
- Field constraints and indexes
- Timestamps for audit trails
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User database model."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_premium: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
