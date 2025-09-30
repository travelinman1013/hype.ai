"""
Tests for Heart Rate Module.

Tests for BPM zone mapping, WebSocket connections, and heart rate services.
"""

import pytest
from datetime import datetime

from heartrate.services import ZoneService
from heartrate.models import HeartRateReading
from heartrate.connection_manager import ConnectionManager


class TestZoneService:
    """Tests for heart rate zone mapping."""

    def test_get_zone_for_bpm_rest(self):
        """Test mapping low BPM to rest zone."""
        zone = ZoneService.get_zone_for_bpm(85)
        assert zone == "rest"

    def test_get_zone_for_bpm_warmup_min_boundary(self):
        """Test warmup zone minimum boundary (90 BPM)."""
        zone = ZoneService.get_zone_for_bpm(90)
        assert zone == "warmup"

    def test_get_zone_for_bpm_warmup_max_boundary(self):
        """Test warmup zone maximum boundary (110 BPM)."""
        zone = ZoneService.get_zone_for_bpm(110)
        assert zone == "warmup"

    def test_get_zone_for_bpm_warmup_mid(self):
        """Test warmup zone middle range."""
        zone = ZoneService.get_zone_for_bpm(100)
        assert zone == "warmup"

    def test_get_zone_for_bpm_cardio_min_boundary(self):
        """Test cardio zone minimum boundary (111 BPM)."""
        zone = ZoneService.get_zone_for_bpm(111)
        assert zone == "cardio"

    def test_get_zone_for_bpm_cardio_max_boundary(self):
        """Test cardio zone maximum boundary (140 BPM)."""
        zone = ZoneService.get_zone_for_bpm(140)
        assert zone == "cardio"

    def test_get_zone_for_bpm_cardio_mid(self):
        """Test cardio zone middle range."""
        zone = ZoneService.get_zone_for_bpm(125)
        assert zone == "cardio"

    def test_get_zone_for_bpm_peak_min_boundary(self):
        """Test peak zone minimum boundary (141 BPM)."""
        zone = ZoneService.get_zone_for_bpm(141)
        assert zone == "peak"

    def test_get_zone_for_bpm_peak_high(self):
        """Test peak zone high value."""
        zone = ZoneService.get_zone_for_bpm(180)
        assert zone == "peak"

    def test_get_zone_for_bpm_peak_very_high(self):
        """Test peak zone very high value (edge case)."""
        zone = ZoneService.get_zone_for_bpm(220)
        assert zone == "peak"

    def test_get_zone_for_bpm_below_warmup(self):
        """Test BPM just below warmup threshold."""
        zone = ZoneService.get_zone_for_bpm(89)
        assert zone == "rest"

    def test_get_spotify_features_for_warmup(self):
        """Test Spotify features for warmup zone."""
        features = ZoneService.get_spotify_features_for_zone("warmup")

        assert features["target_tempo"] == 100
        assert features["target_energy"] == 0.4
        assert features["target_danceability"] == 0.5
        assert features["target_valence"] == 0.6

    def test_get_spotify_features_for_cardio(self):
        """Test Spotify features for cardio zone."""
        features = ZoneService.get_spotify_features_for_zone("cardio")

        assert features["target_tempo"] == 130
        assert features["target_energy"] == 0.7
        assert features["target_danceability"] == 0.7
        assert features["target_valence"] == 0.7

    def test_get_spotify_features_for_peak(self):
        """Test Spotify features for peak zone."""
        features = ZoneService.get_spotify_features_for_zone("peak")

        assert features["target_tempo"] == 160
        assert features["target_energy"] == 0.9
        assert features["target_danceability"] == 0.8
        assert features["target_valence"] == 0.8

    def test_get_spotify_features_for_rest(self):
        """Test Spotify features for rest zone."""
        features = ZoneService.get_spotify_features_for_zone("rest")

        assert features["target_tempo"] == 80
        assert features["target_energy"] == 0.3
        assert features["target_danceability"] == 0.4
        assert features["target_valence"] == 0.5

    def test_get_spotify_features_for_unknown_zone(self):
        """Test Spotify features for unknown zone defaults to cardio."""
        features = ZoneService.get_spotify_features_for_zone("unknown")

        assert features["target_tempo"] == 130
        assert features == ZoneService.get_spotify_features_for_zone("cardio")


