"""User Management Database Models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from auth.models import User


class Subscription(SQLModel, table=True):
    """User subscription for premium features."""

    __tablename__ = "subscriptions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    tier: str = Field(default="free", max_length=50)  # free, premium
    status: str = Field(default="active", max_length=50)  # active, cancelled, expired

    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    user: "User" = Relationship(back_populates="subscription")


class WorkoutSession(SQLModel, table=True):
    """Workout session with heart rate data (premium feature)."""

    __tablename__ = "workout_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None

    # Statistics
    avg_heart_rate: float | None = None
    max_heart_rate: int | None = None
    duration_minutes: int | None = None

    user: "User" = Relationship(back_populates="sessions")
