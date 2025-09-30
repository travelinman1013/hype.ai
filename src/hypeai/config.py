"""
HypeAI Configuration.

Application settings loaded from environment variables using Pydantic Settings.
"""


from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application Settings
    app_name: str = Field(
        default="HypeAI",
        description="Application name"
    )

    debug: bool = Field(
        default=False,
        description="Debug mode (enables detailed error messages)"
    )

    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )

    # Database Settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./hypeai.db",
        description="Database connection URL"
    )

    # Security Settings
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing tokens and sessions"
    )

    encryption_key: str = Field(
        default="",
        description="Base64-encoded Fernet encryption key for OAuth tokens"
    )

    # Spotify OAuth2 Configuration
    spotify_client_id: str = Field(
        default="",
        description="Spotify OAuth2 client ID"
    )

    spotify_client_secret: str = Field(
        default="",
        description="Spotify OAuth2 client secret"
    )

    spotify_redirect_uri: str = Field(
        default="http://localhost:8000/auth/spotify/callback",
        description="Spotify OAuth2 redirect URI"
    )

    spotify_scopes: str = Field(
        default="user-modify-playback-state user-read-playback-state user-read-email",
        description="Space-separated Spotify OAuth2 scopes"
    )

    # CORS Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # API Settings
    max_page_size: int = Field(
        default=100,
        gt=0,
        le=1000,
        description="Maximum items per page in paginated responses"
    )

    default_page_size: int = Field(
        default=20,
        gt=0,
        le=100,
        description="Default items per page"
    )

    # Rate Limiting
    spotify_rate_limit_per_user: int = Field(
        default=10,
        gt=0,
        description="Maximum Spotify API requests per user per window"
    )

    spotify_rate_limit_window: int = Field(
        default=30,
        gt=0,
        description="Rate limit window in seconds"
    )

    # Token Settings
    token_refresh_buffer_seconds: int = Field(
        default=300,
        gt=0,
        description="Refresh tokens this many seconds before expiry"
    )

    # JWT Settings
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24,  # 24 hours
        gt=0,
        description="JWT access token expiration time in minutes"
    )

    # WebSocket Settings
    websocket_heartbeat_interval: int = Field(
        default=30,
        gt=0,
        description="WebSocket heartbeat interval in seconds"
    )

    # Workout Zone Thresholds (BPM)
    zone_warmup_min: int = Field(
        default=90,
        ge=30,
        le=220,
        description="Minimum BPM for warmup zone"
    )

    zone_warmup_max: int = Field(
        default=110,
        ge=30,
        le=220,
        description="Maximum BPM for warmup zone"
    )

    zone_cardio_min: int = Field(
        default=111,
        ge=30,
        le=220,
        description="Minimum BPM for cardio zone"
    )

    zone_cardio_max: int = Field(
        default=140,
        ge=30,
        le=220,
        description="Maximum BPM for cardio zone"
    )

    zone_peak_min: int = Field(
        default=141,
        ge=30,
        le=220,
        description="Minimum BPM for peak zone"
    )

    zone_peak_max: int = Field(
        default=220,
        ge=30,
        le=250,
        description="Maximum BPM for peak zone"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )


# Create global settings instance
settings = Settings()
