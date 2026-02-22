import json
from pathlib import Path

from src.models.place import Place
from src.models.subway import SubwayStation

_places: list[Place] = []
_subway_stations: list[SubwayStation] = []
_loaded = False


def load_data() -> None:
    global _places, _subway_stations, _loaded
    if _loaded:
        return

    data_dir = Path(__file__).parent

    with open(data_dir / "places.json", "r", encoding="utf-8") as f:
        raw_places = json.load(f)
        _places = [Place(**p) for p in raw_places]

    with open(data_dir / "subway.json", "r", encoding="utf-8") as f:
        raw_subway = json.load(f)
        _subway_stations = [SubwayStation(**s) for s in raw_subway]

    _loaded = True


def get_places() -> list[Place]:
    return _places


def get_subway_stations() -> list[SubwayStation]:
    return _subway_stations
