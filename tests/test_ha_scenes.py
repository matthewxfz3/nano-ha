"""Tests for ha_scenes tools."""

from unittest.mock import patch

from tools.ha_scenes import analyze_patterns, suggest_automations

MOCK_HISTORY = {
    "success": True,
    "data": [
        [
            {"state": "off", "last_changed": "2026-03-20T07:00:00Z"},
            {"state": "on", "last_changed": "2026-03-20T07:30:00Z"},
            {"state": "off", "last_changed": "2026-03-20T22:00:00Z"},
            {"state": "on", "last_changed": "2026-03-21T07:15:00Z"},
            {"state": "off", "last_changed": "2026-03-21T22:30:00Z"},
        ]
    ],
}

MOCK_STATES = {
    "success": True,
    "result": [
        {"entity_id": "light.living_room", "state": "on", "attributes": {"friendly_name": "Living Room"}},
        {"entity_id": "light.bedroom", "state": "on", "attributes": {"friendly_name": "Bedroom"}},
        {"entity_id": "binary_sensor.presence", "state": "on", "attributes": {"friendly_name": "Presence", "device_class": "presence"}},
        {"entity_id": "climate.thermostat", "state": "heating", "attributes": {"friendly_name": "Thermostat"}},
    ],
}


class TestAnalyzePatterns:
    @patch("tools.ha_scenes.rest_get", return_value=MOCK_HISTORY)
    def test_detects_peak_hours(self, mock_rest):
        result = analyze_patterns("light.living_room", days=7)
        assert result["success"] is True
        assert result["total_changes"] == 5
        hours = [p["hour"] for p in result["peak_hours"]]
        assert 7 in hours  # morning pattern
        assert 22 in hours  # evening pattern

    @patch("tools.ha_scenes.rest_get", return_value=MOCK_HISTORY)
    def test_detects_transitions(self, mock_rest):
        result = analyze_patterns("light.living_room")
        transitions = [t["transition"] for t in result["top_transitions"]]
        assert "off -> on" in transitions
        assert "on -> off" in transitions

    @patch("tools.ha_scenes.rest_get", return_value={"success": True, "data": []})
    def test_no_history(self, mock_rest):
        result = analyze_patterns("sensor.nonexistent")
        assert result["success"] is True
        assert "No history" in result["message"]

    @patch("tools.ha_scenes.rest_get", return_value={"success": False, "error": "timeout"})
    def test_failure(self, mock_rest):
        result = analyze_patterns("light.x")
        assert result["success"] is False


class TestSuggestAutomations:
    @patch("tools.ha_scenes.ws_send", return_value=MOCK_STATES)
    def test_suggests_presence_lights(self, mock_ws):
        result = suggest_automations()
        assert result["success"] is True
        types = [s["type"] for s in result["suggestions"]]
        assert "presence_lights" in types

    @patch("tools.ha_scenes.ws_send", return_value=MOCK_STATES)
    def test_suggests_climate_schedule(self, mock_ws):
        result = suggest_automations()
        types = [s["type"] for s in result["suggestions"]]
        assert "climate_schedule" in types

    @patch("tools.ha_scenes.ws_send", return_value=MOCK_STATES)
    def test_suggests_goodnight_routine(self, mock_ws):
        result = suggest_automations()
        types = [s["type"] for s in result["suggestions"]]
        assert "goodnight_routine" in types

    @patch("tools.ha_scenes.ws_send", return_value={"success": False})
    def test_failure(self, mock_ws):
        result = suggest_automations()
        assert result["success"] is False
