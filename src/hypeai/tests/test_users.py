"""
Tests for Users Module.

Tests for subscriptions, workout sessions, and user CRUD operations.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from users.models import Subscription, WorkoutSession


class TestSubscription:
    """Tests for Subscription model."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, test_session, test_user):
        """Test creating a subscription."""
        subscription = Subscription(
            user_id=test_user.id,
            tier="premium",
            status="active",
            started_at=datetime.utcnow(),
        )

        test_session.add(subscription)
        await test_session.commit()
        await test_session.refresh(subscription)

        assert subscription.id is not None
        assert subscription.user_id == test_user.id
        assert subscription.tier == "premium"
        assert subscription.status == "active"

    @pytest.mark.asyncio
    async def test_subscription_relationship_with_user(self, test_subscription, test_user):
        """Test subscription relationship with user."""
        assert test_subscription.user.id == test_user.id
        assert test_user.subscription.id == test_subscription.id

    @pytest.mark.asyncio
    async def test_subscription_tiers(self, test_session, test_user):
        """Test different subscription tiers."""
        tiers = ["free", "premium", "pro"]

        for tier in tiers:
            subscription = Subscription(
                user_id=test_user.id,
                tier=tier,
                status="active",
                started_at=datetime.utcnow(),
            )
            test_session.add(subscription)
            await test_session.commit()
            await test_session.refresh(subscription)

            assert subscription.tier == tier

            # Clean up for next iteration
            await test_session.delete(subscription)
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_subscription_status_transitions(self, test_session, test_user):
        """Test subscription status changes."""
        subscription = Subscription(
            user_id=test_user.id,
            tier="premium",
            status="active",
            started_at=datetime.utcnow(),
        )

        test_session.add(subscription)
        await test_session.commit()

        # Test status transitions
        statuses = ["active", "cancelled", "expired"]
        for status in statuses:
            subscription.status = status
            await test_session.commit()
            await test_session.refresh(subscription)
            assert subscription.status == status

    @pytest.mark.asyncio
    async def test_subscription_with_end_date(self, test_session, test_user):
        """Test subscription with end date."""
        ended_at = datetime.utcnow() + timedelta(days=30)

        subscription = Subscription(
            user_id=test_user.id,
            tier="premium",
            status="active",
            started_at=datetime.utcnow(),
            ended_at=ended_at,
        )

        test_session.add(subscription)
        await test_session.commit()
        await test_session.refresh(subscription)

        assert subscription.ended_at is not None
        assert subscription.ended_at == ended_at


