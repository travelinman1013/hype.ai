# HypeAI - Bio-Responsive Music Streaming Service

A FastAPI backend service that syncs real-time heart rate data from Apple HealthKit with Spotify to create adaptive workout playlists. Music automatically adjusts to your workout intensity based on your physiological state.

## Features

- **Spotify OAuth2 Integration**: Secure authentication with automatic token refresh
- **Real-time Heart Rate Streaming**: WebSocket endpoint for continuous BPM data from mobile app
- **Adaptive Music Selection**: Automatically queues tracks based on workout zones (warmup, cardio, peak)
- **Rate Limiting**: Prevents Spotify API 429 errors with sliding window rate limiter
- **Freemium Model**: Free music control, paid workout analytics (Spotify policy compliant)
- **Secure Token Storage**: Encrypted OAuth tokens using Fernet encryption
- **Modular Architecture**: Clean separation of concerns across auth, heartrate, music, and user modules

## Architecture

```
src/hypeai/
├── main.py                 # FastAPI app initialization
├── config.py               # Environment settings
├── database.py             # Async SQLModel database setup
├── auth/                   # Spotify OAuth2 module
│   ├── models.py           # User & OAuthToken models
│   ├── schemas.py          # API request/response schemas
│   ├── services.py         # Auth business logic
│   ├── routes.py           # Auth endpoints
│   └── spotify_client.py   # Spotify OAuth2 client
├── heartrate/              # Heart rate streaming module
│   ├── models.py           # HeartRateReading model
│   ├── services.py         # Zone mapping logic
│   ├── routes.py           # WebSocket endpoint
│   └── connection_manager.py # WebSocket connection pool
├── music/                  # Spotify integration module
│   ├── spotify_api.py      # Spotify Web API client
│   ├── rate_limiter.py     # Rate limiting implementation
│   └── routes.py           # Music endpoints
├── users/                  # User management module
│   ├── models.py           # Subscription & WorkoutSession models
│   └── routes.py           # User endpoints
└── shared/                 # Shared utilities
    ├── exceptions.py       # Custom exception classes
    ├── security.py         # Token encryption utilities
    └── dependencies.py     # FastAPI dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- Spotify Developer Account with registered app
- SQLite (for development) or PostgreSQL (for production)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd hype.ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Spotify credentials:

```bash
# Get these from https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to ENCRYPTION_KEY
ENCRYPTION_KEY=your_generated_key_here

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to SECRET_KEY
SECRET_KEY=your_generated_secret_here
```

### 5. Run the Application

```bash
cd src/hypeai
python main.py
```

Or with uvicorn directly:

```bash
uvicorn src.hypeai.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/spotify` | Get Spotify authorization URL |
| GET | `/auth/spotify/callback` | Handle OAuth callback |
| POST | `/auth/logout` | Revoke user tokens |
| GET | `/auth/me` | Get current user info |

### Heart Rate Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| WebSocket | `/ws/heartrate?user_id=X` | Stream heart rate data |

**WebSocket Message Format:**
```json
{
  "bpm": 125,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "bpm": 125,
  "zone": "cardio",
  "features": {
    "target_tempo": 130,
    "target_energy": 0.7,
    "target_danceability": 0.7,
    "target_valence": 0.7
  },
  "message": "Heart rate 125 BPM mapped to cardio zone"
}
```

### Music

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/music/zones` | Get zone configuration |
| GET | `/music/current?user_id=X` | Get current playback |
| POST | `/music/queue?track_uri=X&user_id=Y` | Queue a track (testing) |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me?user_id=X` | Get user profile |
| GET | `/users/me/subscription?user_id=X` | Get subscription |
| GET | `/users/me/workouts?user_id=X` | Get workout history |

## Workout Zones

Heart rate is mapped to workout zones with corresponding Spotify audio features:

| Zone | BPM Range | Tempo | Energy | Description |
|------|-----------|-------|--------|-------------|
| **Warmup** | 90-110 | 100 | 0.4 | Low-intensity warm-up |
| **Cardio** | 111-140 | 130 | 0.7 | Moderate cardio workout |
| **Peak** | 141+ | 160 | 0.9 | High-intensity peak effort |

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest src/hypeai/tests/ -v

# Run with coverage
pytest src/hypeai/tests/ -v --cov=src/hypeai --cov-report=term-missing

# Run only unit tests (skip integration)
pytest src/hypeai/tests/ -v -m "not integration"
```

### Code Quality

```bash
# Lint with ruff
ruff check src/hypeai/ examples/ --fix

# Type check with mypy
mypy src/hypeai/ examples/

# Format with black
black src/hypeai/ examples/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing the Application

### 1. Test OAuth Flow

```bash
# Get authorization URL
curl http://localhost:8000/auth/spotify
# Visit the auth_url in browser and authorize

# Handle callback (will be automatic redirect)
# User will be created and tokens stored
```

### 2. Test WebSocket Connection

Using `websocat` or similar tool:

```bash
websocat ws://localhost:8000/ws/heartrate?user_id=1

# Send heart rate data
{"bpm": 95}
{"bpm": 125}
{"bpm": 155}

# Observe zone changes
```

### 3. Test Music Endpoints

```bash
# Get zone configuration
curl http://localhost:8000/music/zones

# Get current playback
curl "http://localhost:8000/music/current?user_id=1"

# Queue a track (get track URI from Spotify)
curl -X POST "http://localhost:8000/music/queue?track_uri=spotify:track:TRACK_ID&user_id=1"
```

## Spotify Commercialization Compliance

This application complies with Spotify's commercialization policy:

- ✅ **Music Control**: FREE - Users control their own Spotify playback
- ✅ **Analytics**: PAID - Workout history and heart rate analytics require premium subscription
- ❌ **No Streaming Charges**: We don't charge for music streaming features
- ❌ **No Ads**: No ads shown during music playback

The freemium model monetizes fitness features, not music access.

## Security Considerations

- **Token Encryption**: All OAuth tokens encrypted at rest using Fernet
- **HTTPS Required**: Use HTTPS in production for all endpoints
- **Rate Limiting**: Prevents abuse and API quota exhaustion
- **WebSocket Authentication**: Require token validation before accepting connections
- **Environment Variables**: Never commit `.env` files with secrets

## Known Limitations

- **HealthKit is Local Only**: No cloud API exists. Mobile app must stream data via WebSocket
- **Spotify Rate Limits**: 30-second rolling window, varies by quota mode
- **Token Refresh**: Access tokens expire in 1 hour, automatic refresh implemented
- **Queue Behavior**: Spotify API adds to queue, doesn't skip current track

## Production Deployment

### Environment Variables

Ensure all production settings are configured:

```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/hypeai
ENCRYPTION_KEY=<production-key>
SECRET_KEY=<production-secret>
SPOTIFY_REDIRECT_URI=https://yourdomain.com/auth/spotify/callback
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Database

Use PostgreSQL for production:

```bash
# Install PostgreSQL driver
pip install asyncpg

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hypeai
```

### Running with Uvicorn

```bash
uvicorn src.hypeai.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/hypeai /app/src/hypeai
COPY .env /app/.env

CMD ["uvicorn", "src.hypeai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Follow the modular architecture patterns in `examples/`
2. Write tests for all new features
3. Maintain 80%+ test coverage
4. Use type hints everywhere
5. Follow PEP 8 and project conventions in `CLAUDE.md`

## License

[Your License Here]

## Support

- **Issues**: https://github.com/yourorg/hypeai/issues
- **Documentation**: https://docs.yourdomain.com
- **Spotify API**: https://developer.spotify.com/documentation/web-api/
