from __future__ import annotations

from src.data.loader import get_places
from src.models.place import PlaceType

# Korean district name → English (for accepting Korean input)
_DISTRICT_KO_TO_EN: dict[str, str] = {
    "강남구": "gangnam", "강남": "gangnam",
    "강동구": "gangdong", "강동": "gangdong",
    "강북구": "gangbuk", "강북": "gangbuk",
    "강서구": "gangseo", "강서": "gangseo",
    "관악구": "gwanak", "관악": "gwanak",
    "광진구": "gwangjin", "광진": "gwangjin",
    "구로구": "guro", "구로": "guro",
    "금천구": "geumcheon", "금천": "geumcheon",
    "노원구": "nowon", "노원": "nowon",
    "도봉구": "dobong", "도봉": "dobong",
    "동대문구": "dongdaemun", "동대문": "dongdaemun",
    "동작구": "dongjak", "동작": "dongjak",
    "마포구": "mapo", "마포": "mapo",
    "서대문구": "seodaemun", "서대문": "seodaemun",
    "서초구": "seocho", "서초": "seocho",
    "성동구": "seongdong", "성동": "seongdong",
    "성북구": "seongbuk", "성북": "seongbuk",
    "송파구": "songpa", "송파": "songpa",
    "양천구": "yangcheon", "양천": "yangcheon",
    "영등포구": "yeongdeungpo", "영등포": "yeongdeungpo",
    "용산구": "yongsan", "용산": "yongsan",
    "은평구": "eunpyeong", "은평": "eunpyeong",
    "종로구": "jongno", "종로": "jongno",
    "중구": "jung",
    "중랑구": "jungnang", "중랑": "jungnang",
}


def _normalize_district(district: str) -> str:
    """Normalize district name to lowercase English."""
    d = district.strip()
    if d in _DISTRICT_KO_TO_EN:
        return _DISTRICT_KO_TO_EN[d]
    return d.lower()


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
    places = get_places()
    results = [p for p in places if p.type == type]

    if district:
        normalized = _normalize_district(district)
        results = [p for p in results if p.location.district == normalized]

    if filters:
        filtered = []
        for p in results:
            match = all(p.services.get(k) == v for k, v in filters.items())
            if match:
                filtered.append(p)
        results = filtered

    clamped_limit = max(1, min(limit, 50))
    return [p.model_dump() for p in results[:clamped_limit]]
