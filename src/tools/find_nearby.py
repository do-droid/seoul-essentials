from __future__ import annotations

from src.data.api_client import find_nearby as _api_nearby
from src.models.place import PlaceType
from src.tools.analytics import track_usage


@track_usage
def find_nearby(
    lat: float,
    lng: float,
    radius_m: int = 500,
    type: PlaceType | None = None,
    limit: int = 5,
) -> list[dict] | dict:
    """Find public facilities near GPS coordinates in Seoul, sorted by distance.

    Args:
        lat: Latitude of the search center point (Seoul range: ~37.4 to ~37.7).
        lng: Longitude of the search center point (Seoul range: ~126.7 to ~127.2).
        radius_m: Search radius in meters (100-5000, default 500).
        type: Optional filter by facility type — "toilet", "pharmacy", "wifi", "aed", "tourist_info", or "baeknyeon" (century-old shops).
        limit: Maximum number of results to return (1-20, default 5).

    Returns:
        A list of nearby places sorted by distance, with distance_m field indicating meters from the search point.
    """
    results = _api_nearby(lat=lat, lng=lng, radius_m=radius_m, type=type, limit=limit)
    if isinstance(results, list) and len(results) == 0:
        return {
            "count": 0,
            "results": [],
            "hint": "No results found nearby. Try increasing radius_m or changing the type. If you think this data should exist, consider submitting feedback via the submit_feedback tool.",
        }
    return results
