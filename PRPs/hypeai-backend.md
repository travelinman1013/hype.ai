name: "HypeAI Backend - Bio-Responsive Music Streaming Service"
description: |
  Complete backend implementation for hype.ai - a fitness application that syncs real-time heart rate
  from Apple HealthKit with Spotify to create bio-responsive workout playlists.

---

## Goal

Build a production-ready FastAPI backend service that:
- Authenticates users with both Spotify and their mobile app (HealthKit proxy)
- Receives real-time heart rate data via WebSocket from mobile frontend
- Maps BPM to workout zones and corresponding Spotify audio features
- Automatically queues appropriate tracks based on current heart rate
- Manages user subscriptions for freemium model (free music sync, paid analytics)
- Handles Spotify API rate limits and token refresh automatically
- Complies with Spotify's commercialization policies (no charging for streaming features)

## Why

- **User Value**: Creates an immersive, adaptive workout experience where music responds to physiological state
- **Market Need**: Fills gap between static workout playlists and truly personalized, real-time music experiences
- **Technical Innovation**: Demonstrates real-time streaming integration between health data and music APIs
- **Business Model**: Freemium approach complies with Spotify policies while monetizing fitness features
- **Scalability**: Designed to handle concurrent connections from many users streaming heart rate data

## What

A modular FastAPI backend with the following user-visible behaviors:

1. **OAuth Flow**: User authenticates with Spotify, grants necessary scopes for playback control
2. **Real-time Streaming**: Mobile app sends continuous heart rate data via WebSocket
3. **Adaptive Music**: System automatically queues tracks matching user's current workout intensity
4. **Seamless Transitions**: Music changes occur at track boundaries, not mid-song
5. **Premium Features**: Subscribers access workout history, heart rate analytics, custom zones

### Success Criteria

- [ ] User can authenticate with Spotify OAuth2 and receive/refresh tokens
- [ ] WebSocket endpoint accepts heart rate data stream (BPM as JSON)
- [ ] Heart rate maps to correct workout zone with configurable thresholds
- [ ] Spotify tracks are queued based on zone's target audio features
- [ ] Rate limiting prevents 429 errors from Spotify API
- [ ] Token refresh happens automatically before expiration
- [ ] Database stores users, tokens, subscriptions, and workout sessions
- [ ] All sensitive data encrypted at rest and in transit
- [ ] API handles 100+ concurrent WebSocket connections without degradation
- [ ] Unit tests pass with 80%+ coverage
- [ ] Integration tests verify end-to-end flows

---

## All Needed Context

### Documentation & References

```yaml
# Spotify Web API - MUST READ
- url: https://developer.spotify.com/documentation/web-api/
  why: Core API reference for all Spotify interactions

- url: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
  section: Authorization Code Flow
  why: OAuth2 implementation for long-running applications
  critical: Access tokens expire in 1 hour - must implement refresh

- url: https://developer.spotify.com/documentation/web-api/reference/add-to-queue
  why: Queue track endpoint - primary playback control method
  critical: URI must be track or episode, not playlist or album

- url: https://developer.spotify.com/documentation/web-api/concepts/rate-limits
  why: Rate limiting is 30-second rolling window, varies by quota mode
  critical: Implement exponential backoff for 429 responses

- url: https://developer.spotify.com/documentation/web-api/reference/get-audio-features
  why: Audio features (tempo, energy, danceability) for zone matching

- url: https://developer.spotify.com/documentation/web-api/concepts/api-calls
  why: Best practices including caching with ETag headers

# FastAPI & WebSockets - MUST READ
- url: https://fastapi.tiangolo.com/
  why: Framework documentation for async patterns

- url: https://fastapi.tiangolo.com/advanced/websockets/
  why: WebSocket implementation for real-time heart rate streaming
  critical: Use ConnectionManager for multiple clients

- url: https://testdriven.io/blog/fastapi-sqlmodel/
  why: FastAPI + SQLModel + Async SQLAlchemy integration pattern
  critical: Use async sessions with proper dependency injection

- url: https://betterstack.com/community/guides/scaling-python/authentication-fastapi/
  why: OAuth2 + JWT implementation patterns for FastAPI

# OAuth2 & Async HTTP - MUST READ
- url: https://docs.authlib.org/en/latest/client/httpx.html
  section: AsyncOAuth2Client
  why: Async OAuth2 with automatic token refresh for httpx
  critical: Use update_token callback to persist refreshed tokens

- url: https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens
  why: Spotify-specific token refresh flow
  critical: Refresh tokens don't expire but can be revoked

# SQLModel & Database - MUST READ
- url: https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/
  why: Dependency injection pattern for database sessions
  critical: Use FastAPI dependencies with yield for proper cleanup

# Apple HealthKit Context - IMPORTANT
- url: https://developer.apple.com/documentation/healthkit/
  why: Understanding HealthKit capabilities and limitations
  critical: HealthKit is LOCAL ONLY - no cloud API exists

- note: |
    HealthKit has NO backend API. Mobile app must stream data to our backend.
    Real-time heart rate only available during active workouts in foreground.
    Alternative: Terra API (https://tryterra.co/integrations/apple-health) for cloud integration.

# Spotify Commercialization Policy - CRITICAL
- url: https://developer.spotify.com/policy
  section: Commercialization
  critical: |
    CANNOT charge for streaming features or show ads in streaming context.
    Our approach: FREE music control, PAID fitness analytics/history.
    This keeps core streaming free while monetizing separate value-add features.

# Existing Codebase Patterns
- file: use-cases/pydantic-ai/examples/main_agent_reference/models.py
  why: Pydantic model patterns with validation and examples
  pattern: Use Field() with descriptions, validation, and Config with json_schema_extra

- file: use-cases/pydantic-ai/examples/main_agent_reference/settings.py
  why: Environment variable management with pydantic-settings
  pattern: Use BaseSettings with Field() and load_dotenv()
```

