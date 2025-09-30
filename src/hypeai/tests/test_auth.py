"""
Tests for Authentication Module.

Tests for OAuth flow, token encryption/decryption, and token refresh.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from auth.models import User, OAuthToken
from auth.services import AuthService
from shared.security import TokenEncryption


class TestTokenEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_decrypt_token(self):
        """Test encrypting and decrypting a token."""
        original_token = "test_access_token_12345"

        # Encrypt
        encrypted = TokenEncryption.encrypt_token(original_token)
        assert isinstance(encrypted, bytes)
        assert encrypted != original_token.encode()

        # Decrypt
        decrypted = TokenEncryption.decrypt_token(encrypted)
        assert decrypted == original_token

    def test_oauth_token_encrypt_access_token(self):
        """Test OAuthToken static encrypt method."""
        token = "test_token"
        encrypted = OAuthToken.encrypt_access_token(token)

        assert isinstance(encrypted, bytes)
        assert TokenEncryption.decrypt_token(encrypted) == token

    def test_oauth_token_decrypt_access_token(self, test_oauth_token):
        """Test OAuthToken instance decrypt method."""
        decrypted = test_oauth_token.decrypt_access_token()
        assert decrypted == "test_access_token"

    def test_oauth_token_decrypt_refresh_token(self, test_oauth_token):
        """Test OAuthToken refresh token decryption."""
        decrypted = test_oauth_token.decrypt_refresh_token()
        assert decrypted == "test_refresh_token"

    def test_encryption_with_different_tokens(self):
        """Test that different tokens produce different encrypted values."""
        token1 = "token_one"
        token2 = "token_two"

        encrypted1 = TokenEncryption.encrypt_token(token1)
        encrypted2 = TokenEncryption.encrypt_token(token2)

        assert encrypted1 != encrypted2


class TestOAuthToken:
    """Tests for OAuthToken model."""

    @pytest.mark.asyncio
    async def test_create_oauth_token(self, test_session, test_user):
        """Test creating an OAuth token."""
        expires_at = datetime.utcnow() + timedelta(hours=1)

        token = OAuthToken(
            user_id=test_user.id,
            access_token_encrypted=OAuthToken.encrypt_access_token("new_access_token"),
            refresh_token_encrypted=OAuthToken.encrypt_refresh_token("new_refresh_token"),
            expires_at=expires_at,
            scope="user-modify-playback-state",
            token_type="Bearer",
        )

        test_session.add(token)
        await test_session.commit()
        await test_session.refresh(token)

        assert token.id is not None
        assert token.user_id == test_user.id
        assert token.decrypt_access_token() == "new_access_token"
        assert token.decrypt_refresh_token() == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_oauth_token_relationship_with_user(self, test_oauth_token, test_user):
        """Test OAuth token relationship with user."""
        assert test_oauth_token.user.id == test_user.id
        assert test_oauth_token in test_user.tokens


class TestUser:
    """Tests for User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Test creating a user."""
        user = User(
            spotify_user_id="new_spotify_user_456",
            email="newuser@example.com",
            display_name="New User",
        )

        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        assert user.id is not None
        assert user.spotify_user_id == "new_spotify_user_456"
        assert user.email == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_user_unique_spotify_id(self, test_session, test_user):
        """Test that spotify_user_id must be unique."""
        duplicate_user = User(
            spotify_user_id=test_user.spotify_user_id,
            email="different@example.com",
        )

        test_session.add(duplicate_user)

        with pytest.raises(Exception):  # Should raise IntegrityError
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_user_cascade_delete_tokens(self, test_session, test_user, test_oauth_token):
        """Test that deleting user cascades to tokens."""
        user_id = test_user.id
        token_id = test_oauth_token.id

        # Delete user
        await test_session.delete(test_user)
        await test_session.commit()

        # Verify token is also deleted
        result = await test_session.execute(
            select(OAuthToken).where(OAuthToken.id == token_id)
        )
        deleted_token = result.scalars().first()
        assert deleted_token is None


class TestAuthService:
    """Tests for AuthService business logic."""

    @pytest.mark.asyncio
    async def test_get_user_by_spotify_id(self, test_session, test_user):
        """Test retrieving user by Spotify user ID."""
        user = await AuthService.get_user_by_spotify_id(
            test_session,
            test_user.spotify_user_id
        )

        assert user is not None
        assert user.id == test_user.id
        assert user.spotify_user_id == test_user.spotify_user_id

    @pytest.mark.asyncio
    async def test_get_user_by_spotify_id_not_found(self, test_session):
        """Test retrieving non-existent user returns None."""
        user = await AuthService.get_user_by_spotify_id(
            test_session,
            "nonexistent_spotify_id"
        )

        assert user is None

    @pytest.mark.asyncio
    async def test_create_or_update_user_new_user(self, test_session):
        """Test creating a new user."""
        user_data = {
            "id": "spotify_user_789",
            "email": "create@example.com",
            "display_name": "Created User",
        }

        user = await AuthService.create_or_update_user(test_session, user_data)

        assert user.id is not None
        assert user.spotify_user_id == "spotify_user_789"
        assert user.email == "create@example.com"
        assert user.display_name == "Created User"

    @pytest.mark.asyncio
    async def test_create_or_update_user_existing_user(self, test_session, test_user):
        """Test updating an existing user."""
        user_data = {
            "id": test_user.spotify_user_id,
            "email": "updated@example.com",
            "display_name": "Updated User",
        }

        updated_user = await AuthService.create_or_update_user(test_session, user_data)

        assert updated_user.id == test_user.id
        assert updated_user.email == "updated@example.com"
        assert updated_user.display_name == "Updated User"

    @pytest.mark.asyncio
    async def test_save_tokens(self, test_session, test_user):
        """Test saving OAuth tokens."""
        token_data = {
            "access_token": "new_access_token_123",
            "refresh_token": "new_refresh_token_123",
            "expires_in": 3600,
            "scope": "user-modify-playback-state",
            "token_type": "Bearer",
        }

        token = await AuthService.save_tokens(test_session, test_user.id, token_data)

        assert token.id is not None
        assert token.user_id == test_user.id
        assert token.decrypt_access_token() == "new_access_token_123"
        assert token.decrypt_refresh_token() == "new_refresh_token_123"
        assert token.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_get_latest_token(self, test_session, test_user, test_oauth_token):
        """Test retrieving latest OAuth token for user."""
        token = await AuthService.get_latest_token(test_session, test_user.id)

        assert token is not None
        assert token.id == test_oauth_token.id
        assert token.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_latest_token_not_found(self, test_session):
        """Test retrieving token for user with no tokens."""
        token = await AuthService.get_latest_token(test_session, 99999)

        assert token is None

    @pytest.mark.asyncio
    async def test_is_token_expired_not_expired(self, test_oauth_token):
        """Test checking if token is not expired."""
        is_expired = AuthService.is_token_expired(test_oauth_token)
        assert is_expired is False

    @pytest.mark.asyncio
    async def test_is_token_expired_expired(self, expired_oauth_token):
        """Test checking if token is expired."""
        is_expired = AuthService.is_token_expired(expired_oauth_token)
        assert is_expired is True

    @pytest.mark.asyncio
    async def test_is_token_expired_with_buffer(self, test_session, test_user):
        """Test token expiration check with buffer time."""
        # Create token expiring in 2 minutes
        expires_at = datetime.utcnow() + timedelta(minutes=2)

        token = OAuthToken(
            user_id=test_user.id,
            access_token_encrypted=OAuthToken.encrypt_access_token("expiring_soon"),
            refresh_token_encrypted=OAuthToken.encrypt_refresh_token("refresh"),
            expires_at=expires_at,
            scope="user-modify-playback-state",
            token_type="Bearer",
        )

        test_session.add(token)
        await test_session.commit()

        # With 5 minute buffer (300 seconds), should be considered expired
        is_expired = AuthService.is_token_expired(token, buffer_seconds=300)
        assert is_expired is True

        # With no buffer, should not be expired
        is_expired = AuthService.is_token_expired(token, buffer_seconds=0)
        assert is_expired is False


class TestAuthRoutes:
    """Tests for authentication API routes."""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_spotify_login_redirect(self, test_client):
        """Test Spotify login redirects to authorization URL."""
        response = test_client.get("/auth/spotify/login", follow_redirects=False)

        assert response.status_code == 307
        assert "Location" in response.headers
        assert "accounts.spotify.com/authorize" in response.headers["Location"]

    @pytest.mark.asyncio
    async def test_spotify_callback_error(self, test_client):
        """Test Spotify callback with error parameter."""
        response = test_client.get(
            "/auth/spotify/callback?error=access_denied"
        )

        assert response.status_code == 400
        assert "error" in response.json()["detail"].lower()
