from __future__ import annotations

from src.data.api_client import find_nearby as _api_nearby
from src.tools.analytics import track_usage


@track_usage
def find_nearby(
    lat: float,
    lng: float,
    radius_m: int = 500,
    type: str | None = None,
    limit: int = 5,
) -> list[dict] | dict:
    """Find public facilities near GPS coordinates in Seoul, sorted by distance.

    Args:
        lat: Latitude of the search center point (Seoul range: ~37.4 to ~37.7).
        lng: Longitude of the search center point (Seoul range: ~126.7 to ~127.2).
        radius_m: Search radius in meters (100-5000, default 500).
        type: Optional filter by facility type. Common synonyms ("restroom",
            "lockers", "drugstore") are accepted and mapped. Values —
            "toilet", "pharmacy", "wifi", "aed", "tourist_info", "baeknyeon",
            "bike", "future_heritage", "heritage", "museum",
            "park", "taxi_stand", "metro_facility", "tourist_zone",
            "post_office", "traditional_market", "ev_charger".
        limit: Maximum number of results to return (1-20, default 5).

    Returns:
        A list of nearby places sorted by distance, each with a distance_m
        field giving meters from the search point.

        Records whose coordinates are only known at district level (heritage,
        traditional_market, metro_facility, post_office, ev_charger, baeknyeon)
        are withheld, because a distance measured from a district centroid
        would be fiction — the response `note` says when this happened. Reach
        them with find_places and a `district` instead.
    """
    results = _api_nearby(lat=lat, lng=lng, radius_m=radius_m, type=type, limit=limit)
    if isinstance(results, list) and len(results) == 0:
        return {
            "count": 0,
            "results": [],
            "hint": "No results found nearby. Try increasing radius_m or changing the type. If you think this data should exist, consider submitting feedback via the submit_feedback tool.",
        }
    return results
