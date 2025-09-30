"""
Unit tests for JWT authentication functionality.

Tests token creation, verification, and error handling.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from config import settings
from fastapi import HTTPException
from shared.jwt import create_access_token, get_user_id_from_token, verify_access_token


class TestJWTTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_with_user_id(self):
        """Test creating JWT token with user ID."""
        user_id = 123
        email = "test@example.com"

        token = create_access_token(user_id=user_id, email=email)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_without_email(self):
        """Test creating JWT token without email."""
        user_id = 456

        token = create_access_token(user_id=user_id)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == str(user_id)
        assert payload["email"] is None

    def test_token_expiration_time(self):
        """Test that token has correct expiration time."""
        user_id = 789

        before_creation = datetime.now(timezone.utc)
        token = create_access_token(user_id=user_id)
        after_creation = datetime.now(timezone.utc)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = before_creation + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

        # Verify expiration is within reasonable range (accounting for test execution time)
        assert exp_time > expected_exp - timedelta(seconds=5)
        assert exp_time < after_creation + timedelta(
            minutes=settings.jwt_access_token_expire_minutes + 1
        )


class TestJWTTokenVerification:
    """Tests for JWT token verification."""

    def test_verify_valid_token(self):
        """Test verifying a valid JWT token."""
        user_id = 123
        email = "test@example.com"

        token = create_access_token(user_id=user_id, email=email)
        payload = verify_access_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["email"] == email

    def test_verify_expired_token(self):
        """Test that expired token raises HTTPException."""
        # Create token that expires immediately
        with patch("shared.jwt.settings.jwt_access_token_expire_minutes", -1):
            token = create_access_token(user_id=123)

        # Wait a moment to ensure expiration
        time.sleep(0.1)

        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_invalid_token(self):
        """Test that invalid token raises HTTPException."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_token_with_wrong_secret(self):
        """Test that token signed with wrong secret fails verification."""
        # Create token with different secret
        payload = {
            "sub": "123",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        wrong_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(wrong_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_with_wrong_algorithm(self):
        """Test that token with wrong algorithm fails verification."""
        # Create token with different algorithm
        payload = {
            "sub": "123",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        wrong_token = jwt.encode(payload, settings.secret_key, algorithm="HS512")

        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(wrong_token)

        assert exc_info.value.status_code == 401


class TestGetUserIdFromToken:
    """Tests for extracting user ID from JWT token."""

    def test_get_user_id_from_valid_token(self):
        """Test extracting user ID from valid token."""
        user_id = 123
        token = create_access_token(user_id=user_id)

        extracted_id = get_user_id_from_token(token)

        assert extracted_id == user_id
        assert isinstance(extracted_id, int)

    def test_get_user_id_from_token_without_subject(self):
        """Test that token without subject raises HTTPException."""
        # Create token without 'sub' field
        payload = {
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            get_user_id_from_token(token)

        assert exc_info.value.status_code == 401
        assert "missing user id" in exc_info.value.detail.lower()

    def test_get_user_id_from_token_with_invalid_subject(self):
        """Test that token with non-numeric subject raises HTTPException."""
        # Create token with non-numeric subject
        payload = {
            "sub": "not-a-number",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            get_user_id_from_token(token)

        assert exc_info.value.status_code == 401
        assert "malformed" in exc_info.value.detail.lower()

    def test_get_user_id_from_expired_token(self):
        """Test that expired token raises HTTPException."""
        with patch("shared.jwt.settings.jwt_access_token_expire_minutes", -1):
            token = create_access_token(user_id=123)

        time.sleep(0.1)

        with pytest.raises(HTTPException) as exc_info:
            get_user_id_from_token(token)

        assert exc_info.value.status_code == 401


class TestJWTIntegration:
    """Integration tests for JWT authentication flow."""

    def test_full_token_lifecycle(self):
        """Test complete token creation and verification lifecycle."""
        # Create token
        user_id = 42
        email = "integration@test.com"
        token = create_access_token(user_id=user_id, email=email)

        # Verify token
        payload = verify_access_token(token)
        assert payload["sub"] == str(user_id)

        # Extract user ID
        extracted_id = get_user_id_from_token(token)
        assert extracted_id == user_id

    def test_multiple_tokens_for_different_users(self):
        """Test creating tokens for multiple users."""
        users = [
            (1, "user1@example.com"),
            (2, "user2@example.com"),
            (3, None),
        ]

        tokens = []
        for user_id, email in users:
            token = create_access_token(user_id=user_id, email=email)
            tokens.append(token)

            # Verify each token independently
            extracted_id = get_user_id_from_token(token)
            assert extracted_id == user_id

        # Verify all tokens are unique
        assert len(set(tokens)) == len(tokens)
