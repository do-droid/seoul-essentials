from __future__ import annotations

from src.data.api_client import get_detail as _api_detail


def get_place_detail(id: str) -> dict | str:
    """Get full details of a specific place or subway station in Seoul by its ID.

    Args:
        id: The unique place ID (e.g., "toilet_00001", "pharmacy_001", "wifi_00001", "aed_00001", "tourist_info_01").

    Returns:
        Complete place information including location, services, hours, and accessibility, or an error message if not found.
    """
    result = _api_detail(id)
    if "error" in result:
        return f"Place not found: {id}. Use find_places or get_subway_timetable to discover available IDs."
    return result
