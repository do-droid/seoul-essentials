# Seoul Essentials — MCP Server

Essential public facility data for AI agents helping foreign tourists in Seoul, South Korea.

## What is this?

Seoul Essentials is an MCP (Model Context Protocol) server that provides structured data about essential public facilities in Seoul. Designed for AI agents that assist foreign tourists with real-time queries about nearby services.

## Available Data (22,000+ places)

| Type | Description | Count |
|------|-------------|-------|
| `toilet` | Public restrooms across all 25 districts | 4,452 |
| `pharmacy` | Pharmacies with foreign language support | 417 |
| `wifi` | Free public WiFi hotspots (Seoul WiFi) | 7,251 |
| `aed` | AED (defibrillator) locations | 10,000 |
| `tourist_info` | Tourist information centers | 16 |
| `subway` | Subway timetables for major stations | 10 stations |

## MCP Tools

### `find_places`
Search for public facilities by type and conditions.

**Parameters:**
- `type` (required): `"toilet"` | `"pharmacy"` | `"wifi"` | `"aed"` | `"tourist_info"`
- `district` (optional): Seoul district name in English or Korean (e.g., `"gangnam"`, `"강남구"`)
- `filters` (optional): Service-specific filters (e.g., `{"english": true}`, `{"is_24h": true}`, `{"indoor": true}`)
- `limit` (optional): Max results, 1-50 (default: 10)

### `get_place_detail`
Get full details of a specific place by its ID.

**Parameters:**
- `id` (required): Place ID (e.g., `"toilet_00001"`, `"pharmacy_001"`, `"aed_00001"`)

### `find_nearby`
Find public facilities near GPS coordinates, sorted by distance.

**Parameters:**
- `lat` (required): Latitude (Seoul range: ~37.4 to ~37.7)
- `lng` (required): Longitude (Seoul range: ~126.7 to ~127.2)
- `radius_m` (optional): Search radius in meters, 100-5000 (default: 500)
- `type` (optional): Filter by facility type
- `limit` (optional): Max results, 1-20 (default: 5)

### `get_subway_timetable`
Get subway timetable for a specific station.

**Parameters:**
- `station` (required): Station name in Korean or English (e.g., `"강남"` or `"Gangnam"`)
- `line` (optional): Line number (e.g., `"2"`)
- `day_type` (optional): `"weekday"` | `"saturday"` | `"holiday"` (default: `"weekday"`)
- `direction` (optional): `"up"` | `"down"`

## Quick Start

### Option A: Smithery (Recommended)

Visit [Seoul Essentials on Smithery](https://smithery.ai/servers/do-droid/seoul-essentials) and follow the setup instructions for your MCP client.

### Option B: Direct Connection

Add to your MCP client config (e.g., Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "seoul-essentials": {
      "url": "https://seoul-essentials-mcp-230987091625.asia-northeast3.run.app/mcp"
    }
  }
}
```

### Option C: Run Locally

```bash
git clone https://github.com/do-droid/seoul-essentials.git
cd seoul-essentials
API_BASE_URL="https://asia-northeast3-seoul-essentials.cloudfunctions.net/api" \
uv run python -m src.server
```

## Example Queries

An AI agent can use these tools to answer questions like:

- "Find an English-speaking pharmacy near Gangnam Station"
- "Where is the nearest public restroom to my location?"
- "What's the subway schedule at Myeongdong Station?"
- "Find free WiFi hotspots in Hongdae area"
- "Where is the closest AED to Itaewon?"

## Data Sources

All data sourced from official Seoul government open data:

- [Seoul Open Data Plaza (data.seoul.go.kr)](https://data.seoul.go.kr)
- [Korea Open Data Portal (data.go.kr)](https://www.data.go.kr)

## License

MIT
