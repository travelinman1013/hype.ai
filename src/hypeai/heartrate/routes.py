"""Heart Rate WebSocket Routes."""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .connection_manager import manager
from .services import ZoneService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/heartrate")
async def websocket_heartrate(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for authentication"),
):
    """
    WebSocket endpoint for real-time heart rate streaming.

    Args:
        websocket: WebSocket connection
        user_id: User ID from query parameter
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive heart rate data from client
            data = await websocket.receive_json()

            bpm = data.get("bpm")
            if not bpm:
                await manager.send_personal_message(
                    {"error": "Missing 'bpm' field"},
                    user_id
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
                user_id
            )

            logger.debug(f"User {user_id}: {bpm} BPM -> {zone} zone")

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
