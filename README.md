# Seoul Essentials — MCP Server

Essential public facility data for AI agents helping foreign tourists in Seoul, South Korea.

<a href="https://glama.ai/mcp/servers/@do-droid/seoul-essentials">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@do-droid/seoul-essentials/badge" alt="seoul-essentials MCP server" />
</a>

## What is this?

Seoul Essentials is an MCP (Model Context Protocol) server that provides structured data about essential public facilities in Seoul. Designed for AI agents that assist foreign tourists with real-time queries about nearby services.

## Available Data (30,000+ places, 17 types)

| Type | Description | Count |
|------|-------------|-------|
| `toilet` | Public restrooms across all 25 districts | 4,452 |
| `pharmacy` | Pharmacies with foreign language support (English/Chinese/Japanese) | 417 |
| `wifi` | Free public WiFi hotspots (Seoul WiFi) | 7,251 |
| `aed` | AED (defibrillator) locations | 10,000 |
| `tourist_info` | Tourist information centers | 16 |
| `baeknyeon` | Century-old designated shops & restaurants | 168 |
| `bike` | 따릉이 (Seoul Bike) sharing stations | ~2,700 |
| `future_heritage` | Seoul Future Heritage sites | ~470 |
| `heritage` | Designated cultural properties | ~600 |
| `museum` | Museums & galleries | ~210 |
| `park` | Major parks | ~130 |
| `taxi_stand` | Taxi stands | ~370 |
| `metro_facility` | Subway lockers & facilities | ~290 |
| `tourist_zone` | Tourist special zones | 8 |
| `post_office` | Post offices (EMS / international mail) | 227 |
| `traditional_market` | Korean traditional markets (Gwangjang, Namdaemun, ...) | 433 |
| `ev_charger` | EV charging stations | 187 |
| `subway` | Subway timetables for major stations | 10 stations |

## MCP Tools

### `find_places`
Search for public facilities by type and conditions.

**Parameters:**
- `type` (required): one of the 17 types listed above (e.g., `"toilet"`, `"pharmacy"`, `"post_office"`, `"traditional_market"`, `"ev_charger"`)
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

**English**
- "Find an English-speaking pharmacy near Gangnam Station"
- "Where is the nearest public restroom to my location?"
- "What's the subway schedule at Myeongdong Station?"
- "Find free WiFi hotspots in Hongdae area"
- "Where is the closest AED to Itaewon?"

**日本語**
- 「明洞で日本語が通じる薬局を探して」
- 「弘大の近くで無料Wi-Fiが使える場所は？」
- 「江南駅周辺のEV充電スポットを教えて」

**中文**
- "在明洞附近找会说中文的药店"
- "弘大附近哪里有24小时便利的公共厕所？"
- "梨泰院附近的清真餐厅在哪里？"

## Feedback

We actively review and incorporate feedback to improve data quality and coverage.

**For AI agents:** Use the `submit_feedback` tool during a conversation to report issues or suggest improvements.

**For developers:** [Open a feedback issue](https://github.com/do-droid/seoul-essentials/issues/new?template=feedback.yml) on GitHub.

**Categories:** `new_data` | `data_quality` | `coverage` | `format` | `frequency` | `other`

## Known Data Limitations

- **`pharmacy`**: Sourced from Seoul Open Data Plaza's "Foreign-language Capable Pharmacy Status" dataset, which lists only pharmacies that confirmed English/Chinese/Japanese service. **Gangnam-gu is not represented in the upstream dataset** (origin gap, not a parser bug). Coordinates fall back to the district centroid because the upstream rows do not carry lat/lng. We have requested expanded coverage from Seoul Open Data Plaza for the next refresh.
- **`post_office` / `traditional_market` / `ev_charger`**: Upstream datasets do not include lat/lng. Coordinates fall back to the centroid of each Seoul district (`coordinates_approximate: true`). District-level filters (`?district=mapo`) are exact; `find_nearby` ranking against these types is district-grained rather than building-grained.
- **Roadmap (next round)**: `halal_friendly` (data.go.kr 15111159 was withdrawn — searching alternative sources) and `emergency_room` (data.go.kr 3043449 not findable — switching to e-gen.or.kr OpenAPI) are planned for the following refresh.

## Data Sources

All data sourced from official Seoul government open data:

- [Seoul Open Data Plaza (data.seoul.go.kr)](https://data.seoul.go.kr)
- [Korea Open Data Portal (data.go.kr)](https://www.data.go.kr)

## License

MIT