from __future__ import annotations

from src.data.loader import get_places
from src.models.place import PlaceType


def find_places(
    type: PlaceType,
    district: str | None = None,
    filters: dict | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search for public facilities in Seoul (restrooms, pharmacies, WiFi hotspots, AED locations, tourist info centers).

    Args:
        type: Type of facility — "toilet", "pharmacy", "wifi", "aed", or "tourist_info".
        district: Seoul district name in English (e.g., "gangnam", "jongno", "mapo", "yongsan", "jung", "songpa").
        filters: Service-specific filters as key-value pairs. Examples: {"english_spoken": true} for pharmacies, {"is_24h": true} for restrooms, {"requires_login": false} for WiFi.
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        A list of matching places with location, services, and hours information. All data is bilingual (Korean/English).
    """
    places = get_places()
    results = [p for p in places if p.type == type]

    if district:
        district_lower = district.lower()
        results = [p for p in results if p.location.district.lower() == district_lower]

    if filters:
        filtered = []
        for p in results:
            match = all(p.services.get(k) == v for k, v in filters.items())
            if match:
                filtered.append(p)
        results = filtered

    clamped_limit = max(1, min(limit, 50))
    return [p.model_dump() for p in results[:clamped_limit]]
