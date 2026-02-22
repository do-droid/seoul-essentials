from __future__ import annotations

from src.data.geo import haversine_distance
from src.data.loader import get_places
from src.models.place import PlaceType


def find_nearby(
    lat: float,
    lng: float,
    radius_m: int = 500,
    type: PlaceType | None = None,
    limit: int = 5,
) -> list[dict]:
    """Find public facilities near GPS coordinates in Seoul, sorted by distance.

    Args:
        lat: Latitude of the search center point (Seoul range: ~37.4 to ~37.7).
        lng: Longitude of the search center point (Seoul range: ~126.7 to ~127.2).
        radius_m: Search radius in meters (100-5000, default 500).
        type: Optional filter by facility type — "toilet", "pharmacy", "wifi", "aed", or "tourist_info".
        limit: Maximum number of results to return (1-20, default 5).

    Returns:
        A list of nearby places sorted by distance, with distance_m field indicating meters from the search point.
    """
    places = get_places()
    if type:
        places = [p for p in places if p.type == type]

    clamped_radius = max(100, min(radius_m, 5000))
    clamped_limit = max(1, min(limit, 20))

    with_distance = []
    for p in places:
        dist = haversine_distance(lat, lng, p.location.lat, p.location.lng)
        if dist <= clamped_radius:
            entry = p.model_dump()
            entry["distance_m"] = round(dist, 1)
            with_distance.append(entry)

    with_distance.sort(key=lambda x: x["distance_m"])
    return with_distance[:clamped_limit]