### Current Codebase Tree

```bash
.
├── CLAUDE.md                    # Project instructions and conventions
├── examples/                    # Currently empty - will add patterns here
│   └── .gitkeep
├── PRPs/
│   └── templates/
│       └── prp_base.md         # This PRP template
├── use-cases/                  # Existing examples (pydantic-ai, agents)
│   ├── pydantic-ai/
│   │   └── examples/
│   │       └── main_agent_reference/
│   │           ├── models.py   # Good Pydantic model examples
│   │           └── settings.py # Environment config pattern
│   └── agent-factory-with-subagents/
│       └── agents/
│           └── rag_agent/
│               ├── requirements.txt
│               └── tests/      # Pytest pattern examples
└── README.md
```

### Desired Codebase Tree

```bash
# First: Create example patterns (as specified in INITIAL.md)
examples/
├── api_client/
│   ├── README.md              # Pattern documentation
│   ├── async_client.py        # Async httpx client with OAuth2
│   ├── token_manager.py       # Token refresh logic
│   └── models.py              # Response validation models
│
└── modular_fastapi/
    ├── README.md              # Modular structure documentation
    ├── main.py                # FastAPI app with routers
    ├── config.py              # Settings with pydantic-settings
    ├── database.py            # SQLModel engine and session
    ├── users/                 # Example domain module
    │   ├── __init__.py
    │   ├── models.py          # SQLModel database models
    │   ├── schemas.py         # Pydantic request/response models
    │   ├── routes.py          # FastAPI router with endpoints
    │   └── services.py        # Business logic layer
    └── tests/
        └── test_users.py      # Pytest examples

# Second: Build hype.ai application using example patterns
src/
└── hypeai/
    ├── __init__.py
    ├── main.py                # FastAPI app initialization
    ├── config.py              # Environment settings
    ├── database.py            # Database engine and session
    │
    ├── shared/                # Shared utilities
    │   ├── __init__.py
    │   ├── exceptions.py      # Custom exception classes
    │   ├── security.py        # Encryption utilities
    │   └── dependencies.py    # Common FastAPI dependencies
    │
    ├── auth/                  # OAuth2 module
    │   ├── __init__.py
    │   ├── models.py          # User, OAuthToken SQLModels
    │   ├── schemas.py         # Login/token request/response
    │   ├── routes.py          # /auth/* endpoints
    │   ├── services.py        # OAuth flow logic
    │   └── spotify_client.py  # Spotify OAuth2 client
    │
    ├── heartrate/             # Heart rate streaming module
    │   ├── __init__.py
    │   ├── models.py          # HeartRateReading SQLModel
    │   ├── schemas.py         # WebSocket message formats
    │   ├── routes.py          # WebSocket endpoint
    │   ├── services.py        # Zone mapping logic
    │   └── connection_manager.py  # WebSocket connection pool
    │
    ├── music/                 # Spotify integration module
    │   ├── __init__.py
    │   ├── models.py          # Track, AudioFeatures models
    │   ├── schemas.py         # Search/queue request/response
    │   ├── routes.py          # /music/* endpoints
    │   ├── services.py        # Zone-to-music mapping
    │   ├── spotify_api.py     # Spotify Web API client
    │   └── rate_limiter.py    # Rate limiting implementation
    │
    ├── users/                 # User management module
    │   ├── __init__.py
    │   ├── models.py          # User, Subscription, WorkoutSession
    │   ├── schemas.py         # User profile, subscription schemas
    │   ├── routes.py          # /users/* endpoints
    │   └── services.py        # User CRUD operations
    │
    └── tests/                 # Test suite
        ├── conftest.py        # Pytest fixtures
        ├── test_auth.py
        ├── test_heartrate.py
        ├── test_music.py
        ├── test_users.py
        └── test_integration.py

# Configuration files
├── .env.example               # Environment variable template
├── .gitignore
├── requirements.txt           # Dependencies
├── pyproject.toml            # Project metadata and tool configs
└── README.md                  # Setup and usage instructions
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Spotify API Token Expiration
# Access tokens expire in 3600 seconds (1 hour)
# MUST check expiration before EVERY API call and refresh if needed
# Refresh tokens don't expire but can be revoked by user

# CRITICAL: Spotify Rate Limiting
# Limit is calculated on 30-second rolling window
# Different limits for development vs extended quota mode
# 429 response includes Retry-After header (in seconds)
# MUST implement exponential backoff with jitter

# CRITICAL: HealthKit is Local Only
# NO cloud API exists for HealthKit data
# Mobile app MUST send data to backend via WebSocket
# Cannot query HealthKit directly from backend server
# Consider Terra API or similar if cloud integration needed

# CRITICAL: FastAPI WebSocket Connection Management
# Use ConnectionManager pattern to track active connections
# Must call await websocket.accept() before receiving data
# Wrap receive/send in try/except to handle disconnections
# Use asyncio.create_task() for concurrent message handling

# CRITICAL: SQLModel Async Sessions
# Use AsyncSession from sqlalchemy.ext.asyncio
# MUST use async with session pattern for proper cleanup
# Use select() from sqlalchemy.future, not session.query()
# Commit/rollback must be explicit in services layer

# CRITICAL: Authlib AsyncOAuth2Client
# update_token parameter can be sync or async function
# Must properly close HTTPX sessions (use context manager)
# Token endpoint must return JSON with access_token, refresh_token
# Some providers return expires_in as string, not int

# CRITICAL: Spotify Queue Behavior
# Queue endpoint adds to queue, doesn't skip current track
# If queue is empty, track plays after current song ends
# Cannot remove items from queue via API
# User can manually skip, affecting queue timing

# IMPORTANT: Python async/await patterns
# Cannot use sync httpx.Client in async functions
# Use httpx.AsyncClient with async with pattern
# SQLAlchemy async requires different imports (AsyncSession, AsyncEngine)
# FastAPI background tasks run after response sent

# IMPORTANT: Pydantic v2 Changes
# Use model_config instead of class Config
# Field validation uses field_validator decorator
# JSON schema is accessed via model_json_schema()
# Use ConfigDict from pydantic instead of Config class

# IMPORTANT: Environment Variables
# Use python-dotenv to load .env file
# Call load_dotenv() before creating Settings instance
# Settings should use pydantic-settings BaseSettings
# Never commit .env files - use .env.example template

# SECURITY: Token Storage
# Store OAuth tokens encrypted in database
# Use environment variable for encryption key (Fernet)
# Never log tokens or include in error messages
# Implement token rotation policy

# SECURITY: WebSocket Authentication
# Require JWT or session token before accepting WebSocket
# Validate token in connection_manager before adding to pool
# Implement heartbeat/ping to detect stale connections
# Rate limit WebSocket message frequency per client
```