class TestWorkoutSession:
    """Tests for WorkoutSession model."""

    @pytest.mark.asyncio
    async def test_create_workout_session(self, test_session, test_user):
        """Test creating a workout session."""
        session = WorkoutSession(
            user_id=test_user.id,
            started_at=datetime.utcnow(),
            status="active",
        )

        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.status == "active"
        assert session.ended_at is None

    @pytest.mark.asyncio
    async def test_workout_session_relationship_with_user(
        self,
        test_workout_session,
        test_user
    ):
        """Test workout session relationship with user."""
        assert test_workout_session.user.id == test_user.id
        assert test_workout_session in test_user.sessions

    @pytest.mark.asyncio
    async def test_workout_session_completion(self, test_session, test_user):
        """Test completing a workout session."""
        session = WorkoutSession(
            user_id=test_user.id,
            started_at=datetime.utcnow(),
            status="active",
        )

        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)

        # Complete the session
        session.ended_at = datetime.utcnow()
        session.status = "completed"
        session.duration_minutes = 45
        session.average_bpm = 135
        session.calories_burned = 450

        await test_session.commit()
        await test_session.refresh(session)

        assert session.status == "completed"
        assert session.ended_at is not None
        assert session.duration_minutes == 45
        assert session.average_bpm == 135
        assert session.calories_burned == 450

    @pytest.mark.asyncio
    async def test_workout_session_with_metrics(self, test_session, test_user):
        """Test workout session with complete metrics."""
        session = WorkoutSession(
            user_id=test_user.id,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow() + timedelta(minutes=30),
            status="completed",
            duration_minutes=30,
            average_bpm=125,
            max_bpm=160,
            min_bpm=95,
            calories_burned=300,
            distance_km=3.5,
        )

        test_session.add(session)
        await test_session.commit()
        await test_session.refresh(session)

        assert session.duration_minutes == 30
        assert session.average_bpm == 125
        assert session.max_bpm == 160
        assert session.min_bpm == 95
        assert session.calories_burned == 300
        assert session.distance_km == 3.5

    @pytest.mark.asyncio
    async def test_multiple_workout_sessions_per_user(self, test_session, test_user):
        """Test user can have multiple workout sessions."""
        sessions = []
        for i in range(3):
            session = WorkoutSession(
                user_id=test_user.id,
                started_at=datetime.utcnow() - timedelta(days=i),
                status="completed" if i > 0 else "active",
                duration_minutes=(i + 1) * 30 if i > 0 else None,
            )
            test_session.add(session)
            sessions.append(session)

        await test_session.commit()

        for session in sessions:
            await test_session.refresh(session)
            assert session.id is not None
            assert session.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_workout_session_cascade_delete(
        self,
        test_session,
        test_user,
        test_workout_session,
        test_heart_rate_reading
    ):
        """Test that deleting workout session cascades to heart rate readings."""
        session_id = test_workout_session.id
        reading_id = test_heart_rate_reading.id

        # Delete session
        await test_session.delete(test_workout_session)
        await test_session.commit()

        # Verify session is deleted
        result = await test_session.execute(
            select(WorkoutSession).where(WorkoutSession.id == session_id)
        )
        deleted_session = result.scalars().first()
        assert deleted_session is None

        # Verify heart rate reading is also deleted (cascade)
        from heartrate.models import HeartRateReading
        result = await test_session.execute(
            select(HeartRateReading).where(HeartRateReading.id == reading_id)
        )
        deleted_reading = result.scalars().first()
        assert deleted_reading is None


class TestUserRoutes:
    """Tests for user API routes."""

    @pytest.mark.asyncio
    async def test_get_profile_no_auth(self, test_client):
        """Test getting profile without authentication fails."""
        response = test_client.get("/users/profile")

        # Should fail due to missing authentication
        assert response.status_code in [401, 404, 422]

    @pytest.mark.asyncio
    async def test_get_subscription_no_auth(self, test_client):
        """Test getting subscription without authentication fails."""
        response = test_client.get("/users/subscription")

        # Should fail due to missing authentication
        assert response.status_code in [401, 404, 422]

    @pytest.mark.asyncio
    async def test_get_workout_sessions_no_auth(self, test_client):
        """Test getting workout sessions without authentication fails."""
        response = test_client.get("/users/sessions")

        # Should fail due to missing authentication
        assert response.status_code in [401, 404, 422]


class TestUserCRUDOperations:
    """Tests for user CRUD operations."""

    @pytest.mark.asyncio
    async def test_user_creation_timestamp(self, test_user):
        """Test that user has creation timestamp."""
        assert test_user.created_at is not None
        assert isinstance(test_user.created_at, datetime)

    @pytest.mark.asyncio
    async def test_user_update_timestamp(self, test_session, test_user):
        """Test that user update timestamp changes."""
        original_updated_at = test_user.updated_at

        # Wait a moment and update user
        await asyncio.sleep(0.1)
        test_user.display_name = "Updated Name"
        test_user.updated_at = datetime.utcnow()

        await test_session.commit()
        await test_session.refresh(test_user)

        assert test_user.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_query_user_by_id(self, test_session, test_user):
        """Test querying user by ID."""
        from auth.models import User

        result = await test_session.execute(
            select(User).where(User.id == test_user.id)
        )
        found_user = result.scalars().first()

        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.spotify_user_id == test_user.spotify_user_id

    @pytest.mark.asyncio
    async def test_query_user_by_spotify_id(self, test_session, test_user):
        """Test querying user by Spotify user ID."""
        from auth.models import User

        result = await test_session.execute(
            select(User).where(User.spotify_user_id == test_user.spotify_user_id)
        )
        found_user = result.scalars().first()

        assert found_user is not None
        assert found_user.id == test_user.id


import asyncio
