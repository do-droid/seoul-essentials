from __future__ import annotations

from typing import Literal

from src.data.loader import get_subway_stations


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
    stations = get_subway_stations()
    station_query = station.strip()
    station_lower = station_query.lower()

    matches = []
    for s in stations:
        name_match = (
            s.station_name.ko == station_query
            or s.station_name.en.lower() == station_lower
        )
        if name_match and (line is None or s.line == line):
            matches.append(s)

    if not matches:
        available = sorted(set(
            f"{s.station_name.ko} ({s.station_name.en})" for s in stations
        ))
        return (
            f"Station not found: '{station}'. "
            f"Available stations: {', '.join(available)}"
        )

    results = []
    for s in matches:
        timetable_data = getattr(s.timetable, day_type)
        entry = {
            "station_id": s.station_id,
            "station_name": s.station_name.model_dump(),
            "line": s.line,
            "line_name": s.line_name.model_dump(),
            "day_type": day_type,
            "transfer_lines": s.transfer_lines,
        }

        if direction == "up":
            entry["timetable"] = {"up": [t.model_dump() for t in timetable_data.up]}
        elif direction == "down":
            entry["timetable"] = {"down": [t.model_dump() for t in timetable_data.down]}
        else:
            entry["timetable"] = {
                "up": [t.model_dump() for t in timetable_data.up],
                "down": [t.model_dump() for t in timetable_data.down],
            }
        results.append(entry)

    return results