---

## Implementation Blueprint

### Data Models and Structure

#### Database Models (SQLModel)

```python
# src/hypeai/auth/models.py
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from cryptography.fernet import Fernet
import os

class User(SQLModel, table=True):
    """User account with Spotify OAuth."""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    spotify_user_id: str = Field(unique=True, index=True)
    email: Optional[str] = None
    display_name: Optional[str] = None

    # Relationships
    tokens: list["OAuthToken"] = Relationship(back_populates="user")
    subscription: Optional["Subscription"] = Relationship(back_populates="user")
    sessions: list["WorkoutSession"] = Relationship(back_populates="user")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OAuthToken(SQLModel, table=True):
    """Encrypted OAuth tokens for Spotify."""
    __tablename__ = "oauth_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Store encrypted with Fernet
    access_token_encrypted: bytes
    refresh_token_encrypted: bytes
    expires_at: datetime

    scope: str  # Comma-separated Spotify scopes
    token_type: str = "Bearer"

    user: User = Relationship(back_populates="tokens")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def decrypt_access_token(self, encryption_key: str) -> str:
        """Decrypt access token using Fernet."""
        cipher = Fernet(encryption_key.encode())
        return cipher.decrypt(self.access_token_encrypted).decode()

    def decrypt_refresh_token(self, encryption_key: str) -> str:
        """Decrypt refresh token using Fernet."""
        cipher = Fernet(encryption_key.encode())
        return cipher.decrypt(self.refresh_token_encrypted).decode()

# src/hypeai/users/models.py
class Subscription(SQLModel, table=True):
    """User subscription for premium features."""
    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)

    tier: str = Field(default="free")  # free, premium
    status: str = Field(default="active")  # active, cancelled, expired

    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    user: User = Relationship(back_populates="subscription")

class WorkoutSession(SQLModel, table=True):
    """Workout session with heart rate data (premium feature)."""
    __tablename__ = "workout_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Statistics
    avg_heart_rate: Optional[float] = None
    max_heart_rate: Optional[int] = None
    duration_minutes: Optional[int] = None

    user: User = Relationship(back_populates="sessions")

# src/hypeai/heartrate/models.py
class HeartRateReading(SQLModel, table=True):
    """Individual heart rate measurement (premium users only)."""
    __tablename__ = "heart_rate_readings"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="workout_sessions.id", index=True)

    bpm: int = Field(ge=30, le=250)  # Reasonable HR range
    zone: str  # warmup, cardio, peak
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### Pydantic Schemas

```python
# src/hypeai/auth/schemas.py
from pydantic import BaseModel, Field, HttpUrl

