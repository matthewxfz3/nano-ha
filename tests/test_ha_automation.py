"""Tests for ha_automation tools."""

from unittest.mock import patch

from tools.ha_automation import (
    disable_automation,
    enable_automation,
    list_automations,
    reload_automations,
    trigger_automation,
)

MOCK_STATES = {
    "success": True,
    "result": [
        {
            "entity_id": "automation.morning_lights",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Lights",
                "last_triggered": "2026-03-24T07:00:00Z",
            },
        },
        {
            "entity_id": "automation.night_lock",
            "state": "off",
            "attributes": {
                "friendly_name": "Night Lock",
                "last_triggered": None,
            },
        },
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room"},
        },
    ],
}


class TestListAutomations:
    @patch("tools.ha_automation.ws_send", return_value=MOCK_STATES)
    def test_filters_automations(self, mock_ws):
        result = list_automations()
        assert result["success"] is True
        assert result["count"] == 2
        ids = [a["entity_id"] for a in result["automations"]]
        assert "automation.morning_lights" in ids
        assert "light.living_room" not in ids

    @patch("tools.ha_automation.ws_send", return_value=MOCK_STATES)
    def test_includes_metadata(self, mock_ws):
        result = list_automations()
        morning = next(a for a in result["automations"] if "morning" in a["entity_id"])
        assert morning["name"] == "Morning Lights"
        assert morning["state"] == "on"
        assert morning["last_triggered"] == "2026-03-24T07:00:00Z"

    @patch("tools.ha_automation.ws_send", return_value={"success": False})
    def test_failure(self, mock_ws):
        result = list_automations()
        assert result["success"] is False


class TestTriggerAutomation:
    @patch("tools.ha_automation.ws_send", return_value={"success": True, "result": {}})
    def test_success(self, mock_ws):
        result = trigger_automation("automation.morning_lights")
        assert result["success"] is True
        assert result["triggered"] == "automation.morning_lights"
        cmd = mock_ws.call_args[0][0]
        assert cmd["service"] == "trigger"

    @patch("tools.ha_automation.ws_send", return_value={"success": False})
    def test_failure(self, mock_ws):
        result = trigger_automation("automation.bad")
        assert result["success"] is False


class TestEnableDisable:
    @patch("tools.ha_automation.ws_send", return_value={"success": True, "result": {}})
    def test_enable(self, mock_ws):
        result = enable_automation("automation.night_lock")
        assert result["success"] is True
        cmd = mock_ws.call_args[0][0]
        assert cmd["service"] == "turn_on"

    @patch("tools.ha_automation.ws_send", return_value={"success": True, "result": {}})
    def test_disable(self, mock_ws):
        result = disable_automation("automation.morning_lights")
        assert result["success"] is True
        cmd = mock_ws.call_args[0][0]
        assert cmd["service"] == "turn_off"


class TestReloadAutomations:
    @patch("tools.ha_automation.ws_send", return_value={"success": True, "result": {}})
    def test_success(self, mock_ws):
        result = reload_automations()
        assert result["success"] is True
        cmd = mock_ws.call_args[0][0]
        assert cmd["service"] == "reload"
