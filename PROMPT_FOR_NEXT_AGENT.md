# 🤖 Prompt for Next Coding Agent

Copy and paste this entire prompt to a fresh coding agent to continue development:

---

## Context

You're continuing development on **HypeAI**, a bio-responsive music streaming backend that syncs real-time heart rate data with Spotify. The MVP is complete but needs testing, migrations, and production-ready authentication.

## Current State

**Location**: `/Users/maxwell/LETSGO/Projects/hype.ai/hype.ai`

**What's Done** ✅:
- Complete FastAPI backend with 4 modules (auth, heartrate, music, users)
- Spotify OAuth2 with automatic token refresh and encryption
- WebSocket endpoint for real-time heart rate streaming
- Heart rate → workout zone → music mapping
- Rate limiting for Spotify API
- All database models (SQLModel)
- 12 API endpoints total
- Comprehensive documentation

**What's NOT Done** ❌:
- Unit tests (Priority 1)
- Database migrations with Alembic (Priority 2)
- Production JWT authentication (Priority 3)
- Docker deployment (Priority 4)

**Tech Stack**: FastAPI, SQLModel, Spotify OAuth2, WebSockets, AsyncIO, Pydantic v2

## Critical Files to Read First

1. **`HANDOFF.md`** - Complete handoff documentation (READ THIS FIRST)
2. **`CLAUDE.md`** - Project rules and conventions (MUST FOLLOW)
3. **`PRPs/hypeai-backend.md`** - Full requirements and specifications
4. **`README.md`** - Setup and usage guide
5. **`IMPLEMENTATION_SUMMARY.md`** - What's been built

## Your First Tasks

### Task 1: Verify Setup (30 minutes)

```bash
# Activate virtual environment
cd /Users/maxwell/LETSGO/Projects/hype.ai/hype.ai
source venv_linux/bin/activate

# Setup environment
cp .env.example .env
# Generate encryption key:
python -c "from cryptography.fernet import Fernet; print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}')"
# Generate secret key:
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"
# Add both to .env along with Spotify credentials

# Run application
cd src/hypeai
python main.py

# Verify it works
curl http://localhost:8000/health  # Should return 200
# Visit http://localhost:8000/docs  # Should show API documentation
```

### Task 2: Implement Database Migrations (1-2 hours)

**Goal**: Setup Alembic for database schema management

**Steps**:
1. Initialize Alembic: `alembic init alembic`
2. Update `alembic/env.py` to import SQLModel.metadata
3. Import all models in env.py:
   ```python
   from auth.models import User, OAuthToken
   from users.models import Subscription, WorkoutSession
   from heartrate.models import HeartRateReading
   target_metadata = SQLModel.metadata
   ```
4. Create migration: `alembic revision --autogenerate -m "Initial schema"`
5. Review and apply: `alembic upgrade head`

**Reference**: See `HANDOFF.md` section "Priority 2: Implement Database Migrations"

### Task 3: Implement Unit Tests (4-6 hours)

**Goal**: Create test suite with 80%+ coverage

**Structure**:
```
src/hypeai/tests/
├── conftest.py           # Fixtures (test_session, test_client, mocks)
├── test_auth.py          # Auth module tests
├── test_heartrate.py     # Heart rate module tests
├── test_music.py         # Music module tests
├── test_users.py         # User module tests
└── test_integration.py   # End-to-end tests
```

**Key Tests to Implement**:
- Token encryption/decryption (auth)
- OAuth flow with mocked Spotify (auth)
- Token auto-refresh (auth)
- BPM → zone mapping, especially boundaries (heartrate)
- WebSocket connection lifecycle (heartrate)
- Rate limiter sliding window (music)
- Spotify API 429 error handling (music)

**Run Tests**:
```bash
pytest src/hypeai/tests/ -v --cov=src/hypeai --cov-report=term-missing
```

**Reference**: See `HANDOFF.md` section "Priority 3: Implement Unit Tests"

### Task 4: Implement JWT Authentication (2-3 hours)

**Goal**: Replace query parameter auth with JWT tokens

**Current State** (insecure):
```python
@router.websocket("/ws/heartrate")
async def websocket_heartrate(
    websocket: WebSocket,
    user_id: str = Query(...)  # ⚠️ Not secure!
):
```

**Target State**:
```python
@router.websocket("/ws/heartrate")
async def websocket_heartrate(
    websocket: WebSocket,
    token: str = Query(...)  # JWT token
):
    # Validate JWT and extract user_id
    user_id = verify_jwt_token(token)
```

**Steps**:
1. Add `PyJWT` to requirements.txt
2. Create `src/hypeai/shared/jwt.py` with create/verify functions
3. Update `shared/dependencies.py` to validate JWT tokens
4. Update auth routes to return JWT after OAuth success
5. Update all routes to use JWT authentication
6. Update README.md with new authentication flow

**Reference**: See `HANDOFF.md` section "Priority 4: Implement Production Authentication"

