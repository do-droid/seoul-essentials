from __future__ import annotations

from typing import Literal

from src.data.api_client import get_subway_timetable as _api_subway
from src.tools.analytics import track_usage


@track_usage
def get_subway_timetable(
    station: str,
    line: str | None = None,
    day_type: Literal["weekday", "saturday", "holiday"] | None = None,
    direction: Literal["up", "down"] | None = None,
    after: str | None = None,
    full_day: bool = False,
    limit: int | None = None,
) -> dict | str:
    """Get real Seoul subway timetables — all 405 stations on lines 1-9.

    Covers Seoul Metro lines 1-9 only, with full official timetables
    (Seoul Open Data, ~1,000+ trains/day per station). Interchanges
    between those lines are complete (e.g. Jongno 3-ga on lines 1, 3
    AND 5), but connections to other operators — Gyeongui-Jungang,
    AREX, Sinbundang, Suin-Bundang, Ui-Sinseol, Gyeongchun — are not
    in this dataset and will not appear in `transfer_lines`.

    By default returns the next 20 departures per direction after the
    current time in Seoul (KST), plus a per-direction summary with
    first/last train times and the total train count for the day.

    Args:
        station: Station name in Korean or English (e.g., "강남" or "Gangnam",
            "서울역" or "Seoul Station"). Combined forms like
            "종로3가 (Jongno 3-ga)" and partial names also match.
        line: Line number "1"-"9" (also accepts "3호선" / "Line 3"). If omitted
            for transfer stations, returns every line serving the station.
        day_type: "weekday", "saturday", or "holiday". Omit it — the server
            then applies today's KST service day, including Korean public
            holidays, and echoes which calendar it used in `note`. Pass a
            value only to ask about a different kind of day.
        direction: "up" or "down". On the Line 2 loop, "up" is the inner
            (clockwise) loop and "down" the outer loop — see the
            direction_labels field. If omitted, returns both.
        after: "HH:MM" (KST) — show departures from this time instead of now.
            Times past midnight appear as 24:xx/25:xx.
        full_day: True returns the complete day timetable (large; ~40KB per
            line). Prefer `after` for "next train" questions. Note: the
            response text may name this `full=true` — that is the REST
            parameter; from this tool it is `full_day`.
        limit: Departures per direction to return (1-200, default 20).

    Returns:
        Timetable payload with results per line (departure times, destinations,
        express/normal type, transfer lines, first/last-train summary), or an
        error message with station-name suggestions if no match is found.
    """
    result = _api_subway(
        station=station, line=line, day_type=day_type,
        direction=direction, after=after, full_day=full_day, limit=limit)
    if isinstance(result, dict) and "error" in result:
        msg = str(result["error"])
        suggestions = result.get("suggestions")
        if suggestions:
            msg += " Did you mean: " + "; ".join(suggestions) + "."
        if result.get("note"):
            msg += " " + str(result["note"])
        return msg
    return result
