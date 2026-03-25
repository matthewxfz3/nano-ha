"""Tests for ha_energy tools."""

from unittest.mock import patch

from tools.ha_energy import get_energy_sensors, get_energy_summary, suggest_savings

MOCK_STATES = {
    "success": True,
    "result": [
        {
            "entity_id": "sensor.grid_power",
            "state": "1500",
            "attributes": {"friendly_name": "Grid Power", "device_class": "power", "unit_of_measurement": "W"},
        },
        {
            "entity_id": "sensor.solar_power",
            "state": "0.8",
            "attributes": {"friendly_name": "Solar Power", "device_class": "power", "unit_of_measurement": "kW"},
        },
        {
            "entity_id": "sensor.daily_energy",
            "state": "12.5",
            "attributes": {"friendly_name": "Daily Energy", "device_class": "energy", "unit_of_measurement": "kWh"},
        },
        {
            "entity_id": "sensor.temperature",
            "state": "22",
            "attributes": {"friendly_name": "Temperature", "device_class": "temperature", "unit_of_measurement": "°C"},
        },
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room", "brightness": 255},
        },
        {
            "entity_id": "climate.thermostat",
            "state": "heating",
            "attributes": {"friendly_name": "Thermostat"},
        },
    ],
}


class TestGetEnergySensors:
    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_filters_energy_sensors(self, mock_ws):
        result = get_energy_sensors()
        assert result["success"] is True
        assert result["count"] == 3
        ids = [s["entity_id"] for s in result["sensors"]]
        assert "sensor.grid_power" in ids
        assert "sensor.solar_power" in ids
        assert "sensor.daily_energy" in ids
        assert "sensor.temperature" not in ids

    @patch("tools.ha_energy.ws_send", return_value={"success": False})
    def test_failure(self, mock_ws):
        result = get_energy_sensors()
        assert result["success"] is False


class TestGetEnergySummary:
    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_calculates_total(self, mock_ws):
        result = get_energy_summary()
        assert result["success"] is True
        # 1500W + 800W (0.8kW) = 2300W
        assert result["total_watts"] == 2300.0

    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_identifies_high_consumers(self, mock_ws):
        result = get_energy_summary()
        names = [c["name"] for c in result["high_consumers"]]
        assert "Grid Power" in names
        assert "Solar Power" in names


class TestSuggestSavings:
    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_suggests_brightness_reduction(self, mock_ws):
        result = suggest_savings()
        assert result["success"] is True
        types = [s["type"] for s in result["suggestions"]]
        assert "reduce_brightness" in types

    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_flags_active_climate(self, mock_ws):
        result = suggest_savings()
        types = [s["type"] for s in result["suggestions"]]
        assert "climate_active" in types

    @patch("tools.ha_energy.ws_send", return_value=MOCK_STATES)
    def test_flags_high_power(self, mock_ws):
        result = suggest_savings()
        types = [s["type"] for s in result["suggestions"]]
        assert "high_power" in types
