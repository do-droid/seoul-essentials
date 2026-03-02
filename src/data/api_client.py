"""HTTP API client for Seoul Essentials Cloud Functions backend.

Replaces the old loader.py (direct Firestore access) with a thin HTTP client.
The MCP server no longer needs Firebase credentials — it just calls the REST API.

Configuration:
  API_BASE_URL env var — e.g., "https://api-<hash>-du.a.run.app"
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_base_url: str = ""
_client: httpx.Client | None = None


def init_client() -> None:
    """Initialize the HTTP client with API_BASE_URL."""
    global _base_url, _client

    _base_url = os.environ.get("API_BASE_URL", "").rstrip("/")
    if not _base_url:
        logger.error("API_BASE_URL environment variable is not set!")
        return

    _client = httpx.Client(
        base_url=_base_url,
        timeout=30.0,
        headers={"Accept": "application/json"},
    )
    logger.info(f"API client initialized: {_base_url}")


def _get(path: str, params: dict | None = None) -> dict:
    """GET request to the API. Returns parsed JSON or error dict."""
    if _client is None:
        return {"error": "API client not initialized. Set API_BASE_URL env var."}
    try:
        resp = _client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            return e.response.json()
        except Exception:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}


def _post(path: str, body: dict) -> dict:
    """POST request to the API. Returns parsed JSON or error dict."""
    if _client is None:
        return {"error": "API client not initialized. Set API_BASE_URL env var."}
    try:
        resp = _client.post(path, json=body)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            return e.response.json()
        except Exception:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}


def search_places(
    type: str,
    district: str | None = None,
    filters: dict | None = None,
    limit: int = 10,
) -> list[dict]:
    """Call GET /places."""
    params: dict = {"type": type, "limit": str(limit)}
    if district:
        params["district"] = district
    if filters:
        for k, v in filters.items():
            params[f"filter.{k}"] = str(v).lower() if isinstance(v, bool) else str(v)

    data = _get("/places", params=params)
    return data.get("results", []) if "results" in data else [data]


def get_detail(place_id: str) -> dict:
    """Call GET /places/<id>."""
    return _get(f"/places/{place_id}")


def find_nearby(
    lat: float,
    lng: float,
    radius_m: int = 500,
    type: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Call GET /places/nearby."""
    params: dict = {
        "lat": str(lat),
        "lng": str(lng),
        "radius_m": str(radius_m),
        "limit": str(limit),
    }
    if type:
        params["type"] = type

    data = _get("/places/nearby", params=params)
    return data.get("results", []) if "results" in data else [data]


def get_subway_timetable(
    station: str,
    line: str | None = None,
    day_type: str = "weekday",
    direction: str | None = None,
) -> list[dict] | dict:
    """Call GET /subway/timetable."""
    params: dict = {"station": station, "day_type": day_type}
    if line:
        params["line"] = line
    if direction:
        params["direction"] = direction

    data = _get("/subway/timetable", params=params)
    if "error" in data:
        return data
    return data.get("results", []) if "results" in data else [data]


def post_feedback(category: str, message: str, priority: str = "medium") -> dict:
    """Call POST /feedback."""
    return _post("/feedback", {
        "category": category,
        "message": message,
        "priority": priority,
    })


def post_analytics(event: dict) -> None:
    """Call POST /analytics. Fire-and-forget — failures are silently ignored."""
    try:
        _post("/analytics", event)
    except Exception:
        pass


def get_analytics(days: int = 7) -> dict:
    """Call GET /analytics."""
    return _get("/analytics", params={"days": str(days)})


def health_check() -> dict:
    """Call GET /health to verify API connectivity."""
    return _get("/health")
