"""WebSocket Connection Manager for Heart Rate Streaming."""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket instance
            user_id: User identifier
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        """
        Remove a WebSocket connection.

        Args:
            user_id: User identifier
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send message to specific user.

        Args:
            message: Message dictionary
            user_id: User identifier
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected users.

        Args:
            message: Message dictionary
        """
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")


# Global connection manager instance
manager = ConnectionManager()