class SpotifyAuthURL(BaseModel):
    """Response with Spotify authorization URL."""
    auth_url: HttpUrl

class OAuthCallback(BaseModel):
    """OAuth callback query parameters."""
    code: str
    state: Optional[str] = None

class TokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: str

# src/hypeai/heartrate/schemas.py
class HeartRateData(BaseModel):
    """Real-time heart rate data from client."""
    bpm: int = Field(ge=30, le=250, description="Heart rate in beats per minute")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WorkoutZone(BaseModel):
    """Workout zone with thresholds."""
    name: str  # warmup, cardio, peak
    min_bpm: int
    max_bpm: int
    spotify_features: "SpotifyAudioFeatures"

# src/hypeai/music/schemas.py
class SpotifyAudioFeatures(BaseModel):
    """Target audio features for Spotify search."""
    target_tempo: Optional[float] = None  # BPM
    target_energy: Optional[float] = Field(None, ge=0.0, le=1.0)
    target_danceability: Optional[float] = Field(None, ge=0.0, le=1.0)
    target_valence: Optional[float] = Field(None, ge=0.0, le=1.0)

class TrackQueueRequest(BaseModel):
    """Request to queue a track."""
    track_uri: str = Field(pattern=r"^spotify:track:\w+$")
```

### Task List (Implementation Order)

```yaml
# PHASE 1: Foundation & Examples (Required First)
Task 1: Create async API client example pattern
  CREATE examples/api_client/async_client.py:
    - Implement AsyncAPIClient base class using httpx.AsyncClient
    - Add retry decorator with exponential backoff
    - Include error handling pattern with custom exceptions
    - Use async context manager pattern (async with)

  CREATE examples/api_client/token_manager.py:
    - Implement TokenManager with AsyncOAuth2Client from Authlib
    - Add token refresh logic with expiration checking
    - Include update_token callback for persistence
    - Handle edge cases (revoked tokens, network errors)

  CREATE examples/api_client/models.py:
    - Pydantic models for API responses
    - Field validation examples
    - Use Field() with descriptions and constraints

  CREATE examples/api_client/README.md:
    - Document the pattern and when to use it
    - Include code examples and common pitfalls

Task 2: Create modular FastAPI example pattern
  CREATE examples/modular_fastapi/main.py:
    - Initialize FastAPI app with metadata
    - Include routers from domain modules
    - Add middleware (CORS, error handling)
    - Include startup/shutdown events

  CREATE examples/modular_fastapi/config.py:
    - BaseSettings with environment variables
    - Use load_dotenv() pattern
    - Include validation and defaults

  CREATE examples/modular_fastapi/database.py:
    - Async SQLAlchemy engine and session factory
    - Dependency for getting sessions
    - Include session lifecycle management

  CREATE examples/modular_fastapi/users/ module:
    - Complete CRUD example with models, schemas, routes, services
    - Demonstrate separation of concerns
    - Include FastAPI dependencies (get_db, get_current_user)

  CREATE examples/modular_fastapi/README.md:
    - Explain modular architecture benefits
    - Document file responsibilities
    - Include testing approach

