"""
Database Configuration.

Async database setup with SQLModel for HypeAI application.
"""

from collections.abc import AsyncGenerator

from config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables():
    """
    Create all database tables.

    Should be called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLModel
        from auth.models import OAuthToken, User  # noqa: F401
        from heartrate.models import HeartRateReading  # noqa: F401
        from users.models import Subscription, WorkoutSession  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.

    Yields:
        AsyncSession instance

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            users = result.scalars().all()
            return users
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
