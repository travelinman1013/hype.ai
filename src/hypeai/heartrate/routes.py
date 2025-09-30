"""Heart Rate WebSocket Routes."""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from shared.jwt import get_user_id_from_token

from .connection_manager import manager
from .services import ZoneService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/heartrate")
async def websocket_heartrate(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    WebSocket endpoint for real-time heart rate streaming.

    Requires JWT token as query parameter (?token=<jwt_token>).

    Args:
        websocket: WebSocket connection
        token: JWT access token from query parameter

    Raises:
        WebSocket 403: If token is invalid or expired
    """
    # Validate JWT token and extract user ID
    try:
        user_id = get_user_id_from_token(token)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    await manager.connect(websocket, str(user_id))

    try:
        while True:
            # Receive heart rate data from client
            data = await websocket.receive_json()

            bpm = data.get("bpm")
            if not bpm:
                await manager.send_personal_message(
                    {"error": "Missing 'bpm' field"},
                    str(user_id)
                )
                continue

            # Determine workout zone
            zone = ZoneService.get_zone_for_bpm(bpm)

            # Get audio features for zone
            features = ZoneService.get_spotify_features_for_zone(zone)

            # Send acknowledgment with zone info
            await manager.send_personal_message(
                {
                    "bpm": bpm,
                    "zone": zone,
                    "features": features,
                    "message": f"Heart rate {bpm} BPM mapped to {zone} zone"
                },
                str(user_id)
            )

            logger.debug(f"User {user_id}: {bpm} BPM -> {zone} zone")

    except WebSocketDisconnect:
        manager.disconnect(str(user_id))
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(str(user_id))
