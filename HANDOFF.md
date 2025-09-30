# HypeAI Backend - Development Handoff Document

## 🎯 Project Overview

**Project**: HypeAI - Bio-Responsive Music Streaming Backend
**Status**: MVP Implementation Complete - Ready for Testing & Enhancements
**Technology Stack**: FastAPI, SQLModel, Spotify OAuth2, WebSockets, AsyncIO
**Last Updated**: 2025-09-30

### What This System Does

HypeAI is a backend service that:
1. Authenticates users with Spotify OAuth2
2. Receives real-time heart rate data via WebSocket from a mobile app
3. Maps heart rate (BPM) to workout zones (warmup, cardio, peak)
4. Automatically queues Spotify tracks matching the current workout intensity
5. Manages user subscriptions (free music control, paid workout analytics)

### Business Model Compliance

⚠️ **CRITICAL**: This app complies with Spotify's commercialization policy:
- ✅ Music control features are FREE
- ✅ Only workout analytics/history is PAID
- ❌ Cannot charge for streaming features
- ❌ Cannot show ads during music playback

## 📁 Current Project State

### What's Been Completed ✅

#### Phase 1: Example Patterns (Reference Implementation)
- **`examples/api_client/`** - Async HTTP client pattern with OAuth2 token management
- **`examples/modular_fastapi/`** - Complete modular FastAPI application pattern
- These serve as reference for the coding patterns used throughout the project

#### Phase 2: Core Application Setup
```
src/hypeai/
├── main.py                    # FastAPI app entry point ✅
├── config.py                  # Pydantic Settings for env vars ✅
├── database.py                # Async SQLModel setup ✅
├── requirements.txt           # All dependencies ✅
├── pyproject.toml            # Project config & tool settings ✅
├── .env.example              # Environment variable template ✅
├── .gitignore                # Updated git ignore ✅
└── README.md                 # Comprehensive documentation ✅
```

#### Phase 3: Authentication Module ✅
All files in `src/hypeai/auth/`:
- `spotify_client.py` - OAuth2 client with automatic token refresh
- `models.py` - User & OAuthToken SQLModels with Fernet encryption
- `schemas.py` - Pydantic request/response models
- `services.py` - Business logic (create user, save/refresh tokens)
- `routes.py` - 4 endpoints (get auth URL, callback, logout, get user info)

**Endpoints Implemented:**
- `GET /auth/spotify` - Get Spotify authorization URL
- `GET /auth/spotify/callback` - Handle OAuth callback
- `POST /auth/logout` - Revoke user tokens
- `GET /auth/me` - Get current user info

#### Phase 4: Heart Rate Streaming Module ✅
All files in `src/hypeai/heartrate/`:
- `connection_manager.py` - WebSocket connection pool manager
- `services.py` - Zone mapping logic (BPM → workout zone → audio features)
- `models.py` - HeartRateReading SQLModel
- `routes.py` - WebSocket endpoint

**Endpoint Implemented:**
- `WebSocket /ws/heartrate?user_id=X` - Real-time BPM streaming

**Zone Configuration:**
- Warmup: 90-110 BPM → tempo 100, energy 0.4
- Cardio: 111-140 BPM → tempo 130, energy 0.7
- Peak: 141+ BPM → tempo 160, energy 0.9

#### Phase 5: Spotify Integration Module ✅
All files in `src/hypeai/music/`:
- `spotify_api.py` - Async Spotify Web API client
- `rate_limiter.py` - Sliding window rate limiter (10 req/30s per user)
- `routes.py` - Music control endpoints

**Endpoints Implemented:**
- `GET /music/zones` - Get zone configuration
- `GET /music/current?user_id=X` - Get current playback state
- `POST /music/queue?track_uri=X&user_id=Y` - Queue a track

#### Phase 6: User Management Module ✅
All files in `src/hypeai/users/`:
- `models.py` - Subscription & WorkoutSession SQLModels
- `routes.py` - User profile and subscription endpoints

**Endpoints Implemented:**
- `GET /users/me?user_id=X` - Get user profile
- `GET /users/me/subscription?user_id=X` - Get subscription info
- `GET /users/me/workouts?user_id=X` - Get workout history (premium)

#### Phase 7: Shared Utilities ✅
All files in `src/hypeai/shared/`:
- `exceptions.py` - Custom exception classes (SpotifyAPIError, RateLimitError, etc.)
- `security.py` - Token encryption/decryption with Fernet
- `dependencies.py` - FastAPI dependencies (auth, premium check)

### What's NOT Done ❌