# PHASE 2: Core Application Setup
Task 3: Initialize hype.ai project structure
  CREATE src/hypeai/ directory structure:
    - All __init__.py files
    - Basic README.md with setup instructions

  CREATE requirements.txt:
    - fastapi[all]>=0.104.0
    - sqlmodel>=0.0.14
    - uvicorn[standard]>=0.24.0
    - httpx>=0.25.0
    - authlib>=1.3.0
    - python-dotenv>=1.0.0
    - cryptography>=41.0.0
    - pydantic>=2.5.0
    - pydantic-settings>=2.1.0
    - pytest>=7.4.0
    - pytest-asyncio>=0.21.0

  CREATE .env.example:
    - All required environment variables with descriptions
    - Include Spotify client ID/secret placeholders
    - Database URL, encryption key, etc.

  CREATE pyproject.toml:
    - Project metadata
    - Tool configurations (ruff, mypy, pytest)

Task 4: Implement configuration and database
  CREATE src/hypeai/config.py:
    - MIRROR examples/modular_fastapi/config.py pattern
    - Add Spotify-specific settings (client_id, client_secret, redirect_uri)
    - Add encryption_key for token storage
    - Include database_url, secret_key for sessions

  CREATE src/hypeai/database.py:
    - MIRROR examples/modular_fastapi/database.py pattern
    - Async SQLAlchemy engine with SQLModel
    - Session factory with proper cleanup
    - get_session dependency for FastAPI

  CREATE src/hypeai/shared/exceptions.py:
    - Custom exceptions (SpotifyAPIError, TokenExpiredError, etc.)
    - Include HTTP status codes

  CREATE src/hypeai/shared/security.py:
    - Token encryption/decryption helpers using Fernet
    - Use encryption_key from config

# PHASE 3: Authentication Module
Task 5: Implement Spotify OAuth2 client
  CREATE src/hypeai/auth/spotify_client.py:
    - MIRROR examples/api_client/async_client.py pattern
    - Use AsyncOAuth2Client from Authlib
    - Implement authorization_url() method
    - Implement fetch_token(code) method
    - Implement refresh_token() method
    - Add update_token callback to save to database

  CREATE src/hypeai/auth/models.py:
    - User and OAuthToken SQLModels (see Data Models section)
    - Include encryption/decryption methods

Task 6: Implement auth service and routes
  CREATE src/hypeai/auth/schemas.py:
    - Pydantic schemas for auth requests/responses

  CREATE src/hypeai/auth/services.py:
    - create_user(spotify_user_id, email, display_name)
    - save_tokens(user_id, tokens) - with encryption
    - get_valid_token(user_id) - with auto-refresh if expired
    - revoke_tokens(user_id)

  CREATE src/hypeai/auth/routes.py:
    - GET /auth/spotify - returns authorization URL
    - GET /auth/spotify/callback - handles OAuth callback
    - POST /auth/logout - revokes tokens
    - GET /auth/me - returns current user info

# PHASE 4: Heart Rate Streaming Module
Task 7: Implement WebSocket connection manager
  CREATE src/hypeai/heartrate/connection_manager.py:
    - ConnectionManager class to track active WebSocket connections
    - connect(websocket, user_id) - validate auth, add to pool
    - disconnect(websocket) - remove from pool
    - broadcast(message) - send to all connected clients
    - send_personal(message, websocket) - send to specific client
    - Include authentication check before accepting connection

  CREATE src/hypeai/heartrate/schemas.py:
    - HeartRateData Pydantic model
    - WorkoutZone model with thresholds

Task 8: Implement zone mapping service
  CREATE src/hypeai/heartrate/services.py:
    - get_zone_for_bpm(bpm) - maps BPM to workout zone
    - get_spotify_features_for_zone(zone) - returns target audio features
    - PATTERN: Use configurable thresholds from config
    - Default zones:
      * Warmup: 90-110 BPM (tempo: 90-110, energy: 0.3-0.5)
      * Cardio: 111-140 BPM (tempo: 120-140, energy: 0.6-0.8)
      * Peak: 141+ BPM (tempo: 140-180, energy: 0.8-1.0)

  CREATE src/hypeai/heartrate/models.py:
    - HeartRateReading SQLModel (premium feature)

  CREATE src/hypeai/heartrate/routes.py:
    - WebSocket /ws/heartrate - receives BPM stream
    - PATTERN: Accept connection, authenticate, enter receive loop
    - On each message: parse BPM, determine zone, trigger music update
    - Handle disconnections gracefully

