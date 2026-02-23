from __future__ import annotations

from src.data.loader import get_places, get_subway_stations


def get_place_detail(id: str) -> dict | str:
    """Get full details of a specific place or subway station in Seoul by its ID.

    Args:
        id: The unique place ID (e.g., "toilet_00001", "pharmacy_001", "wifi_00001", "aed_00001", "tourist_info_01").

    Returns:
        Complete place information including location, services, hours, and accessibility, or an error message if not found.
    """
    for p in get_places():
        if p.id == id:
            return p.model_dump()

    for s in get_subway_stations():
        if s.station_id == id:
            return s.model_dump()

    return f"Place not found: {id}. Use find_places or get_subway_timetable to discover available IDs."
