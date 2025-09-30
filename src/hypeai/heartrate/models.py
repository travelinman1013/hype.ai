"""Heart Rate Database Models."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class HeartRateReading(SQLModel, table=True):
    """Individual heart rate measurement (premium users only)."""

    __tablename__ = "heart_rate_readings"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="workout_sessions.id", index=True)

    bpm: int = Field(ge=30, le=250)  # Reasonable HR range
    zone: str = Field(max_length=50)  # warmup, cardio, peak
    timestamp: datetime = Field(default_factory=datetime.utcnow)
