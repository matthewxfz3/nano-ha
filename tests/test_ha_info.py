"""Tests for ha_info tools."""

from unittest.mock import MagicMock, patch

from tools.ha_info import get_config, get_history, health_check


class TestGetHistory:
    @patch("tools.ha_info.rest_get")
    def test_found(self, mock_rest):
        mock_rest.return_value = {
            "success": True,
            "data": [
                [
                    {"entity_id": "sensor.temp", "state": "22", "last_changed": "2026-03-24T10:00:00Z"},
                    {"entity_id": "sensor.temp", "state": "23", "last_changed": "2026-03-24T11:00:00Z"},
                ]
            ],
        }
        result = get_history("sensor.temp", hours=24)
        assert result["success"] is True
        assert result["count"] == 2
        assert result["history"][0]["state"] == "22"

    @patch("tools.ha_info.rest_get")
    def test_not_found(self, mock_rest):
        mock_rest.return_value = {"success": True, "data": []}
        result = get_history("sensor.nonexistent")
        assert result["success"] is True
        assert result["count"] == 0

    @patch("tools.ha_info.rest_get")
    def test_api_failure(self, mock_rest):
        mock_rest.return_value = {"success": False, "error": "timeout"}
        result = get_history("sensor.temp")
        assert result["success"] is False


class TestHealthCheck:
    @patch("tools.ha_info.subprocess.run")
    @patch("tools.ha_info.httpx.get")
    def test_all_healthy(self, mock_get, mock_run):
        mock_get.return_value = MagicMock(status_code=200)
        mock_run.return_value = MagicMock(returncode=0, stdout='{"Name":"ha"}')
        result = health_check()
        assert result["success"] is True
        assert result["services"]["homeassistant"] is True

    @patch("tools.ha_info.subprocess.run")
    @patch("tools.ha_info.httpx.get")
    def test_ha_down(self, mock_get, mock_run):
        mock_get.side_effect = Exception("Connection refused")
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = health_check()
        assert result["services"]["homeassistant"] is False
        assert result["all_healthy"] is False


class TestGetConfig:
    @patch("tools.ha_info.ws_send")
    def test_success(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": {
                "location_name": "NanoHA",
                "version": "2026.3.3",
                "unit_system": {"temperature": "°C"},
                "components": ["light", "sensor", "automation"],
            },
        }
        result = get_config()
        assert result["success"] is True
        assert result["version"] == "2026.3.3"
        assert "light" in result["components"]

    @patch("tools.ha_info.ws_send")
    def test_failure(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": "auth_failed"}
        result = get_config()
        assert result["success"] is False
