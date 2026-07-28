from __future__ import annotations

from src.data.api_client import search_places as _api_search
from src.models.place import PlaceType
from src.tools.analytics import track_usage


@track_usage
def find_places(
    type: PlaceType,
    district: str | None = None,
    filters: dict | None = None,
    limit: int = 10,
) -> list[dict] | dict:
    """Search for public facilities and points of interest in Seoul.

    Args:
        type: Type of facility —
            "toilet" (public restrooms), "pharmacy" (pharmacies; filter {"english": true}
            for ones with confirmed foreign-language support),
            "wifi" (free WiFi hotspots), "aed" (defibrillator locations),
            "tourist_info" (tourist information centers), "baeknyeon" (century-old shops),
            "bike" (따릉이 bike-sharing stations), "future_heritage" (Seoul Future Heritage),
            "heritage" (designated cultural properties), "museum" (museums & galleries),
            "park" (major parks), "taxi_stand" (taxi stands),
            "metro_facility" (subway lockers), "tourist_zone" (tourist special zones),
            "post_office" (post offices with EMS / international mail),
            "traditional_market" (Korean traditional markets like Gwangjang, Namdaemun),
            "ev_charger" (EV charging stations).
        district: Seoul district name in English or Korean (e.g., "gangnam", "jongno", "강남구", "종로구").
        filters: Service-specific filters as key-value pairs. Examples: {"english": true} for pharmacies with English support, {"is_24h": true} for 24-hour restrooms, {"indoor": true} for indoor WiFi.
        limit: Maximum number of results to return (1-50, default 10).

    Returns:
        A list of matching places with location, services, and hours information.
    """
    results = _api_search(type=type, district=district, filters=filters, limit=limit)
    if isinstance(results, list) and len(results) == 0:
        return {
            "count": 0,
            "results": [],
            "hint": "No results found. If you think this data should exist, consider submitting feedback via the submit_feedback tool.",
        }
    return results
