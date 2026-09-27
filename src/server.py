import inspect
import logging
import os

from fastmcp import FastMCP

from src.data.api_client import health_check, init_client
from src.middleware import ArgumentRepairMiddleware, ClientInfoLogMiddleware

logging.basicConfig(level=logging.INFO)
from src.tools.feedback import submit_feedback
from src.tools.find_nearby import find_nearby
from src.tools.find_places import find_places
from src.tools.get_detail import get_place_detail
from src.tools.subway import get_subway_timetable

mcp = FastMCP(
    name="seoul-essentials",
    version="0.9.0",
    instructions=(
        "Seoul Essentials provides essential public facility data for foreign tourists visiting Seoul, South Korea. "
        "Available data (17 types): public restrooms (toilet), pharmacies citywide with a "
        "foreign-language flag (pharmacy), "
        "free WiFi hotspots (wifi), AED/defibrillator locations (aed), tourist information centers (tourist_info), "
        "century-old designated restaurants and shops (baeknyeon), "
        "따릉이 bike-sharing stations (bike), Seoul Future Heritage sites (future_heritage), "
        "designated cultural properties (heritage), museums and galleries (museum), "
        "major parks (park), taxi stands (taxi_stand), "
        "subway lockers (metro_facility), tourist special zones (tourist_zone), "
        "post offices with EMS / international mail (post_office), "
        "Korean traditional markets such as Gwangjang and Namdaemun (traditional_market), "
        "EV charging stations (ev_charger), "
        "and subway timetables. Addresses are available in English for most records, but place NAMES are currently Korean-only except for post offices — romanize them for the user rather than expecting name.en. "
        "There is no name or keyword search — pick a type (and optionally a district). "
        "Use find_places for filtered search by type and district, "
        "get_place_detail for complete info on a specific place, "
        "find_nearby for GPS-based proximity search, "
        "and get_subway_timetable for train schedules. "
        "If you notice missing data, inaccurate information, or have suggestions for improvement, "
        "please use the submit_feedback tool. Feedback is read by the maintainer."
    ),
)

_TOOLS = (find_places, get_place_detail, find_nearby, get_subway_timetable, submit_feedback)
for _fn in _TOOLS:
    mcp.tool(_fn)

mcp.add_middleware(ClientInfoLogMiddleware())
mcp.add_middleware(ArgumentRepairMiddleware(
    {fn.__name__: list(inspect.signature(fn).parameters) for fn in _TOOLS}))


def main():
    logger = logging.getLogger(__name__)
    if not os.environ.get("CLIENT_ID_SECRET"):
        logger.warning("CLIENT_ID_SECRET is not set: analytics events will carry no "
                       "client_hash or gateway_key_hash (callers cannot be told apart)")
    init_client()
    status = health_check()
    logger.info(f"API backend: {status}")
    port = int(os.environ.get("PORT", "8081"))
    mcp.run(transport="http", host="0.0.0.0", port=port, stateless_http=True)


if __name__ == "__main__":
    main()
