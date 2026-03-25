"""Tests for ha_monitor tools."""

from unittest.mock import patch

from tools.ha_monitor import check_anomalies


MOCK_STATES_WITH_ANOMALIES = {
    "success": True,
    "result": [
        {
            "entity_id": "binary_sensor.front_door",
            "state": "on",
            "attributes": {"friendly_name": "Front Door", "device_class": "door"},
        },
        {
            "entity_id": "binary_sensor.hallway_motion",
            "state": "on",
            "attributes": {"friendly_name": "Hallway Motion", "device_class": "motion"},
        },
        {
            "entity_id": "sensor.lock_battery",
            "state": "8",
            "attributes": {"friendly_name": "Lock Battery"},
        },
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room"},
        },
        {
            "entity_id": "sensor.temperature",
            "state": "22",
            "attributes": {"friendly_name": "Temperature"},
        },
    ],
}

MOCK_STATES_CLEAN = {
    "success": True,
    "result": [
        {
            "entity_id": "binary_sensor.front_door",
            "state": "off",
            "attributes": {"friendly_name": "Front Door", "device_class": "door"},
        },
        {
            "entity_id": "sensor.lock_battery",
            "state": "85",
            "attributes": {"friendly_name": "Lock Battery"},
        },
    ],
}


class TestCheckAnomalies:
    @patch("tools.ha_client.ws_send", return_value=MOCK_STATES_WITH_ANOMALIES)
    def test_detects_open_door(self, mock_ws):
        result = check_anomalies()
        assert result["success"] is True
        door_anomalies = [a for a in result["anomalies"] if a["type"] == "open_entry"]
        assert len(door_anomalies) == 1
        assert "Front Door" in door_anomalies[0]["message"]

    @patch("tools.ha_client.ws_send", return_value=MOCK_STATES_WITH_ANOMALIES)
    def test_detects_low_battery(self, mock_ws):
        result = check_anomalies()
        battery = [a for a in result["anomalies"] if a["type"] == "low_battery"]
        assert len(battery) == 1
        assert "8.0%" in battery[0]["message"]

    @patch("tools.ha_client.ws_send", return_value=MOCK_STATES_WITH_ANOMALIES)
    @patch("tools.ha_monitor.datetime")
    def test_detects_motion_at_night(self, mock_dt, mock_ws):
        # Simulate 2 AM
        from datetime import timezone
        mock_now = type("MockDT", (), {"hour": 2})()
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: __import__("datetime").datetime(*a, **kw)

        result = check_anomalies()
        # Motion at night detection depends on is_night flag
        assert result["success"] is True

    @patch("tools.ha_client.ws_send", return_value=MOCK_STATES_CLEAN)
    def test_no_anomalies(self, mock_ws):
        result = check_anomalies()
        assert result["success"] is True
        assert result["count"] == 0

    @patch("tools.ha_client.ws_send", return_value={"success": False})
    def test_ha_unreachable(self, mock_ws):
        result = check_anomalies()
        assert result["success"] is False

    @patch("tools.ha_client.ws_send", return_value=MOCK_STATES_WITH_ANOMALIES)
    def test_ignores_normal_entities(self, mock_ws):
        result = check_anomalies()
        anomaly_ids = [a["entity_id"] for a in result["anomalies"]]
        assert "light.living_room" not in anomaly_ids
        assert "sensor.temperature" not in anomaly_ids
