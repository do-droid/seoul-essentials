import logging
import os

from fastmcp import FastMCP

from src.data.loader import get_places, get_subway_stations, load_data

logging.basicConfig(level=logging.INFO)
from src.tools.find_nearby import find_nearby
from src.tools.find_places import find_places
from src.tools.get_detail import get_place_detail
from src.tools.subway import get_subway_timetable

mcp = FastMCP(
    name="seoul-essentials",
    instructions=(
        "Seoul Essentials provides essential public facility data for foreign tourists visiting Seoul, South Korea. "
        "Available data: public restrooms (toilet), pharmacies with language support (pharmacy), "
        "free WiFi hotspots (wifi), AED/defibrillator locations (aed), tourist information centers (tourist_info), "
        "and subway timetables. All data is bilingual (Korean/English). "
        "Use find_places for filtered search by type and district, "
        "get_place_detail for complete info on a specific place, "
        "find_nearby for GPS-based proximity search, "
        "and get_subway_timetable for train schedules."
    ),
)

mcp.tool(find_places)
mcp.tool(get_place_detail)
mcp.tool(find_nearby)
mcp.tool(get_subway_timetable)


def main():
    load_data()
    logger = logging.getLogger(__name__)
    logger.info(f"Data ready: {len(get_places())} places, {len(get_subway_stations())} subway stations")
    port = int(os.environ.get("PORT", "8081"))
    mcp.run(transport="http", host="0.0.0.0", port=port, stateless_http=True)


if __name__ == "__main__":
    main()