# PHASE 5: Spotify Integration Module
Task 9: Implement Spotify Web API client
  CREATE src/hypeai/music/spotify_api.py:
    - MIRROR examples/api_client/async_client.py pattern
    - Use httpx.AsyncClient with retry logic
    - search_tracks(audio_features, limit) - search by features
    - get_audio_features(track_id) - get track features
    - queue_track(track_uri, user_token) - add to queue
    - get_current_playback(user_token) - check playback state
    - CRITICAL: Include token refresh before each request
    - CRITICAL: Handle 429 with exponential backoff using Retry-After header

Task 10: Implement rate limiting
  CREATE src/hypeai/music/rate_limiter.py:
    - RateLimiter class with sliding window algorithm
    - acquire() method - blocks until request allowed
    - Use asyncio.sleep() for async waiting
    - Track requests per user per 30-second window
    - PATTERN: Max 10 requests per 30 seconds per user (conservative)

Task 11: Implement music service and routes
  CREATE src/hypeai/music/services.py:
    - select_track_for_zone(zone, user_id) - finds matching track
    - queue_track_for_user(track_uri, user_id) - queues with rate limit
    - PATTERN: Check if track already queued to avoid duplicates
    - PATTERN: Wait for current song to finish before queuing next

  CREATE src/hypeai/music/schemas.py:
    - SpotifyAudioFeatures Pydantic model
    - TrackQueueRequest Pydantic model

  CREATE src/hypeai/music/routes.py:
    - GET /music/zones - returns zone configuration
    - GET /music/current - returns current playback state
    - POST /music/queue - manually queue a track (testing)

# PHASE 6: User Management Module
Task 12: Implement user service and routes
  CREATE src/hypeai/users/models.py:
    - Subscription and WorkoutSession SQLModels

  CREATE src/hypeai/users/schemas.py:
    - Pydantic schemas for user profile, subscriptions

  CREATE src/hypeai/users/services.py:
    - get_user(user_id)
    - update_subscription(user_id, tier)
    - get_workout_history(user_id) - premium only
    - start_workout_session(user_id)
    - end_workout_session(session_id, statistics)

  CREATE src/hypeai/users/routes.py:
    - GET /users/me - get current user profile
    - GET /users/me/subscription - get subscription details
    - POST /users/me/subscription - update subscription (premium)
    - GET /users/me/workouts - get workout history (premium)

# PHASE 7: Main Application Assembly
Task 13: Create main FastAPI application
  CREATE src/hypeai/main.py:
    - MIRROR examples/modular_fastapi/main.py pattern
    - Initialize FastAPI app with title, version, description
    - Include CORS middleware (allow frontend origins)
    - Include routers from all modules (auth, heartrate, music, users)
    - Add startup event to create database tables
    - Add health check endpoint GET /health

  CREATE src/hypeai/shared/dependencies.py:
    - get_current_user(token: str) - JWT or session validation
    - require_premium(user: User) - dependency for premium endpoints
    - get_db dependency (import from database.py)

# PHASE 8: Testing
Task 14: Implement unit tests for auth module
  CREATE src/hypeai/tests/conftest.py:
    - Pytest fixtures: test_db, test_client, test_user
    - Mock Spotify OAuth responses

  CREATE src/hypeai/tests/test_auth.py:
    - test_spotify_auth_url_generation()
    - test_oauth_callback_success()
    - test_oauth_callback_invalid_code()
    - test_token_refresh_before_expiry()
    - test_token_encryption_decryption()
    - test_logout_revokes_tokens()

Task 15: Implement unit tests for heartrate module
  CREATE src/hypeai/tests/test_heartrate.py:
    - test_websocket_connection_requires_auth()
    - test_heart_rate_parsing()
    - test_bpm_to_zone_mapping()
    - test_zone_threshold_boundaries()
    - test_websocket_disconnection_handling()

Task 16: Implement unit tests for music module
  CREATE src/hypeai/tests/test_music.py:
    - test_spotify_search_with_audio_features()
    - test_track_queuing_with_rate_limit()
    - test_429_error_retry_with_backoff()
    - test_token_refresh_on_401()
    - test_zone_to_audio_features_mapping()

Task 17: Implement integration tests
  CREATE src/hypeai/tests/test_integration.py:
    - test_full_oauth_flow()
    - test_websocket_to_music_queue_flow()
    - test_heart_rate_triggers_zone_change()
    - test_multiple_concurrent_websockets()
    - test_premium_workout_history_storage()

