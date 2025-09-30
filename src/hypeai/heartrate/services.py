"""Heart Rate Zone Mapping Services."""

from config import settings


class ZoneService:
    """Service for mapping BPM to workout zones."""

    @staticmethod
    def get_zone_for_bpm(bpm: int) -> str:
        """
        Map BPM to workout zone.

        Args:
            bpm: Heart rate in beats per minute

        Returns:
            Zone name (warmup, cardio, peak)
        """
        if settings.zone_warmup_min <= bpm <= settings.zone_warmup_max:
            return "warmup"
        elif settings.zone_cardio_min <= bpm <= settings.zone_cardio_max:
            return "cardio"
        elif bpm >= settings.zone_peak_min:
            return "peak"
        else:
            return "rest"  # Below warmup threshold

    @staticmethod
    def get_spotify_features_for_zone(zone: str) -> dict:
        """
        Get target Spotify audio features for zone.

        Args:
            zone: Workout zone name

        Returns:
            Dictionary of audio features
        """
        zone_features = {
            "warmup": {
                "target_tempo": 100,
                "target_energy": 0.4,
                "target_danceability": 0.5,
                "target_valence": 0.6,
            },
            "cardio": {
                "target_tempo": 130,
                "target_energy": 0.7,
                "target_danceability": 0.7,
                "target_valence": 0.7,
            },
            "peak": {
                "target_tempo": 160,
                "target_energy": 0.9,
                "target_danceability": 0.8,
                "target_valence": 0.8,
            },
            "rest": {
                "target_tempo": 80,
                "target_energy": 0.3,
                "target_danceability": 0.4,
                "target_valence": 0.5,
            },
        }

        return zone_features.get(zone, zone_features["cardio"])