#### Phase 8: Testing (HIGH PRIORITY)
```
src/hypeai/tests/
├── conftest.py               # Pytest fixtures ❌
├── test_auth.py             # Auth module tests ❌
├── test_heartrate.py        # Heart rate module tests ❌
├── test_music.py            # Music module tests ❌
├── test_users.py            # User module tests ❌
└── test_integration.py      # End-to-end tests ❌
```

**Required Test Coverage:**
- Auth: Token encryption, OAuth flow, token refresh
- Heart rate: Zone mapping, WebSocket connection/disconnection
- Music: Rate limiting, Spotify API error handling, track queuing
- Integration: Full OAuth → WebSocket → Music queue flow
- Target: 80%+ code coverage

#### Phase 9: Database Migrations (HIGH PRIORITY)
- Alembic initialization and configuration ❌
- Initial migration for all models ❌
- Migration for any schema changes ❌

#### Additional Enhancements (MEDIUM PRIORITY)
- Production-ready authentication (JWT tokens instead of query params) ❌
- WebSocket authentication validation ❌
- Comprehensive error handling and logging ❌
- API rate limiting (beyond Spotify rate limiting) ❌
- Metrics and monitoring endpoints ❌
- Docker containerization ❌
- CI/CD pipeline ❌

## 🚀 Getting Started (For New Developer)

### Step 1: Environment Setup

```bash
# Navigate to project root
cd /Users/maxwell/LETSGO/Projects/hype.ai/hype.ai

# Activate existing virtual environment
source venv_linux/bin/activate

# Verify dependencies are installed
pip list | grep fastapi  # Should show fastapi 0.118.0+
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Generate encryption key for token storage
python -c "from cryptography.fernet import Fernet; print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}')"

# Generate secret key for sessions
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"

# Edit .env and add:
# 1. The generated keys above
# 2. Spotify credentials from https://developer.spotify.com/dashboard
# 3. Database URL (default SQLite works for development)
```

**Required Environment Variables:**
- `SPOTIFY_CLIENT_ID` - From Spotify Developer Dashboard
- `SPOTIFY_CLIENT_SECRET` - From Spotify Developer Dashboard
- `SPOTIFY_REDIRECT_URI` - Default: http://localhost:8000/auth/spotify/callback
- `ENCRYPTION_KEY` - Generated with Fernet.generate_key()
- `SECRET_KEY` - Generated with secrets.token_urlsafe(32)
- `DATABASE_URL` - Default: sqlite+aiosqlite:///./hypeai.db

### Step 3: Verify Installation

```bash
# Check project structure
ls -la src/hypeai/

# Should see: main.py, config.py, database.py, auth/, heartrate/, music/, users/, shared/

# Verify dependencies
cd src/hypeai
python -c "import fastapi, sqlmodel, httpx, authlib, cryptography; print('All dependencies available')"
```

### Step 4: Run the Application

```bash
# From src/hypeai directory
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running:**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Step 5: Test Basic Functionality

```bash
# Test OAuth flow (in browser)
# Visit: http://localhost:8000/auth/spotify
# Should redirect to Spotify authorization