# PHASE 9: Documentation & Deployment Prep
Task 18: Create comprehensive README
  CREATE README.md:
    - Project overview and features
    - Architecture diagram (text-based)
    - Setup instructions (virtual environment, dependencies, .env)
    - Running the application (uvicorn command)
    - API endpoint documentation
    - Testing instructions
    - Spotify commercialization compliance notes
    - Deployment considerations (Uvicorn, concurrent connections)

Task 19: Add database migrations support
  CREATE alembic.ini:
    - Alembic configuration for SQLModel

  CREATE alembic/env.py:
    - Migration environment setup
    - Import all SQLModel models

  RUN: alembic revision --autogenerate -m "Initial schema"
  RUN: alembic upgrade head
```

### Integration Points

```yaml
DATABASE:
  - engine: PostgreSQL or SQLite (async driver)
  - migrations: Alembic with SQLModel metadata
  - connection: Async sessions with dependency injection
  - encryption: Fernet for OAuth tokens at rest

SPOTIFY_API:
  - base_url: https://api.spotify.com/v1
  - auth_url: https://accounts.spotify.com/authorize
  - token_url: https://accounts.spotify.com/api/token
  - scopes: "user-modify-playback-state user-read-playback-state user-read-email"

WEBSOCKET:
  - endpoint: /ws/heartrate
  - authentication: JWT or session token in query parameter or initial message
  - message_format: JSON with {"bpm": int, "timestamp": ISO8601}
  - heartbeat: Client sends ping every 30 seconds, server responds with pong

CONFIG:
  - file: .env (loaded with python-dotenv)
  - settings_class: Settings from pydantic-settings.BaseSettings
  - required_vars:
    * SPOTIFY_CLIENT_ID
    * SPOTIFY_CLIENT_SECRET
    * SPOTIFY_REDIRECT_URI
    * DATABASE_URL
    * ENCRYPTION_KEY (base64-encoded Fernet key)
    * SECRET_KEY (for JWT/sessions)

ROUTES_STRUCTURE:
  - /auth/spotify - GET - OAuth start
  - /auth/spotify/callback - GET - OAuth callback
  - /auth/logout - POST - Revoke tokens
  - /auth/me - GET - Current user
  - /ws/heartrate - WebSocket - Heart rate stream
  - /music/zones - GET - Zone configuration
  - /music/current - GET - Current playback
  - /music/queue - POST - Manual queue (testing)
  - /users/me - GET - User profile
  - /users/me/subscription - GET/POST - Subscription management
  - /users/me/workouts - GET - Workout history (premium)
  - /health - GET - Health check
```

---

## Validation Loop

### Level 1: Syntax & Style

```bash
# BEFORE any testing, ensure code is syntactically correct and follows style

# Check and auto-fix with ruff
ruff check src/hypeai/ examples/ --fix

# Type checking with mypy
mypy src/hypeai/ examples/

# Expected: 0 errors
# If errors: READ the error message, understand the issue, fix code, re-run
# Common issues:
#   - Missing type hints on function signatures
#   - Incorrect async/await usage
#   - SQLModel relationship types
```

### Level 2: Unit Tests

```python
# Run unit tests for each module independently

# Pattern: Test happy path, edge cases, error handling for EACH function/route
# Use pytest.mark.asyncio for async tests
# Mock external API calls (Spotify) using pytest-mock or unittest.mock

# Example tests to include:

# Auth module
def test_token_encryption_decryption():
    """Ensure tokens can be encrypted and decrypted correctly."""
    # Create token, encrypt, store, retrieve, decrypt, verify match

def test_token_refresh_when_expired():
    """Ensure expired tokens trigger refresh automatically."""
    # Mock token with past expiry, call get_valid_token, verify refresh called

# Heart rate module
def test_zone_mapping_boundaries():
    """Ensure BPM at zone boundaries maps correctly."""
    # Test BPM 90, 110, 111, 140, 141, 200

def test_websocket_authentication_required():
    """Ensure unauthenticated connections are rejected."""
    # Connect without token, expect rejection

# Music module
def test_rate_limiter_blocks_excessive_requests():
    """Ensure rate limiter prevents >10 requests per 30 seconds."""
    # Make 11 requests rapidly, verify 11th is delayed

def test_spotify_429_triggers_backoff():
    """Ensure 429 responses trigger exponential backoff."""
    # Mock 429 response with Retry-After, verify backoff logic
```

```bash
# Run all unit tests
pytest src/hypeai/tests/ -v -m "not integration"

