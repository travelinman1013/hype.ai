"""
Application Configuration.

Demonstrates Pydantic Settings for environment variable management:
- Type-safe configuration
- Environment variable loading with python-dotenv
- Validation and default values
- Multiple configuration sources
"""


from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be prefixed with APP_ to avoid conflicts.
    Example: APP_DATABASE_URL=sqlite+aiosqlite:///./test.db
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="APP_",
    )

    # Application settings
    app_name: str = Field(
        default="Modular FastAPI Example",
        description="Application name"
    )

    debug: bool = Field(
        default=False,
        description="Debug mode (enables detailed error messages)"
    )

    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./example.db",
        description="Database connection URL"
    )

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Security settings
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing tokens and sessions"
    )

    # API settings
    api_version: str = Field(
        default="v1",
        description="API version"
    )

    max_page_size: int = Field(
        default=100,
        gt=0,
        le=1000,
        description="Maximum items per page in paginated responses"
    )


# Create global settings instance
settings = Settings()