## Important Rules & Patterns

### MUST Follow These:

1. **ALWAYS use async/await** - No sync operations
2. **ALWAYS use `get_session` dependency** - No manual session creation
3. **ALWAYS encrypt OAuth tokens** - Use `OAuthToken.encrypt_access_token()`
4. **ALWAYS check token expiration** - Use `AuthService.get_valid_access_token()`
5. **ALWAYS apply rate limiting** - Call `rate_limiter.acquire(user_id)` before Spotify API
6. **ALWAYS use `select()` not `.query()`** - For async SQLModel queries

### Common Pitfalls:

❌ **Don't use sync httpx.Client** → ✅ Use `httpx.AsyncClient`
❌ **Don't use session.query()** → ✅ Use `await session.execute(select(...))`
❌ **Don't store tokens in plain text** → ✅ Always encrypt
❌ **Don't forget token refresh** → ✅ Use `get_valid_access_token()`

### Example Patterns:

```python
# ✅ CORRECT async database query
from sqlalchemy import select
result = await session.execute(select(User).where(User.id == user_id))
user = result.scalars().first()

# ✅ CORRECT token refresh
access_token = await AuthService.get_valid_access_token(session, user_id)

# ✅ CORRECT rate limiting
await rate_limiter.acquire(str(user_id))
async with SpotifyAPI(access_token) as spotify:
    await spotify.queue_track(track_uri)
```

## Critical Warnings

⚠️ **HealthKit has NO cloud API** - All heart rate data comes via WebSocket from mobile app
⚠️ **Spotify tokens expire in 1 hour** - Always use auto-refresh service
⚠️ **Spotify rate limit is 30-second rolling window** - Always use rate limiter
⚠️ **Cannot charge for music streaming** - Only charge for workout analytics (Spotify policy)

## Testing Commands

```bash
# Lint code
source venv_linux/bin/activate
ruff check src/hypeai/ --fix

# Type check
mypy src/hypeai/

# Run tests
pytest src/hypeai/tests/ -v --cov=src/hypeai

# Run application
cd src/hypeai && python main.py

# Test WebSocket
websocat ws://localhost:8000/ws/heartrate?user_id=1
# Send: {"bpm": 125}
```

## File Structure Reference

```
src/hypeai/
├── main.py                # FastAPI app entry point
├── config.py              # Pydantic Settings
├── database.py            # Async SQLModel setup
├── auth/                  # Spotify OAuth2 module
│   ├── spotify_client.py  # OAuth client with auto-refresh
│   ├── models.py          # User & encrypted tokens
│   ├── services.py        # Auth business logic
│   ├── schemas.py         # API schemas
│   └── routes.py          # 4 endpoints
├── heartrate/             # Real-time streaming
│   ├── connection_manager.py  # WebSocket manager
│   ├── services.py        # Zone mapping (BPM → music)
│   ├── models.py          # HeartRateReading model
│   └── routes.py          # WebSocket endpoint
├── music/                 # Spotify integration
│   ├── spotify_api.py     # Async Spotify API client
│   ├── rate_limiter.py    # Sliding window rate limiter
│   └── routes.py          # 3 endpoints
├── users/                 # User management
│   ├── models.py          # Subscription & WorkoutSession
│   └── routes.py          # 3 endpoints
└── shared/                # Utilities
    ├── exceptions.py      # Custom exceptions
    ├── security.py        # Token encryption
    └── dependencies.py    # FastAPI dependencies
```

## Questions to Ask Before Starting

1. **Is the virtual environment activated?** (`which python` should show venv_linux path)
2. **Is `.env` configured?** (encryption key, secret key, Spotify credentials)
3. **Can the app start?** (`python src/hypeai/main.py` should run without errors)
4. **Can you access API docs?** (http://localhost:8000/docs should load)
5. **Have you read `HANDOFF.md`?** (This has ALL the details you need)

## Success Criteria

You're done when:
- [ ] All unit tests pass with 80%+ coverage
- [ ] Database migrations work (`alembic upgrade head`)
- [ ] JWT authentication replaces query params
- [ ] Manual OAuth → WebSocket → music queue flow works
- [ ] README.md updated with new auth flow
- [ ] No linting or type errors

## Need Help?

1. **Check `HANDOFF.md`** - Comprehensive troubleshooting guide
2. **Check `PRPs/hypeai-backend.md`** - Full requirements and known issues
3. **Check example patterns** - `examples/` directory shows correct patterns
4. **Check logs** - Terminal output shows detailed errors

## Final Note

The codebase is solid and well-structured. Focus on:
1. Understanding the async patterns (everything is async)
2. Following the module structure (models → schemas → services → routes)
3. Writing comprehensive tests
4. Implementing secure authentication

The foundation is excellent. Build on it with confidence! 🚀

---

**Start by reading `HANDOFF.md` in full, then begin with Task 1 above.**
