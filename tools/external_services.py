"""NanoHA External Services — weather, calendar, news via public APIs."""

import logging
import os

import httpx

from tools.constants import DEFAULT_TIMEOUT

log = logging.getLogger(__name__)


def get_weather(lat: float | None = None, lon: float | None = None) -> dict:
    """Get current weather and 3-day forecast via Open-Meteo (free, no API key).

    If lat/lon not provided, attempts to read from HA config.
    """
    if lat is None or lon is None:
        from tools.ha_client import ws_send
        config = ws_send({"type": "get_config"})
        if config.get("success"):
            lat = config["result"].get("latitude")
            lon = config["result"].get("longitude")
        if lat is None or lon is None:
            return {"success": False, "error": "Location not configured. Provide lat/lon or set location in HA."}

    try:
        resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=DEFAULT_TIMEOUT,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.error("Weather API failed: %s", e)
        return {"success": False, "error": f"Cannot fetch weather: {e}"}

    if resp.status_code != 200:
        return {"success": False, "error": f"Weather API returned {resp.status_code}"}

    data = resp.json()
    current = data.get("current", {})
    daily = data.get("daily", {})

    weather_codes = {
        0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
        55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
        71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Light showers",
        81: "Showers", 82: "Heavy showers", 95: "Thunderstorm",
    }

    forecast = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        forecast.append({
            "date": date,
            "high": daily.get("temperature_2m_max", [None])[i],
            "low": daily.get("temperature_2m_min", [None])[i],
            "condition": weather_codes.get(daily.get("weather_code", [0])[i], "Unknown"),
        })

    return {
        "success": True,
        "current": {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "condition": weather_codes.get(current.get("weather_code", 0), "Unknown"),
        },
        "forecast": forecast,
    }


def get_news(query: str = "technology", count: int = 5) -> dict:
    """Get news headlines via a public RSS-to-JSON proxy.

    Uses Google News RSS feed parsed client-side. No API key needed.
    """
    try:
        resp = httpx.get(
            f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.error("News fetch failed: %s", e)
        return {"success": False, "error": f"Cannot fetch news: {e}"}

    if resp.status_code != 200:
        return {"success": False, "error": f"News API returned {resp.status_code}"}

    # Parse RSS XML minimally
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(resp.text)
        items = root.findall(".//item")[:count]
        headlines = []
        for item in items:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            headlines.append({"title": title, "link": link, "published": pub_date})
    except ET.ParseError:
        return {"success": False, "error": "Cannot parse news feed."}

    return {"success": True, "query": query, "count": len(headlines), "headlines": headlines}