# Test WebSocket (install websocat first: brew install websocat)
websocat ws://localhost:8000/ws/heartrate?user_id=1
# Type: {"bpm": 125}
# Should receive: {"bpm": 125, "zone": "cardio", "features": {...}, "message": "..."}
```

## 📚 Key Files to Understand

### Critical Files (Read These First)

1. **`CLAUDE.md`** - Project instructions and coding conventions
   - MUST follow these rules (Archon-first, modular patterns, etc.)
   - Contains all coding standards and patterns

2. **`PRPs/hypeai-backend.md`** - Complete project specification
   - Full requirements and success criteria
   - Known gotchas and library quirks
   - Implementation blueprint

3. **`src/hypeai/main.py`** - Application entry point
   - How all modules are wired together
   - Middleware configuration
   - Lifespan management

4. **`src/hypeai/config.py`** - All configuration
   - Environment variables and their defaults
   - Zone thresholds, rate limits, etc.

5. **`src/hypeai/database.py`** - Database setup
   - Async engine configuration
   - Session factory and dependency
   - Model imports for table creation

### Module Entry Points

Each module follows the same pattern:
- `models.py` - Database schema (SQLModel)
- `schemas.py` - API contracts (Pydantic)
- `services.py` - Business logic
- `routes.py` - API endpoints (FastAPI router)

**Read in this order for each module:**
1. `models.py` - Understand data structure
2. `schemas.py` - Understand API contracts
3. `services.py` - Understand business logic
4. `routes.py` - Understand endpoint flow

## 🔧 Development Patterns & Conventions

### Pattern 1: Async Everything

```python
# ✅ CORRECT - Use async
async def get_user(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

# ❌ WRONG - Don't use sync
def get_user(session: Session, user_id: int) -> User:
    return session.query(User).filter(User.id == user_id).first()
```

### Pattern 2: Database Sessions

```python
# ✅ CORRECT - Use dependency injection
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    # session automatically committed/rolled back
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

# ❌ WRONG - Don't create sessions manually
async def get_user(user_id: int):
    async with async_session_maker() as session:
        # This bypasses FastAPI dependency management
        pass
```

### Pattern 3: Token Encryption

```python
# ✅ CORRECT - Always encrypt OAuth tokens
oauth_token = OAuthToken(
    user_id=user.id,
    access_token_encrypted=OAuthToken.encrypt_access_token(token["access_token"]),
    refresh_token_encrypted=OAuthToken.encrypt_refresh_token(token["refresh_token"]),
    expires_at=expires_at,
    # ...
)

# ❌ WRONG - Never store tokens in plain text
oauth_token = OAuthToken(
    user_id=user.id,
    access_token=token["access_token"],  # Plain text!
    # ...
)
```

### Pattern 4: Token Refresh

```python
# ✅ CORRECT - Check expiration before every Spotify API call
access_token = await AuthService.get_valid_access_token(session, user_id)
# This automatically refreshes if needed

# ❌ WRONG - Use token directly without checking expiration
oauth_token = await AuthService.get_user_token(session, user_id)
access_token = oauth_token.decrypt_access_token()  # Might be expired!
```

### Pattern 5: Rate Limiting

```python
# ✅ CORRECT - Acquire rate limit before Spotify API calls
await rate_limiter.acquire(str(user_id))
async with SpotifyAPI(access_token) as spotify:
    await spotify.queue_track(track_uri)

# ❌ WRONG - No rate limiting
async with SpotifyAPI(access_token) as spotify:
    await spotify.queue_track(track_uri)  # Might hit 429 error!
```

## ⚠️ Known Gotchas & Important Warnings

### 1. HealthKit Has No Cloud API

❌ **You CANNOT query HealthKit directly from the backend**
✅ **Mobile app MUST stream data via WebSocket**

The backend has no direct access to HealthKit. All heart rate data comes through the WebSocket endpoint from the mobile app.

### 2. Spotify Token Expiration

⚠️ **Access tokens expire in 1 hour (3600 seconds)**
✅ **Always use `AuthService.get_valid_access_token()` which auto-refreshes**

```python
# This handles expiration checking and refresh
access_token = await AuthService.get_valid_access_token(session, user_id)
```

### 3. Spotify Rate Limiting

⚠️ **30-second rolling window, varies by quota mode**
✅ **Always call `rate_limiter.acquire(user_id)` before Spotify API calls**

The rate limiter is configured for 10 requests per 30 seconds per user (conservative).

### 4. SQLModel Async Queries

❌ **Don't use `.query()`** (old sync API)
✅ **Use `select()` from sqlalchemy**

```python
# ✅ CORRECT
from sqlalchemy import select
result = await session.execute(select(User).where(User.id == user_id))
user = result.scalars().first()

# ❌ WRONG
user = session.query(User).filter(User.id == user_id).first()
```

### 5. WebSocket Authentication

⚠️ **Current implementation uses query parameter for user_id**
🚧 **This is NOT production-ready - needs JWT token validation**

```python
# Current (placeholder):
@router.websocket("/ws/heartrate")
async def websocket_heartrate(
    websocket: WebSocket,
    user_id: str = Query(...)  # ⚠️ Not secure!
):
    pass

# TODO: Implement proper JWT validation:
# 1. Accept token in query param or initial message
# 2. Validate JWT token
# 3. Extract user_id from validated token
```

### 6. Pydantic v2 Syntax

✅ **Use `model_config` instead of `class Config`**
✅ **Use `from_attributes=True` instead of `orm_mode=True`**

```python
# ✅ CORRECT (Pydantic v2)
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ❌ WRONG (Pydantic v1)
class UserResponse(BaseModel):
    class Config:
        orm_mode = True
```

### 7. Spotify Queue Behavior

⚠️ **Queue endpoint adds to queue, doesn't skip current track**
⚠️ **Cannot remove items from queue via API**

The track will play after the current song ends. Users can manually skip.

## 🎯 Immediate Next Steps (Prioritized)

### Priority 1: Get Application Running

**Goal**: Verify the application starts and basic endpoints work

**Tasks**:
1. [ ] Setup `.env` file with all required variables
2. [ ] Run `python src/hypeai/main.py`
3. [ ] Verify health check: `curl http://localhost:8000/health`
4. [ ] Check API docs: http://localhost:8000/docs
5. [ ] Test OAuth flow (visit /auth/spotify in browser)

**Success Criteria**: Application starts without errors, health endpoint returns 200

### Priority 2: Implement Database Migrations

**Goal**: Setup Alembic for database schema management

**Tasks**:
1. [ ] Initialize Alembic: `alembic init alembic`
2. [ ] Update `alembic/env.py` to import SQLModel metadata
3. [ ] Create initial migration: `alembic revision --autogenerate -m "Initial schema"`
4. [ ] Review generated migration
5. [ ] Apply migration: `alembic upgrade head`
6. [ ] Verify tables created: Check database file or run query

**Reference**: See PRP section "Task 19: Add database migrations support"

**Files to Create**:
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment
- `alembic/versions/XXXX_initial_schema.py` - Initial migration

### Priority 3: Implement Unit Tests

**Goal**: Create comprehensive test suite with 80%+ coverage

**Tasks**:
1. [ ] Create `src/hypeai/tests/conftest.py` with fixtures:
   - `test_session` - In-memory database session
   - `test_client` - FastAPI test client
   - `mock_spotify_oauth` - Mock OAuth responses

2. [ ] Create `src/hypeai/tests/test_auth.py`:
   - Test token encryption/decryption
   - Test OAuth callback flow
   - Test token refresh logic
   - Test user creation

3. [ ] Create `src/hypeai/tests/test_heartrate.py`:
   - Test zone mapping (BPM → zone)
   - Test WebSocket connection
   - Test WebSocket message handling
   - Test zone boundary cases

4. [ ] Create `src/hypeai/tests/test_music.py`:
   - Test rate limiter
   - Test Spotify API client
   - Test 429 error handling
   - Test track queuing

5. [ ] Create `src/hypeai/tests/test_users.py`:
   - Test user profile endpoints
   - Test subscription logic
   - Test workout history

6. [ ] Create `src/hypeai/tests/test_integration.py`:
   - Test full OAuth → token storage flow
   - Test WebSocket → zone mapping → music queue flow
   - Test concurrent WebSocket connections

**Run Tests**:
```bash
# Run all tests
pytest src/hypeai/tests/ -v

# Run with coverage
pytest src/hypeai/tests/ -v --cov=src/hypeai --cov-report=term-missing

# Run only unit tests
pytest src/hypeai/tests/ -v -m "not integration"
```

**Reference**: See PRP sections "Task 14-17: Implement tests"

### Priority 4: Implement Production Authentication

**Goal**: Replace query parameter authentication with JWT tokens

**Tasks**:
1. [ ] Add PyJWT to requirements.txt
2. [ ] Create `src/hypeai/shared/jwt.py`:
   - `create_access_token(user_id: str) -> str`
   - `verify_access_token(token: str) -> str` (returns user_id)

3. [ ] Update `src/hypeai/shared/dependencies.py`:
   - Replace `get_current_user_id` with JWT validation
   - Extract token from `Authorization: Bearer <token>` header

4. [ ] Update auth routes to return JWT after OAuth:
   - After successful OAuth, generate JWT token
   - Return JWT token to client

5. [ ] Update WebSocket endpoint:
   - Accept JWT token in query param or initial message
   - Validate token before accepting connection

6. [ ] Update all route examples in README.md

**Security Note**: Use environment variable `SECRET_KEY` for JWT signing

### Priority 5: Enhanced Error Handling

**Goal**: Improve error handling and user feedback

**Tasks**:
1. [ ] Add exception handlers in `main.py`:
   - Handle `SpotifyAPIError` → return 502/503
   - Handle `TokenExpiredError` → return 401 with refresh hint
   - Handle `RateLimitError` → return 429 with Retry-After
   - Handle `ValidationError` → return 422 with field details

2. [ ] Add request logging middleware:
   - Log all requests with timestamp, method, path, status
   - Log errors with full traceback

3. [ ] Improve error messages:
   - Include request_id for tracking
   - Provide actionable error messages
   - Don't leak sensitive information

## 📖 Reference Documentation

### Internal Documentation
- `README.md` - Complete setup and usage guide
- `IMPLEMENTATION_SUMMARY.md` - What's been built and statistics
- `PRPs/hypeai-backend.md` - Full project requirements and specifications
- `CLAUDE.md` - Project conventions and rules (MUST FOLLOW)
- `examples/api_client/README.md` - Async API client pattern
- `examples/modular_fastapi/README.md` - Modular FastAPI pattern

### External Documentation
- **Spotify API**: https://developer.spotify.com/documentation/web-api/
  - OAuth: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
  - Rate Limits: https://developer.spotify.com/documentation/web-api/concepts/rate-limits
  - Queue Track: https://developer.spotify.com/documentation/web-api/reference/add-to-queue

- **FastAPI**: https://fastapi.tiangolo.com/
  - WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
  - Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/

- **SQLModel**: https://sqlmodel.tiangolo.com/
  - Async: https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/

- **Authlib**: https://docs.authlib.org/en/latest/client/httpx.html
  - AsyncOAuth2Client usage

## 🔍 Debugging Tips

### Database Issues

```bash
# Check database tables were created
sqlite3 hypeai.db ".tables"
# Should see: users, oauth_tokens, subscriptions, workout_sessions, heart_rate_readings

# Inspect table schema
sqlite3 hypeai.db ".schema users"

# View data
sqlite3 hypeai.db "SELECT * FROM users;"
```

### OAuth Issues

```bash
# Check Spotify redirect URI matches exactly
# In Spotify Dashboard: Settings → Redirect URIs
# Should include: http://localhost:8000/auth/spotify/callback

# Test authorization URL generation
curl http://localhost:8000/auth/spotify
```

### WebSocket Issues

```bash
# Test WebSocket connection
websocat -v ws://localhost:8000/ws/heartrate?user_id=1

# Send test message
{"bpm": 125}

# Check logs for connection/disconnection messages
```

### Rate Limiting Issues

```python
# Temporarily increase rate limit for testing
# In .env file:
SPOTIFY_RATE_LIMIT_PER_USER=100

# Or modify rate_limiter directly:
# src/hypeai/music/rate_limiter.py
rate_limiter = RateLimiter(max_requests=100)
```

## 📞 Getting Help

### Check These First
1. **Error logs** - Check terminal output for exceptions
2. **API docs** - http://localhost:8000/docs for endpoint details
3. **PRP file** - `PRPs/hypeai-backend.md` has troubleshooting section
4. **Example patterns** - `examples/` directory shows correct patterns

### Common Issues & Solutions

**Issue**: `ENCRYPTION_KEY environment variable is not set`
**Solution**: Generate key with `Fernet.generate_key()` and add to .env

**Issue**: `No module named 'config'`
**Solution**: Run from `src/hypeai/` directory or fix PYTHONPATH

**Issue**: `sqlite3.OperationalError: no such table: users`
**Solution**: Tables aren't created. App should create them on startup, but verify with Alembic migrations

**Issue**: `401 Unauthorized from Spotify`
**Solution**: Token expired. Service should auto-refresh, but check `get_valid_access_token()` is being used

**Issue**: `429 Too Many Requests from Spotify`
**Solution**: Rate limiting not working. Verify `rate_limiter.acquire()` is called before Spotify API calls

## 🎓 Learning Resources

If you need to understand any concepts better:

- **Async Python**: https://realpython.com/async-io-python/
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **SQLModel Tutorial**: https://sqlmodel.tiangolo.com/tutorial/
- **OAuth2 Explained**: https://www.oauth.com/oauth2-servers/access-tokens/
- **WebSockets**: https://websockets.readthedocs.io/en/stable/

## 🚦 Success Criteria

You'll know you're ready to deploy when:

- [ ] All unit tests pass with 80%+ coverage
- [ ] Integration tests pass
- [ ] Manual testing of OAuth flow works end-to-end
- [ ] Manual testing of WebSocket → music queue works
- [ ] No linting errors (`ruff check src/hypeai/`)
- [ ] No type errors (`mypy src/hypeai/`)
- [ ] Database migrations run successfully
- [ ] Application handles 100+ concurrent WebSocket connections
- [ ] Documentation is up to date
- [ ] JWT authentication replaces query param auth
- [ ] All TODO comments in code are addressed

## 📝 Final Notes

This is a solid MVP implementation with:
- ✅ Complete modular architecture
- ✅ All core features implemented
- ✅ Security best practices (token encryption, rate limiting)
- ✅ Async operations throughout
- ✅ Comprehensive documentation

The main gaps are:
- ❌ Test suite
- ❌ Production authentication (JWT)
- ❌ Database migrations
- ❌ Docker deployment

Focus on tests first - they'll help you understand the codebase deeply and catch any issues before moving to production.

**Good luck! The foundation is solid. Build on it with confidence.** 🚀
