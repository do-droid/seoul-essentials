"""Flask REST API for Seoul Essentials data.

Endpoints:
  GET /health                  — health check
  GET /places                  — search places by type, district, filters
  GET /places/<id>             — get single place or subway station detail
  GET /places/nearby           — find places near GPS coordinates
  GET /subway/timetable        — get subway timetable
"""

from __future__ import annotations

import math
from typing import Any

import firebase_admin
from firebase_admin import firestore
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Korean district name → English mapping
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in meters between two GPS coordinates."""
    R = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def _get_db():
    """Get Firestore client (initializes Firebase if needed)."""
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()
    return firestore.client()


# ---------------------------------------------------------------------------
# Flask app factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "seoul-essentials-api"})

    # ------------------------------------------------------------------
    # GET /places — search by type, district, filters
    # ------------------------------------------------------------------
    @app.route("/places", methods=["GET"])
    def search_places():
        place_type = request.args.get("type")
        if not place_type:
            return jsonify({"error": "Missing required parameter: type"}), 400

        valid_types = {"toilet", "pharmacy", "wifi", "aed", "tourist_info"}
        if place_type not in valid_types:
            return jsonify({"error": f"Invalid type: {place_type}. Must be one of: {', '.join(sorted(valid_types))}"}), 400

        district = request.args.get("district")
        limit = min(max(int(request.args.get("limit", "10")), 1), 50)

        db = _get_db()
        query = db.collection("places").where("type", "==", place_type)

        # District filter (server-side)
        if district:
            normalized = _normalize_district(district)
            query = query.where("location.district", "==", normalized)

        docs = query.limit(limit * 3).stream()  # fetch extra for client-side filter
        results: list[dict[str, Any]] = []

        # Parse service filters from query params (e.g., ?filter.english=true)
        filters: dict[str, Any] = {}
        for key, value in request.args.items():
            if key.startswith("filter."):
                field = key[7:]  # strip "filter." prefix
                # Convert "true"/"false" to bool, try int, else string
                if value.lower() == "true":
                    filters[field] = True
                elif value.lower() == "false":
                    filters[field] = False
                else:
                    try:
                        filters[field] = int(value)
                    except ValueError:
                        filters[field] = value

        for doc in docs:
            data = doc.to_dict()
            # Apply service filters in Python
            if filters:
                services = data.get("services", {})
                if not all(services.get(k) == v for k, v in filters.items()):
                    continue
            results.append(data)
            if len(results) >= limit:
                break

        return jsonify({"count": len(results), "results": results})

    # ------------------------------------------------------------------
    # GET /places/nearby — GPS proximity search
    # ------------------------------------------------------------------
    @app.route("/places/nearby", methods=["GET"])
    def find_nearby():
        try:
            lat = float(request.args["lat"])
            lng = float(request.args["lng"])
        except (KeyError, ValueError):
            return jsonify({"error": "Missing or invalid required parameters: lat, lng"}), 400

        radius_m = min(max(int(request.args.get("radius_m", "500")), 100), 5000)
        limit = min(max(int(request.args.get("limit", "5")), 1), 20)
        place_type = request.args.get("type")

        # Bounding box: 1 degree latitude ≈ 111,320 m
        lat_delta = radius_m / 111_320.0
        lat_min = lat - lat_delta
        lat_max = lat + lat_delta

        db = _get_db()

        if place_type:
            # Composite index: type + location.lat
            query = (
                db.collection("places")
                .where("type", "==", place_type)
                .where("location.lat", ">=", lat_min)
                .where("location.lat", "<=", lat_max)
            )
        else:
            # Single field index: location.lat
            query = (
                db.collection("places")
                .where("location.lat", ">=", lat_min)
                .where("location.lat", "<=", lat_max)
            )

        # Lng bounding box (approximate, cos(lat) adjusted)
        lng_delta = radius_m / (111_320.0 * math.cos(math.radians(lat)))
        lng_min = lng - lng_delta
        lng_max = lng + lng_delta

        docs = query.stream()
        candidates: list[dict[str, Any]] = []

        for doc in docs:
            data = doc.to_dict()
            loc = data.get("location", {})
            doc_lng = loc.get("lng", 0)

            # Longitude filter in Python (Firestore only supports range on one field)
            if doc_lng < lng_min or doc_lng > lng_max:
                continue

            # Exact haversine distance
            dist = _haversine(lat, lng, loc.get("lat", 0), doc_lng)
            if dist <= radius_m:
                data["distance_m"] = round(dist, 1)
                candidates.append(data)

        # Sort by distance and limit
        candidates.sort(key=lambda x: x["distance_m"])
        results = candidates[:limit]

        return jsonify({"count": len(results), "results": results})

    # ------------------------------------------------------------------
    # GET /places/<id> — single place or subway station detail
    # ------------------------------------------------------------------
    @app.route("/places/<place_id>", methods=["GET"])
    def get_place_detail(place_id: str):
        db = _get_db()

        # Try places collection first
        doc = db.collection("places").document(place_id).get()
        if doc.exists:
            return jsonify(doc.to_dict())

        # Try subway_stations collection
        doc = db.collection("subway_stations").document(place_id).get()
        if doc.exists:
            return jsonify(doc.to_dict())

        return jsonify({"error": f"Not found: {place_id}"}), 404

    # ------------------------------------------------------------------
    # GET /subway/timetable — subway timetable lookup
    # ------------------------------------------------------------------
    @app.route("/subway/timetable", methods=["GET"])
    def get_subway_timetable():
        station = request.args.get("station")
        if not station:
            return jsonify({"error": "Missing required parameter: station"}), 400

        line = request.args.get("line")
        day_type = request.args.get("day_type", "weekday")
        direction = request.args.get("direction")

        if day_type not in ("weekday", "saturday", "holiday"):
            return jsonify({"error": f"Invalid day_type: {day_type}. Must be weekday, saturday, or holiday"}), 400

        if direction and direction not in ("up", "down"):
            return jsonify({"error": f"Invalid direction: {direction}. Must be up or down"}), 400

        db = _get_db()
        station_query = station.strip()
        station_lower = station_query.lower()

        # Query all subway stations and filter by name match
        docs = db.collection("subway_stations").stream()
        matches: list[dict[str, Any]] = []

        for doc in docs:
            data = doc.to_dict()
            sname = data.get("station_name", {})
            name_ko = sname.get("ko", "")
            name_en = sname.get("en", "")
            name_match = (name_ko == station_query or name_en.lower() == station_lower)

            if not name_match:
                continue

            sline = data.get("line", "")
            if line and sline != line:
                continue

            # Extract the requested timetable slice
            timetable_full = data.get("timetable", {})
            day_data = timetable_full.get(day_type, {})

            entry: dict[str, Any] = {
                "station_id": data.get("station_id"),
                "station_name": sname,
                "line": sline,
                "line_name": data.get("line_name", {}),
                "day_type": day_type,
                "transfer_lines": data.get("transfer_lines", []),
            }

            if direction == "up":
                entry["timetable"] = {"up": day_data.get("up", [])}
            elif direction == "down":
                entry["timetable"] = {"down": day_data.get("down", [])}
            else:
                entry["timetable"] = {
                    "up": day_data.get("up", []),
                    "down": day_data.get("down", []),
                }

            matches.append(entry)

        if not matches:
            # Return available stations for helpful error message
            all_docs = db.collection("subway_stations").stream()
            available = sorted(set(
                f"{d.to_dict().get('station_name', {}).get('ko', '')} ({d.to_dict().get('station_name', {}).get('en', '')})"
                for d in all_docs
            ))
            return jsonify({
                "error": f"Station not found: '{station}'",
                "available_stations": available,
            }), 404

        return jsonify({"count": len(matches), "results": matches})

    return app
