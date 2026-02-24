"""Data loader — reads from Firestore at startup, caches in memory.

Credential resolution order:
  1. FIREBASE_CREDENTIALS_BASE64 env var (for Smithery / production)
  2. GOOGLE_APPLICATION_CREDENTIALS env var (standard GCP)
  3. Local fallback JSON files in src/data/ (development only)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from pathlib import Path

from src.models.place import Place
from src.models.subway import SubwayStation

logger = logging.getLogger(__name__)

_places: list[Place] = []
_subway_stations: list[SubwayStation] = []
_loaded = False


def _init_firestore():
    """Initialize Firebase and return Firestore client, or None if unavailable."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Already initialized?
        try:
            app = firebase_admin.get_app()
            return firestore.client()
        except ValueError:
            pass

        # Option 1: Base64-encoded credentials (Smithery / Docker)
        b64_creds = os.environ.get("FIREBASE_CREDENTIALS_BASE64")
        if b64_creds:
            cred_json = base64.b64decode(b64_creds).decode("utf-8")
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from FIREBASE_CREDENTIALS_BASE64")
            return firestore.client()

        # Option 2: Standard GOOGLE_APPLICATION_CREDENTIALS
        gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if gac and Path(gac).exists():
            cred = credentials.Certificate(gac)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from GOOGLE_APPLICATION_CREDENTIALS")
            return firestore.client()

        logger.info("No Firebase credentials found")
        return None

    except ImportError:
        logger.info("firebase-admin not installed, using local fallback")
        return None
    except Exception as e:
        logger.warning(f"Firebase init failed: {e}, using local fallback")
        return None


def _load_from_firestore(db) -> bool:
    """Load all data from Firestore into memory. Returns True on success."""
    global _places, _subway_stations

    try:
        # Load places
        logger.info("Loading places from Firestore...")
        places_ref = db.collection("places")
        places_docs = places_ref.stream()
        raw_places = [doc.to_dict() for doc in places_docs]
        _places = [Place(**p) for p in raw_places]
        logger.info(f"Loaded {len(_places)} places from Firestore")

        # Load subway stations
        logger.info("Loading subway stations from Firestore...")
        subway_ref = db.collection("subway_stations")
        subway_docs = subway_ref.stream()
        raw_subway = [doc.to_dict() for doc in subway_docs]
        _subway_stations = [SubwayStation(**s) for s in raw_subway]
        logger.info(f"Loaded {len(_subway_stations)} subway stations from Firestore")

        return True

    except Exception as e:
        logger.warning(f"Firestore load failed: {e}")
        return False


def _load_from_local() -> bool:
    """Load from local JSON files (development fallback). Returns True on success."""
    global _places, _subway_stations

    data_dir = Path(__file__).parent

    places_path = data_dir / "places.json"
    subway_path = data_dir / "subway.json"

    if not places_path.exists():
        logger.error(f"Local places.json not found at {places_path}")
        return False

    with open(places_path, "r", encoding="utf-8") as f:
        raw_places = json.load(f)
        _places = [Place(**p) for p in raw_places]

    if subway_path.exists():
        with open(subway_path, "r", encoding="utf-8") as f:
            raw_subway = json.load(f)
            _subway_stations = [SubwayStation(**s) for s in raw_subway]

    logger.info(f"Loaded {len(_places)} places, {len(_subway_stations)} stations from local JSON")
    return True


def load_data() -> None:
    """Load all data into memory. Tries Firestore first, falls back to local JSON."""
    global _loaded
    if _loaded:
        return

    # Try Firestore
    db = _init_firestore()
    if db and _load_from_firestore(db):
        _loaded = True
        return

    # Fallback to local JSON
    if _load_from_local():
        _loaded = True
        return

    logger.error("Failed to load data from any source!")


def get_places() -> list[Place]:
    return _places


def get_subway_stations() -> list[SubwayStation]:
    return _subway_stations
