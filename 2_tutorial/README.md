# Tutorial 2 — Weather MCP Server & UI ⛅

A practical example showing how an LLM can **plan** weather queries and then **execute** them through a **Model Context Protocol (MCP)** server.  
You’ll run a FastMCP server that wraps the **Open-Meteo** APIs and a Streamlit UI that asks an LLM to output a **JSON plan of tool calls**.

---

## What you’ll learn

- How to expose weather functions as MCP **tools** over HTTP.
- How to let an LLM **plan** tool calls (the LLM doesn’t fetch weather itself).
- How a Streamlit UI can **execute** those tools and render rich results.

---

## Folder contents

```
2_tutorial/
├── README.md                 # This file
├── weather_mcp_server.py     # FastMCP server (Open-Meteo geocoding + forecast)
└── ui.py                     # Streamlit app that plans + executes tool calls
```
---

## Run

Open **two terminals**.

### Terminal 1 — start the MCP server
```bash
cd 2_tutorial
python weather_mcp_server.py
```
- Starts FastMCP on `http://0.0.0.0:8000/mcp` (listens on port **8000**).

### Terminal 2 — start the UI
```bash
cd 2_tutorial
streamlit run ui.py
```
- Opens a local web UI.
- The app reads:
  - **Model**: defaults to `"gpt-3.5-turbo"` (editable in the sidebar).
  - **MCP base URL**: `http://127.0.0.1:8000/mcp` (editable via env; see below).

---

## How it works (quick)

1. You enter a natural-language weather question, e.g.  
   “**Weather in Södertälje now and 5-day forecast?**”
2. The LLM replies with a **JSON array** of tool calls, e.g.
   ```json
   [
     {"func": "get_current_weather", "city": "Södertälje", "country_code": "SE", "units": "metric"},
     {"func": "get_daily_forecast", "city": "Södertälje", "country_code": "SE", "days": 5, "units": "metric"}
   ]
   ```
3. The UI executes each tool against the MCP server and renders:
   - Current conditions (temperature, humidity, wind, description…)
   - A tabular/charted daily forecast

> The planner can also reference earlier outputs with `RESULT_N`.  
> In this app, such a reference will pass the **entire prior output object** into a later call.

---

## MCP tools (server)

### `get_current_weather`
```text
get_current_weather(
  city: str,
  country_code: Optional[str] = None,   # e.g., "SE", "US"
  state: Optional[str] = None,          # region/admin1 (e.g., "California")
  units: Literal["metric","imperial"] = "metric",
  lang: str = "en"
) -> dict
```
**Returns (shape):**
```json
{
  "location": {
    "name": "...", "country": "...", "country_code": "...", "admin1": "...",
    "latitude": 59.2, "longitude": 17.6, "timezone": "Europe/Stockholm"
  },
  "current": {
    "observed_at": "2025-08-22T10:10",
    "temperature": 17.3, "temperature_unit": "°C",
    "relative_humidity": 62,
    "precipitation": 0.0,
    "wind_speed": 3.5, "wind_direction": 240,
    "is_day": true,
    "weather_code": 3,
    "weather_description": "Overcast"
  },
  "units": "metric",
  "source": "Open-Meteo"
}
```

### `get_daily_forecast`
```text
get_daily_forecast(
  city: str,
  days: int = 3,                         # 1..16 (Open-Meteo limit)
  country_code: Optional[str] = None,
  state: Optional[str] = None,
  units: Literal["metric","imperial"] = "metric",
  lang: str = "en"
) -> dict
```
**Returns (shape):**
```json
{
  "location": { "...": "..." },
  "daily": [
    {
      "date": "2025-08-22",
      "weather_code": 3,
      "weather_description": "Overcast",
      "temp_min": 12.1,
      "temp_max": 19.8,
      "precipitation_sum": 0.8,
      "wind_speed_max": 7.2
    }
  ],
  "units": "metric",
  "source": "Open-Meteo"
}
```

> The server uses Open-Meteo **geocoding** to resolve `city` (optionally filtered by `country_code` and `state`) and then calls the forecast API with correct units.

---


## Sample prompts

- `Weather in Södertälje right now`
- `Current weather in Stockholm and a 3-day forecast`
- `Give me today’s weather and a 5-day outlook for London in imperial units`
- `Show weather for San Jose, state California, US`
- `Weather in Paris (French language) and 2-day forecast`

---

## Troubleshooting

- **UI error: “OpenAI API key is not set”**  
  Ensure `OPENAI_API_KEY` is exported **in the same shell** where you run `streamlit`.

- **Connection refused / cannot reach MCP**  
  Start the server first (Terminal 1). Confirm `MCP_BASE_URL` is `http://127.0.0.1:8000/mcp`.

- **Port 8000 already in use**  
  Stop the conflicting process or change the port in `weather_mcp_server.py` and update `MCP_BASE_URL`.

- **Ambiguous city results**  
  Provide `country_code` (e.g., `GB`) and/or `state` (e.g., `California`) in your prompt.

- **Out-of-range forecast days**  
  The server enforces `1 ≤ days ≤ 16`.

---

## Extend the tutorial (ideas)

- Add hourly forecasts and precipitation probability to the tool outputs.
- Cache geocoding/forecast responses to reduce external API calls.
- Localize the UI (units, language) and add sidebar controls for quick toggling.
- Add simple **retry/backoff** for transient HTTP errors.

---

## Notes on data sources

- Weather data and geocoding by **Open-Meteo**.  
- Values are best-effort and may differ from other providers.

---

## License

MIT — please use and adapt freely.
