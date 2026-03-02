from __future__ import annotations

from typing import Literal

from src.data.api_client import get_subway_timetable as _api_subway
from src.tools.analytics import track_usage


@track_usage
def get_subway_timetable(
    station: str,
    line: str | None = None,
    day_type: Literal["weekday", "saturday", "holiday"] = "weekday",
    direction: Literal["up", "down"] | None = None,
) -> list[dict] | str:
    """Get Seoul subway timetable for a specific station.

    Args:
        station: Station name in Korean or English (e.g., "강남" or "Gangnam", "서울역" or "Seoul Station").
        line: Line number (e.g., "1", "2", "3"). If omitted for transfer stations, returns all lines.
        day_type: Schedule type — "weekday", "saturday", or "holiday" (default: "weekday").
        direction: Train direction — "up" (toward city center) or "down" (away from center). If omitted, returns both.

    Returns:
        Timetable data with departure times, destinations, and transfer line info, or an error message if station not found.
    """
    result = _api_subway(station=station, line=line, day_type=day_type, direction=direction)
    if isinstance(result, dict) and "error" in result:
        available = result.get("available_stations", [])
        msg = f"Station not found: '{station}'."
        if available:
            msg += f" Available stations: {', '.join(available)}"
        return msg
    return result
