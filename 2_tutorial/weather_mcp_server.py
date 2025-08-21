# weather_mcp_server.py
import requests
from typing import Optional, List, Literal, Dict, Any
from fastmcp import FastMCP

mcp = FastMCP(name="Weather MCP Server", instructions="Provides current weather and simple forecasts by city.")

# --- Helpers -----------------------------------------------------------------

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def _choose_match(results: List[Dict[str, Any]], country_code: Optional[str], state: Optional[str]) -> Dict[str, Any]:
    """Pick the best geocoding match, optionally filtering by country/state."""
    if not results:
        raise ValueError("No matching locations found.")
    filtered = results
    if country_code:
        cc = country_code.strip().upper()
        filtered = [r for r in filtered if r.get("country_code", "").upper() == cc] or filtered
    if state:
        s = state.lower().strip()
        filtered = [r for r in filtered if (r.get("admin1") or "").lower() == s] or filtered
    # Prefer largest population if multiple remain
    filtered.sort(key=lambda r: r.get("population", 0), reverse=True)
    return filtered[0]

def _geocode_city(name: str, country_code: Optional[str], state: Optional[str], lang: str) -> Dict[str, Any]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": 10, "language": lang or "en", "format": "json"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Geocoding failed: HTTP {r.status_code}")
    data = r.json()
    return _choose_match(data.get("results", []), country_code, state)

def _units_params(units: Literal["metric", "imperial"]) -> Dict[str, str]:
    if units == "imperial":
        return {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch"}
    return {"temperature_unit": "celsius", "wind_speed_unit": "ms", "precipitation_unit": "mm"}

# --- Tools -------------------------------------------------------------------

@mcp.tool()
def get_current_weather(
    city: str,
    country_code: Optional[str] = None,
    state: Optional[str] = None,
    units: Literal["metric", "imperial"] = "metric",
    lang: str = "en",
) -> dict:
    """
    Get current weather for a city. Optionally disambiguate with country_code (e.g., 'SE', 'US')
    and state/region name. Units: 'metric' or 'imperial'.
    """
    loc = _geocode_city(city, country_code, state, lang)
    lat, lon = loc["latitude"], loc["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "is_day",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
        ]),
        "timezone": "auto",
        **_units_params(units),
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Weather fetch failed: HTTP {r.status_code}")
    data = r.json()
    cur = data.get("current") or {}
    code = int(cur.get("weather_code")) if cur.get("weather_code") is not None else None

    return {
        "location": {
            "name": loc.get("name"),
            "country": loc.get("country"),
            "country_code": loc.get("country_code"),
            "admin1": loc.get("admin1"),
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone"),
        },
        "current": {
            "observed_at": cur.get("time"),
            "temperature": cur.get("temperature_2m"),
            "temperature_unit": "°F" if units == "imperial" else "°C",
            "relative_humidity": cur.get("relative_humidity_2m"),
            "precipitation": cur.get("precipitation"),
            "wind_speed": cur.get("wind_speed_10m"),
            "wind_direction": cur.get("wind_direction_10m"),
            "is_day": bool(cur.get("is_day")) if cur.get("is_day") is not None else None,
            "weather_code": code,
            "weather_description": WEATHER_CODE_MAP.get(code, "Unknown"),
        },
        "units": units,
        "source": "Open-Meteo",
    }

@mcp.tool()
def get_daily_forecast(
    city: str,
    days: int = 3,
    country_code: Optional[str] = None,
    state: Optional[str] = None,
    units: Literal["metric", "imperial"] = "metric",
    lang: str = "en",
) -> dict:
    """
    Get a simple daily forecast for the next `days` (1–7 recommended).
    """
    if days < 1 or days > 16:
        raise ValueError("days must be between 1 and 16 (Open-Meteo limit).")

    loc = _geocode_city(city, country_code, state, lang)
    lat, lon = loc["latitude"], loc["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ]),
        "forecast_days": days,
        "timezone": "auto",
        **_units_params(units),
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Forecast fetch failed: HTTP {r.status_code}")
    data = r.json()
    daily = data.get("daily") or {}
    out = []
    times = daily.get("time", []) or []
    for i, date in enumerate(times):
        code = int(daily["weather_code"][i]) if daily.get("weather_code") else None
        out.append({
            "date": date,
            "weather_code": code,
            "weather_description": WEATHER_CODE_MAP.get(code, "Unknown"),
            "temp_min": daily.get("temperature_2m_min", [None]*len(times))[i],
            "temp_max": daily.get("temperature_2m_max", [None]*len(times))[i],
            "precipitation_sum": daily.get("precipitation_sum", [None]*len(times))[i],
            "wind_speed_max": daily.get("wind_speed_10m_max", [None]*len(times))[i],
        })

    return {
        "location": {
            "name": loc.get("name"),
            "country": loc.get("country"),
            "country_code": loc.get("country_code"),
            "admin1": loc.get("admin1"),
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone"),
        },
        "daily": out,
        "units": units,
        "source": "Open-Meteo",
    }

# --- Server entrypoint -------------------------------------------------------

if __name__ == "__main__":
    # Run the server over HTTP transport with streaming support
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
