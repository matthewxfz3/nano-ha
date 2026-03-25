"""Tests for external_services tools."""

from unittest.mock import MagicMock, patch

import httpx

from tools.external_services import get_news, get_weather

MOCK_WEATHER_RESP = {
    "current": {
        "temperature_2m": 18.5,
        "relative_humidity_2m": 65,
        "weather_code": 2,
        "wind_speed_10m": 12.3,
    },
    "daily": {
        "time": ["2026-03-24", "2026-03-25", "2026-03-26"],
        "temperature_2m_max": [20, 22, 19],
        "temperature_2m_min": [12, 14, 11],
        "weather_code": [0, 3, 61],
    },
}

MOCK_NEWS_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item><title>AI Advances in 2026</title><link>https://example.com/1</link><pubDate>Mon, 24 Mar 2026</pubDate></item>
<item><title>Smart Home Trends</title><link>https://example.com/2</link><pubDate>Mon, 24 Mar 2026</pubDate></item>
</channel></rss>"""


class TestGetWeather:
    @patch("tools.external_services.httpx.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: MOCK_WEATHER_RESP)
        result = get_weather(lat=37.7749, lon=-122.4194)
        assert result["success"] is True
        assert result["current"]["temperature"] == 18.5
        assert result["current"]["condition"] == "Partly cloudy"
        assert len(result["forecast"]) == 3
        assert result["forecast"][0]["high"] == 20

    @patch("tools.external_services.httpx.get")
    def test_api_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        result = get_weather(lat=0, lon=0)
        assert result["success"] is False

    @patch("tools.external_services.httpx.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("No internet")
        result = get_weather(lat=0, lon=0)
        assert result["success"] is False

    def test_no_location(self):
        with patch("tools.ha_client.ws_send", return_value={"success": False}):
            result = get_weather()
            assert result["success"] is False
            assert "Location" in result["error"]


class TestGetNews:
    @patch("tools.external_services.httpx.get")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text=MOCK_NEWS_RSS)
        result = get_news(query="technology", count=5)
        assert result["success"] is True
        assert result["count"] == 2
        assert result["headlines"][0]["title"] == "AI Advances in 2026"

    @patch("tools.external_services.httpx.get")
    def test_api_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        result = get_news()
        assert result["success"] is False

    @patch("tools.external_services.httpx.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        result = get_news()
        assert result["success"] is False
