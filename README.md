# Seoul Essentials — MCP Server

Essential public facility data for AI agents helping foreign tourists in Seoul, South Korea.

## What is this?

Seoul Essentials is an MCP (Model Context Protocol) server that provides structured, bilingual (Korean/English) data about essential public facilities in Seoul. Designed for AI agents that assist foreign tourists with real-time queries about nearby services.

## Available Data

| Type | Description | Sample Count |
|------|-------------|-------------|
| `toilet` | Public restrooms (subway stations, parks, landmarks) | 15 |
| `pharmacy` | Pharmacies with language support & 24hr availability | 15 |
| `wifi` | Free public WiFi hotspots | 15 |
| `aed` | AED (Automated External Defibrillator) locations | 15 |
| `tourist_info` | Tourist information centers | 10 |
| `subway` | Subway timetables for major stations | 10 stations |

> Coverage is expanding — full Seoul dataset (15,000+ places) coming soon.

## MCP Tools

### `find_places`
Search for public facilities by type and conditions.

**Parameters:**
- `type` (required): `"toilet"` | `"pharmacy"` | `"wifi"` | `"aed"` | `"tourist_info"`
- `district` (optional): Seoul district name (e.g., `"gangnam"`, `"jongno"`, `"mapo"`)
- `filters` (optional): Service-specific filters (e.g., `{"english_spoken": true}`)
- `limit` (optional): Max results (default: 10)

### `get_place_detail`
Get full details of a specific place by its ID.

**Parameters:**
- `id` (required): Place ID (e.g., `"kr-pharmacy-gangnam-001"`)

### `find_nearby`
Find public facilities near GPS coordinates, sorted by distance.

**Parameters:**
- `lat` (required): Latitude
- `lng` (required): Longitude
- `radius_m` (optional): Search radius in meters (default: 500)
- `type` (optional): Filter by facility type
- `limit` (optional): Max results (default: 5)

### `get_subway_timetable`
Get subway timetable for a specific station.

**Parameters:**
- `station` (required): Station name in Korean or English (e.g., `"강남"` or `"Gangnam"`)
- `line` (optional): Line number (e.g., `"2"`)
- `day_type` (optional): `"weekday"` | `"saturday"` | `"holiday"` (default: `"weekday"`)
- `direction` (optional): `"up"` | `"down"`

## Example Queries

An AI agent can use these tools to answer questions like:

- "Find an English-speaking pharmacy near Gangnam Station"
- "Where is the nearest public restroom to my location?"
- "What's the subway schedule at Myeongdong Station?"
- "Find free WiFi hotspots in Hongdae area"
- "Where is the closest AED to Itaewon?"

## Data Sources

- [Korea Open Data Portal (data.go.kr)](https://www.data.go.kr)
- [Seoul Open Data Plaza (data.seoul.go.kr)](https://data.seoul.go.kr)

## License

MIT
