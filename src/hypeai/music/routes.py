"""Music API Routes."""

import logging

from auth.services import AuthService
from database import get_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from heartrate.services import ZoneService
from shared.dependencies import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession

from .rate_limiter import rate_limiter
from .spotify_api import SpotifyAPI

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/zones")
async def get_zone_configuration():
    """
    Get workout zone configuration.

    Returns:
        Zone thresholds and audio features
    """
    zones = {
        "warmup": {
            "min_bpm": 90,
            "max_bpm": 110,
            "features": ZoneService.get_spotify_features_for_zone("warmup"),
        },
        "cardio": {
            "min_bpm": 111,
            "max_bpm": 140,
            "features": ZoneService.get_spotify_features_for_zone("cardio"),
        },
        "peak": {
            "min_bpm": 141,
            "max_bpm": 220,
            "features": ZoneService.get_spotify_features_for_zone("peak"),
        },
    }

    return {"zones": zones}


@router.get("/current")
async def get_current_playback(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get user's current Spotify playback state.

    Requires JWT authentication via Authorization header.

    Args:
        session: Database session
        user_id: User ID from JWT token

    Returns:
        Current playback state
    """
    try:
        # Get valid access token
        access_token = await AuthService.get_valid_access_token(session, user_id)

        # Check rate limit
        await rate_limiter.acquire(str(user_id))

        # Get playback state from Spotify
        async with SpotifyAPI(access_token) as spotify:
            playback = await spotify.get_current_playback()

        return {"playback": playback}

    except Exception as e:
        logger.error(f"Failed to get playback for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get playback: {str(e)}"
        )


@router.post("/queue")
async def queue_track(
    track_uri: str = Query(..., description="Spotify track URI"),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    Manually queue a track (for testing).

    Requires JWT authentication via Authorization header.

    Args:
        track_uri: Spotify track URI
        session: Database session
        user_id: User ID from JWT token

    Returns:
        Success message
    """
    try:
        # Get valid access token
        access_token = await AuthService.get_valid_access_token(session, user_id)

        # Check rate limit
        await rate_limiter.acquire(str(user_id))

        # Queue track
        async with SpotifyAPI(access_token) as spotify:
            await spotify.queue_track(track_uri)

        return {"message": f"Successfully queued track {track_uri}"}

    except Exception as e:
        logger.error(f"Failed to queue track for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue track: {str(e)}"
        )
