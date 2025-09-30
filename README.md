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

The project includes production-ready Docker configuration with multi-stage builds and PostgreSQL.

#### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

#### Quick Start with Docker Compose

**1. Configure Environment:**

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your Spotify credentials and generate secure keys
```

**2. Generate Security Keys:**

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**3. Start Services:**

```bash
# Build and start all services (API + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f api

# Check service health
docker-compose ps
```

**4. Run Database Migrations:**

```bash
# Run migrations inside the container
docker-compose exec api alembic upgrade head
```

**5. Access the Application:**

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Adminer (Dev): http://localhost:8080 (with `--profile dev`)

#### Docker Compose Services

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| **api** | FastAPI application | 8000 | `/health` endpoint |
| **postgres** | PostgreSQL 16 database | 5432 | pg_isready |
| **adminer** | Database UI (dev only) | 8080 | HTTP check |

#### Docker Commands

**Development Mode:**

```bash
# Start with development tools (includes Adminer)
docker-compose --profile dev up -d

# Hot-reload enabled (code changes auto-restart)
docker-compose logs -f api

# Execute commands in container
docker-compose exec api python -m pytest
docker-compose exec api alembic revision --autogenerate -m "Migration name"
```

**Production Mode:**

```bash
# Start without development tools
docker-compose up -d

# Run with multiple workers
docker-compose up -d --scale api=4

# View resource usage
docker stats
```

**Maintenance:**

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild after code changes
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f          # All services
docker-compose logs -f api      # Just API
docker-compose logs -f postgres # Just database
```

#### Docker Environment Variables

Key environment variables for Docker deployment (see `.env.example`):

```bash
# Application
APP_NAME=HypeAI
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (automatically used by docker-compose)
POSTGRES_DB=hypeai
POSTGRES_USER=hypeai_user
POSTGRES_PASSWORD=changeme_secure_password
DATABASE_URL=postgresql+asyncpg://hypeai_user:changeme_secure_password@postgres:5432/hypeai

# Security (CRITICAL: Generate unique values!)
SECRET_KEY=<generate-unique-key>
ENCRYPTION_KEY=<generate-unique-key>

# Spotify OAuth
SPOTIFY_CLIENT_ID=<your-client-id>
SPOTIFY_CLIENT_SECRET=<your-client-secret>
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/spotify/callback

# Docker Ports
API_PORT=8000
ADMINER_PORT=8080
```

#### Database Migrations with Docker

```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "Add new field"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history

# View current version
docker-compose exec api alembic current
```

#### Production Deployment Checklist

- [ ] Generate unique `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Use strong PostgreSQL password
- [ ] Configure CORS for production domain
- [ ] Set proper `SPOTIFY_REDIRECT_URI` for production
- [ ] Enable HTTPS/TLS termination (use reverse proxy)
- [ ] Set up database backups
- [ ] Configure logging aggregation
- [ ] Set up monitoring and alerts
- [ ] Review and adjust resource limits

#### Dockerfile Details

The multi-stage Dockerfile optimizes for:

- **Build Stage**: Installs dependencies with build tools
- **Production Stage**: Minimal runtime image with only required packages
- **Security**: Runs as non-root user (`appuser`)
- **Health Checks**: Built-in health monitoring
- **Layer Caching**: Optimized for fast rebuilds

#### Troubleshooting Docker

**API won't start:**

```bash
# Check logs for errors
docker-compose logs api

# Verify environment variables
docker-compose exec api env | grep -E "DATABASE_URL|SECRET_KEY"

# Check database connection
docker-compose exec api python -c "from database import engine; import asyncio; asyncio.run(engine.connect())"
```

**Database connection issues:**

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U hypeai_user -d hypeai -c "SELECT version();"
```

**Port conflicts:**

```bash
# Change ports in .env file
API_PORT=8001
POSTGRES_PORT=5433
ADMINER_PORT=8081

# Restart services
docker-compose down && docker-compose up -d
```

#### Advanced: Custom Docker Configuration

**Custom Dockerfile:**

The included `Dockerfile` uses multi-stage builds for optimal image size:

```dockerfile
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder
# ... dependency installation

# Stage 2: Runtime - Copy only what's needed
FROM python:3.11-slim
# ... minimal runtime setup
```

**Custom docker-compose.yml:**

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  api:
    volumes:
      # Mount local code for development
      - ./src/hypeai:/app/src/hypeai:ro
    environment:
      DEBUG: "true"
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
