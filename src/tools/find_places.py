from __future__ import annotations

from src.data.api_client import search_places as _api_search
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
        district: Seoul district name in English or Korean (e.g., "gangnam", "jongno", "강남구", "종로구").
        filters: Service-specific filters as key-value pairs. Examples: {"english": true} for pharmacies with English support, {"is_24h": true} for 24-hour restrooms, {"indoor": true} for indoor WiFi.
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        A list of matching places with location, services, and hours information.
    """
    return _api_search(type=type, district=district, filters=filters, limit=limit)
