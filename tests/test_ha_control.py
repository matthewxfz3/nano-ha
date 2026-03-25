"""Tests for ha_control tools."""

from unittest.mock import patch

import pytest

from tools.ha_control import call_service, get_entity_state, list_entities

MOCK_STATES = {
    "success": True,
    "result": [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "brightness": 200},
            "last_changed": "2026-03-24T10:00:00Z",
            "last_updated": "2026-03-24T10:00:00Z",
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {"friendly_name": "Bedroom Light"},
            "last_changed": "2026-03-24T09:00:00Z",
            "last_updated": "2026-03-24T09:00:00Z",
        },
        {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {"friendly_name": "Temperature", "unit_of_measurement": "°C"},
            "last_changed": "2026-03-24T10:05:00Z",
            "last_updated": "2026-03-24T10:05:00Z",
        },
    ],
}


class TestListEntities:
    @patch("tools.ha_control.ws_send", return_value=MOCK_STATES)
    def test_list_all(self, mock_ws):
        result = list_entities()
        assert result["success"] is True
        assert result["count"] == 3

    @patch("tools.ha_control.ws_send", return_value=MOCK_STATES)
    def test_filter_by_domain(self, mock_ws):
        result = list_entities(domain="light")
        assert result["success"] is True
        assert result["count"] == 2
        assert all(e["entity_id"].startswith("light.") for e in result["entities"])

    @patch("tools.ha_control.ws_send", return_value=MOCK_STATES)
    def test_filter_by_domain_sensor(self, mock_ws):
        result = list_entities(domain="sensor")
        assert result["count"] == 1
        assert result["entities"][0]["entity_id"] == "sensor.temperature"

    @patch("tools.ha_control.ws_send", return_value={"success": False, "error": "fail"})
    def test_ws_failure(self, mock_ws):
        result = list_entities()
        assert result["success"] is False


class TestGetEntityState:
    @patch("tools.ha_control.rest_get")
    def test_found(self, mock_rest):
        mock_rest.return_value = {
            "success": True,
            "data": {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light", "brightness": 200},
                "last_changed": "2026-03-24T10:00:00Z",
                "last_updated": "2026-03-24T10:00:00Z",
            },
        }
        result = get_entity_state("light.living_room")
        assert result["success"] is True
        assert result["state"] == "on"
        assert result["attributes"]["brightness"] == 200
        mock_rest.assert_called_once_with("/api/states/light.living_room")

    @patch("tools.ha_control.rest_get")
    def test_not_found(self, mock_rest):
        mock_rest.return_value = {"success": False, "status_code": 404, "error": "Not found"}
        result = get_entity_state("light.nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]


class TestCallService:
    @patch("tools.ha_control.ws_send")
    def test_turn_on_light(self, mock_ws):
        mock_ws.return_value = {"success": True, "result": {}}
        result = call_service("light", "turn_on", entity_id="light.living_room")
        assert result["success"] is True
        assert result["service"] == "light.turn_on"
        cmd = mock_ws.call_args[0][0]
        assert cmd["domain"] == "light"
        assert cmd["service"] == "turn_on"
        assert cmd["target"]["entity_id"] == "light.living_room"

    @patch("tools.ha_control.ws_send")
    def test_with_data(self, mock_ws):
        mock_ws.return_value = {"success": True, "result": {}}
        result = call_service(
            "light", "turn_on",
            entity_id="light.living_room",
            data={"brightness": 128},
        )
        assert result["success"] is True
        cmd = mock_ws.call_args[0][0]
        assert cmd["service_data"]["brightness"] == 128

    @patch("tools.ha_control.ws_send")
    def test_failure(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": {"code": "not_found"}}
        result = call_service("light", "turn_on", entity_id="light.x")
        assert result["success"] is False