# If failing:
#   1. READ the error and traceback carefully
#   2. Identify root cause (logic error, missing mock, async issue)
#   3. Fix code (not test, unless test is actually wrong)
#   4. Re-run until passing
#
# Do NOT mock to pass - fix real issues
# Aim for 80%+ coverage
pytest src/hypeai/tests/ -v -m "not integration" --cov=src/hypeai --cov-report=term-missing
```

### Level 3: Integration Tests

```bash
# Start database (if using PostgreSQL)
docker run -d --name hypeai-db -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

# Run migrations
alembic upgrade head

# Start FastAPI application
uvicorn src.hypeai.main:app --reload --port 8000

# In another terminal, run integration tests
pytest src/hypeai/tests/test_integration.py -v

# Expected: All integration tests pass
# Tests full flows:
#   1. OAuth flow from start to callback to token storage
#   2. WebSocket connection with heart rate streaming
#   3. Heart rate change triggering music queue update
#   4. Rate limiting across multiple requests
#   5. Premium features only accessible to subscribed users
```

### Level 4: Manual Testing

```bash
# Test OAuth flow
# 1. Visit http://localhost:8000/auth/spotify
# 2. Follow redirect to Spotify, authorize
# 3. Verify redirect back with tokens stored

# Test WebSocket
# Use websocat or similar tool
websocat ws://localhost:8000/ws/heartrate?token=YOUR_JWT_TOKEN

# Send heart rate data
{"bpm": 95, "timestamp": "2025-01-15T10:30:00Z"}
{"bpm": 125, "timestamp": "2025-01-15T10:30:30Z"}
{"bpm": 150, "timestamp": "2025-01-15T10:31:00Z"}

# Expected:
#   - First message (95 BPM) maps to "warmup" zone
#   - Second message (125 BPM) maps to "cardio" zone, triggers track queue
#   - Third message (150 BPM) maps to "peak" zone, triggers different track

# Verify in Spotify app that tracks are being queued
```

---

## Final Validation Checklist

- [ ] All unit tests pass: `pytest src/hypeai/tests/ -v -m "not integration" --cov=src/hypeai`
- [ ] Integration tests pass: `pytest src/hypeai/tests/test_integration.py -v`
- [ ] No linting errors: `ruff check src/hypeai/ examples/`
- [ ] No type errors: `mypy src/hypeai/ examples/`
- [ ] OAuth flow works end-to-end manually
- [ ] WebSocket accepts connections and processes heart rate data
- [ ] Heart rate zones trigger appropriate Spotify track queuing
- [ ] Rate limiting prevents 429 errors from Spotify
- [ ] Token refresh happens automatically before expiration
- [ ] Premium features require subscription check
- [ ] Database migrations run successfully
- [ ] README.md is complete with setup and usage instructions
- [ ] .env.example includes all required variables
- [ ] No tokens or secrets in code or logs
- [ ] Application handles 100+ concurrent WebSocket connections
- [ ] Spotify commercialization policy compliance verified (free streaming, paid analytics)

---

## Anti-Patterns to Avoid

- ❌ Don't skip token expiration checks - ALWAYS verify before API calls
- ❌ Don't ignore Spotify rate limits - implement proper backoff with Retry-After
- ❌ Don't store tokens in plain text - ALWAYS encrypt with Fernet
- ❌ Don't use sync httpx.Client - use AsyncClient for FastAPI
- ❌ Don't skip WebSocket authentication - validate before accepting connection
- ❌ Don't queue tracks mid-song - wait for current track to end naturally
- ❌ Don't assume HealthKit has cloud API - mobile app MUST stream data
- ❌ Don't charge for music streaming features - only charge for fitness analytics
- ❌ Don't use session.query() - use select() from sqlalchemy.future for async
- ❌ Don't forget to close HTTPX clients - use async with context manager
- ❌ Don't commit .env files - use .env.example as template
- ❌ Don't mock tests to pass - fix underlying code issues

---

## Success Criteria Summary

**Technical Success:**
- ✅ FastAPI backend with modular architecture
- ✅ OAuth2 integration with Spotify (authorization code flow)
- ✅ WebSocket streaming for real-time heart rate data
- ✅ Zone-based music selection with Spotify audio features
- ✅ Automatic token refresh and rate limiting
- ✅ SQLModel database with encrypted token storage
- ✅ Comprehensive test suite with 80%+ coverage

**Business Success:**
- ✅ Compliant with Spotify commercialization policy
- ✅ Freemium model: free music sync, paid analytics
- ✅ Scalable architecture for concurrent users
- ✅ Secure handling of health and authentication data

**User Experience Success:**
- ✅ Seamless OAuth flow with Spotify
- ✅ Real-time music adaptation to heart rate
- ✅ Smooth track transitions at song boundaries
- ✅ Premium users get workout history and analytics
