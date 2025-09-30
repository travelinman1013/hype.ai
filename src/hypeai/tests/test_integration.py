"""
Integration Tests for HypeAI.

End-to-end tests for complete workflows.
"""

import pytest
from datetime import datetime


class TestEndToEndWorkflow:
    """Test complete user workflows."""

    @pytest.mark.asyncio
    async def test_user_authentication_flow(self, test_session, test_user, test_oauth_token):
        """Test complete user authentication workflow."""
        # User should exist
        assert test_user.id is not None
        assert test_user.spotify_user_id is not None

        # Token should be linked to user
        assert test_oauth_token.user_id == test_user.id

        # Token should be encrypted and decryptable
        decrypted_access = test_oauth_token.decrypt_access_token()
        decrypted_refresh = test_oauth_token.decrypt_refresh_token()

        assert decrypted_access == "test_access_token"
        assert decrypted_refresh == "test_refresh_token"

    @pytest.mark.asyncio
    async def test_workout_session_workflow(
        self,
        test_session,
        test_user,
        test_workout_session,
        test_heart_rate_reading
    ):
        """Test complete workout session workflow."""
        # Session should be created
        assert test_workout_session.id is not None
        assert test_workout_session.user_id == test_user.id
        assert test_workout_session.status == "active"

        # Heart rate reading should be linked to session
        assert test_heart_rate_reading.session_id == test_workout_session.id
        assert test_heart_rate_reading.user_id == test_user.id
        assert test_heart_rate_reading.bpm == 125
        assert test_heart_rate_reading.zone == "cardio"

    @pytest.mark.asyncio
    async def test_subscription_and_user_workflow(
        self,
        test_session,
        test_user,
        test_subscription
    ):
        """Test subscription management workflow."""
        # Subscription should be linked to user
        assert test_subscription.user_id == test_user.id
        assert test_user.subscription.id == test_subscription.id

        # User should be able to have active subscription
        assert test_subscription.status == "active"
        assert test_subscription.tier == "premium"


class TestZoneBasedMusicFlow:
    """Test heart rate zone to music mapping flow."""

    def test_rest_zone_music_features(self):
        """Test music features for rest zone."""
        from heartrate.services import ZoneService

        bpm = 85
        zone = ZoneService.get_zone_for_bpm(bpm)
        features = ZoneService.get_spotify_features_for_zone(zone)

        assert zone == "rest"
        assert features["target_tempo"] == 80
        assert features["target_energy"] == 0.3

    def test_warmup_zone_music_features(self):
        """Test music features for warmup zone."""
        from heartrate.services import ZoneService

        bpm = 100
        zone = ZoneService.get_zone_for_bpm(bpm)
        features = ZoneService.get_spotify_features_for_zone(zone)

        assert zone == "warmup"
        assert features["target_tempo"] == 100
        assert features["target_energy"] == 0.4

    def test_cardio_zone_music_features(self):
        """Test music features for cardio zone."""
        from heartrate.services import ZoneService

        bpm = 125
        zone = ZoneService.get_zone_for_bpm(bpm)
        features = ZoneService.get_spotify_features_for_zone(zone)

        assert zone == "cardio"
        assert features["target_tempo"] == 130
        assert features["target_energy"] == 0.7

    def test_peak_zone_music_features(self):
        """Test music features for peak zone."""
        from heartrate.services import ZoneService

        bpm = 160
        zone = ZoneService.get_zone_for_bpm(bpm)
        features = ZoneService.get_spotify_features_for_zone(zone)

        assert zone == "peak"
        assert features["target_tempo"] == 160
        assert features["target_energy"] == 0.9


class TestDataIntegrity:
    """Test data integrity and constraints."""

    @pytest.mark.asyncio
    async def test_user_must_have_unique_spotify_id(self, test_session, test_user):
        """Test that duplicate Spotify user IDs are prevented."""
        from auth.models import User

        duplicate = User(
            spotify_user_id=test_user.spotify_user_id,
            email="different@example.com"
        )

        test_session.add(duplicate)

        with pytest.raises(Exception):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_oauth_token_requires_user(self, test_session):
        """Test that OAuth token requires valid user reference."""
        from auth.models import OAuthToken
        from datetime import timedelta

        expires_at = datetime.utcnow() + timedelta(hours=1)

        token = OAuthToken(
            user_id=99999,  # Non-existent user
            access_token_encrypted=OAuthToken.encrypt_access_token("token"),
            refresh_token_encrypted=OAuthToken.encrypt_refresh_token("refresh"),
            expires_at=expires_at,
            scope="test",
            token_type="Bearer",
        )

        test_session.add(token)

        with pytest.raises(Exception):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_heart_rate_reading_requires_session(self, test_session, test_user):
        """Test that heart rate reading requires valid session."""
        from heartrate.models import HeartRateReading

        reading = HeartRateReading(
            user_id=test_user.id,
            session_id=99999,  # Non-existent session
            bpm=120,
            zone="cardio",
            timestamp=datetime.utcnow(),
        )

        test_session.add(reading)

        with pytest.raises(Exception):
            await test_session.commit()


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_bpm_values(self):
        """Test zone mapping with invalid BPM values."""
        from heartrate.services import ZoneService

        # Very low BPM
        zone = ZoneService.get_zone_for_bpm(30)
        assert zone == "rest"

        # Very high BPM
        zone = ZoneService.get_zone_for_bpm(250)
        assert zone == "peak"

        # Negative BPM (edge case)
        zone = ZoneService.get_zone_for_bpm(-10)
        assert zone == "rest"

    def test_invalid_zone_name(self):
        """Test Spotify features with invalid zone name."""
        from heartrate.services import ZoneService

        features = ZoneService.get_spotify_features_for_zone("invalid_zone")

        # Should default to cardio
        cardio_features = ZoneService.get_spotify_features_for_zone("cardio")
        assert features == cardio_features

    @pytest.mark.asyncio
    async def test_rate_limiter_with_zero_requests(self):
        """Test rate limiter behavior with edge case parameters."""
        from music.rate_limiter import RateLimiter

        # This tests initialization, actual usage with 0 would block forever
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.max_requests == 1
        assert limiter.window_seconds == 1


class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_openapi_docs_available(self, test_client):
        """Test that OpenAPI documentation is available."""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
