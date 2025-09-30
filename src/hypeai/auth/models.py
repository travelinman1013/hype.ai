"""
Authentication Database Models.

SQLModel models for users and OAuth tokens with encryption support.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from shared.security import TokenEncryption
from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from users.models import Subscription, WorkoutSession


class User(SQLModel, table=True):
    """User account with Spotify OAuth."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    spotify_user_id: str = Field(unique=True, index=True, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)

    # Relationships
    tokens: list["OAuthToken"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    subscription: Optional["Subscription"] = Relationship(back_populates="user")
    sessions: list["WorkoutSession"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OAuthToken(SQLModel, table=True):
    """Encrypted OAuth tokens for Spotify."""

    __tablename__ = "oauth_tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Store encrypted with Fernet
    access_token_encrypted: bytes = Field(sa_column=Column(LargeBinary))
    refresh_token_encrypted: bytes = Field(sa_column=Column(LargeBinary))

    expires_at: datetime
    issued_at: datetime = Field(default_factory=datetime.utcnow)

    scope: str = Field(max_length=500)  # Comma-separated Spotify scopes
    token_type: str = Field(default="Bearer", max_length=50)

    user: User = Relationship(back_populates="tokens")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def decrypt_access_token(self) -> str:
        """
        Decrypt access token using Fernet.

        Returns:
            Decrypted access token string

        Raises:
            ValueError: If decryption fails
        """
        return TokenEncryption.decrypt_token(self.access_token_encrypted)

    def decrypt_refresh_token(self) -> str:
        """
        Decrypt refresh token using Fernet.

        Returns:
            Decrypted refresh token string

        Raises:
            ValueError: If decryption fails
        """
        return TokenEncryption.decrypt_token(self.refresh_token_encrypted)

    @staticmethod
    def encrypt_access_token(token: str) -> bytes:
        """
        Encrypt access token using Fernet.

        Args:
            token: Access token string

        Returns:
            Encrypted token bytes
        """
        return TokenEncryption.encrypt_token(token)

    @staticmethod
    def encrypt_refresh_token(token: str) -> bytes:
        """
        Encrypt refresh token using Fernet.

        Args:
            token: Refresh token string

        Returns:
            Encrypted token bytes
        """
        return TokenEncryption.encrypt_token(token)