class TestHeartRateReading:
    """Tests for HeartRateReading model."""

    @pytest.mark.asyncio
    async def test_create_heart_rate_reading(
        self,
        test_session,
        test_user,
        test_workout_session
    ):
        """Test creating a heart rate reading."""
        reading = HeartRateReading(
            user_id=test_user.id,
            session_id=test_workout_session.id,
            bpm=130,
            zone="cardio",
            timestamp=datetime.utcnow(),
        )

        test_session.add(reading)
        await test_session.commit()
        await test_session.refresh(reading)

        assert reading.id is not None
        assert reading.user_id == test_user.id
        assert reading.bpm == 130
        assert reading.zone == "cardio"

    @pytest.mark.asyncio
    async def test_heart_rate_reading_relationships(
        self,
        test_heart_rate_reading,
        test_user,
        test_workout_session
    ):
        """Test heart rate reading relationships."""
        assert test_heart_rate_reading.user.id == test_user.id
        assert test_heart_rate_reading.session.id == test_workout_session.id

    @pytest.mark.asyncio
    async def test_multiple_readings_same_session(
        self,
        test_session,
        test_user,
        test_workout_session
    ):
        """Test creating multiple readings for same session."""
        readings = [
            HeartRateReading(
                user_id=test_user.id,
                session_id=test_workout_session.id,
                bpm=100 + i * 10,
                zone="cardio",
                timestamp=datetime.utcnow(),
            )
            for i in range(5)
        ]

        for reading in readings:
            test_session.add(reading)

        await test_session.commit()

        # Verify all readings were created
        for reading in readings:
            await test_session.refresh(reading)
            assert reading.id is not None


class TestConnectionManager:
    """Tests for WebSocket connection manager."""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        """Test connecting and disconnecting WebSocket."""
        manager = ConnectionManager()
        user_id = "test_user_1"

        # Mock WebSocket
        class MockWebSocket:
            async def accept(self):
                pass

        websocket = MockWebSocket()

        # Connect
        await manager.connect(websocket, user_id)
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] == websocket

        # Disconnect
        manager.disconnect(user_id)
        assert user_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connect_replaces_existing_connection(self):
        """Test that new connection replaces old one for same user."""
        manager = ConnectionManager()
        user_id = "test_user_1"

        class MockWebSocket:
            async def accept(self):
                pass

        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()

        # Connect first websocket
        await manager.connect(websocket1, user_id)
        assert manager.active_connections[user_id] == websocket1

        # Connect second websocket (should replace)
        await manager.connect(websocket2, user_id)
        assert manager.active_connections[user_id] == websocket2
        assert manager.active_connections[user_id] != websocket1

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific user."""
        manager = ConnectionManager()
        user_id = "test_user_1"

        class MockWebSocket:
            def __init__(self):
                self.sent_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.sent_messages.append(data)

        websocket = MockWebSocket()
        await manager.connect(websocket, user_id)

        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, user_id)

        assert len(websocket.sent_messages) == 1
        assert websocket.sent_messages[0] == message

    @pytest.mark.asyncio
    async def test_send_personal_message_to_disconnected_user(self):
        """Test sending message to disconnected user doesn't raise error."""
        manager = ConnectionManager()
        user_id = "nonexistent_user"

        # Should not raise an error
        await manager.send_personal_message({"test": "data"}, user_id)

    @pytest.mark.asyncio
    async def test_multiple_users_connected(self):
        """Test multiple users connected simultaneously."""
        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        user1 = "user_1"
        user2 = "user_2"
        user3 = "user_3"

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await manager.connect(ws1, user1)
        await manager.connect(ws2, user2)
        await manager.connect(ws3, user3)

        assert len(manager.active_connections) == 3
        assert user1 in manager.active_connections
        assert user2 in manager.active_connections
        assert user3 in manager.active_connections

        # Disconnect one
        manager.disconnect(user2)
        assert len(manager.active_connections) == 2
        assert user2 not in manager.active_connections
