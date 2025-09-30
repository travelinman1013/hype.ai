"""
Pytest Fixtures for HypeAI Tests.

Shared fixtures for database sessions, test clients, and mocked services.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from cryptography.fernet import Fernet

# Set up test settings BEFORE any other imports
encryption_key = Fernet.generate_key().decode()
from config import Settings
test_settings_instance = Settings(
    database_url="sqlite+aiosqlite:///:memory:",
    debug=True,
    environment="testing",
    secret_key="test-secret-key",
    encryption_key=encryption_key,
    spotify_client_id="test_client_id",
    spotify_client_secret="test_client_secret",
    spotify_redirect_uri="http://localhost:8000/auth/spotify/callback",
    spotify_scopes="user-modify-playback-state user-read-playback-state user-read-email",
    spotify_rate_limit_per_user=10,
    spotify_rate_limit_window=30,
)

# Patch settings BEFORE importing other modules
import config
config.settings = test_settings_instance

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from auth.models import OAuthToken, User
from database import get_session
from heartrate.models import HeartRateReading
from main import app
from users.models import Subscription, WorkoutSession


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    Yields:
        Event loop instance
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Get test settings instance.

    Returns:
        Settings instance for testing
    """
    return test_settings_instance


@pytest.fixture
async def test_engine(test_settings: Settings):
    """
    Create async test database engine.

    Args:
        test_settings: Test settings fixture

    Yields:
        Async engine instance
    """
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async test database session.

    Args:
        test_engine: Test engine fixture

    Yields:
        Async session instance
    """
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_session(test_session: AsyncSession):
    """
    Override FastAPI get_session dependency.

    Args:
        test_session: Test session fixture

    Returns:
        Dependency override function
    """
    async def _override_get_session():
        yield test_session

    return _override_get_session


@pytest.fixture
def test_client(override_get_session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with overridden dependencies.

    Args:
        override_get_session: Session override fixture

    Yields:
        TestClient instance
    """
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_test_client(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client for WebSocket testing.

    Args:
        override_get_session: Session override fixture

    Yields:
        AsyncClient instance
    """
    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """
    Create test user.

    Args:
        test_session: Test session fixture

    Returns:
        User instance
    """
    user = User(
        spotify_user_id="test_spotify_user_123",
        email="test@example.com",
        display_name="Test User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_oauth_token(test_session: AsyncSession, test_user: User) -> OAuthToken:
    """
    Create test OAuth token.

    Args:
        test_session: Test session fixture
        test_user: Test user fixture

    Returns:
        OAuthToken instance
    """
    expires_at = datetime.utcnow() + timedelta(hours=1)

    token = OAuthToken(
        user_id=test_user.id,
        access_token_encrypted=OAuthToken.encrypt_access_token("test_access_token"),
        refresh_token_encrypted=OAuthToken.encrypt_refresh_token("test_refresh_token"),
        expires_at=expires_at,
        scope="user-modify-playback-state user-read-playback-state",
        token_type="Bearer",
    )

    test_session.add(token)
    await test_session.commit()
    await test_session.refresh(token)
    return token


@pytest.fixture
async def expired_oauth_token(test_session: AsyncSession, test_user: User) -> OAuthToken:
    """
    Create expired OAuth token for testing refresh logic.

    Args:
        test_session: Test session fixture
        test_user: Test user fixture

    Returns:
        Expired OAuthToken instance
    """
    expires_at = datetime.utcnow() - timedelta(hours=1)

    token = OAuthToken(
        user_id=test_user.id,
        access_token_encrypted=OAuthToken.encrypt_access_token("expired_access_token"),
        refresh_token_encrypted=OAuthToken.encrypt_refresh_token("test_refresh_token"),
        expires_at=expires_at,
        scope="user-modify-playback-state",
        token_type="Bearer",
    )

    test_session.add(token)
    await test_session.commit()
    await test_session.refresh(token)
    return token


@pytest.fixture
async def test_subscription(test_session: AsyncSession, test_user: User) -> Subscription:
    """
    Create test subscription.

    Args:
        test_session: Test session fixture
        test_user: Test user fixture

    Returns:
        Subscription instance
    """
    subscription = Subscription(
        user_id=test_user.id,
        tier="premium",
        status="active",
        started_at=datetime.utcnow(),
    )

    test_session.add(subscription)
    await test_session.commit()
    await test_session.refresh(subscription)
    return subscription


@pytest.fixture
async def test_workout_session(test_session: AsyncSession, test_user: User) -> WorkoutSession:
    """
    Create test workout session.

    Args:
        test_session: Test session fixture
        test_user: Test user fixture

    Returns:
        WorkoutSession instance
    """
    session = WorkoutSession(
        user_id=test_user.id,
        started_at=datetime.utcnow(),
        status="active",
    )

    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)
    return session


@pytest.fixture
async def test_heart_rate_reading(
    test_session: AsyncSession,
    test_user: User,
    test_workout_session: WorkoutSession,
) -> HeartRateReading:
    """
    Create test heart rate reading.

    Args:
        test_session: Test session fixture
        test_user: Test user fixture
        test_workout_session: Test workout session fixture

    Returns:
        HeartRateReading instance
    """
    reading = HeartRateReading(
        user_id=test_user.id,
        session_id=test_workout_session.id,
        bpm=125,
        zone="cardio",
        timestamp=datetime.utcnow(),
    )

    test_session.add(reading)
    await test_session.commit()
    await test_session.refresh(reading)
    return reading


@pytest.fixture
def mock_spotify_api():
    """
    Mock Spotify API responses using respx.

    Returns:
        respx.MockRouter instance
    """
    with respx.mock:
        # Mock token endpoint
        respx.post("https://accounts.spotify.com/api/token").mock(
            return_value={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
                "scope": "user-modify-playback-state",
                "token_type": "Bearer",
            }
        )

        # Mock user profile endpoint
        respx.get("https://api.spotify.com/v1/me").mock(
            return_value={
                "id": "test_spotify_user_123",
                "email": "test@example.com",
                "display_name": "Test User",
            }
        )

        # Mock queue endpoint
        respx.post("https://api.spotify.com/v1/me/player/queue").mock(
            return_value=None,
            status_code=204,
        )

        # Mock playback state endpoint
        respx.get("https://api.spotify.com/v1/me/player").mock(
            return_value={
                "is_playing": True,
                "item": {
                    "id": "test_track_id",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                },
            }
        )

        # Mock search endpoint
        respx.get("https://api.spotify.com/v1/search").mock(
            return_value={
                "tracks": {
                    "items": [
                        {
                            "uri": "spotify:track:test123",
                            "name": "Test Track",
                            "artists": [{"name": "Test Artist"}],
                        }
                    ]
                }
            }
        )

        yield respx


@pytest.fixture
def mock_spotify_client():
    """
    Create mock Spotify OAuth client.

    Returns:
        Mock SpotifyOAuthClient
    """
    mock_client = AsyncMock()
    mock_client.get_authorization_url.return_value = "https://accounts.spotify.com/authorize?..."
    mock_client.fetch_token = AsyncMock(return_value={
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "scope": "user-modify-playback-state",
        "token_type": "Bearer",
    })
    mock_client.refresh_token = AsyncMock(return_value={
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    })
    return mock_client
