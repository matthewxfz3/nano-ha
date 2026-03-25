"""Tests for ha_devices tools."""

from unittest.mock import patch

from tools.ha_devices import (
    assign_device_to_area,
    continue_config_flow,
    create_area,
    discover_devices,
    list_areas,
    list_devices,
    start_config_flow,
)


MOCK_DEVICES = {
    "success": True,
    "result": [
        {
            "id": "dev-001",
            "name": "Hue Bridge",
            "manufacturer": "Philips",
            "model": "BSB002",
            "area_id": "area-lr",
            "disabled_by": None,
            "name_by_user": None,
        },
        {
            "id": "dev-002",
            "name": "Aqara Sensor",
            "manufacturer": "Aqara",
            "model": "FP300",
            "area_id": "area-br",
            "disabled_by": None,
            "name_by_user": None,
        },
    ],
}


class TestDiscoverDevices:
    @patch("tools.ha_devices.ws_send")
    def test_found(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": [
                {"flow_id": "f1", "handler": "hue", "context": {"source": "zeroconf"}},
            ],
        }
        result = discover_devices()
        assert result["success"] is True
        assert result["count"] == 1
        assert result["discoveries"][0]["handler"] == "hue"

    @patch("tools.ha_devices.ws_send")
    def test_none_found(self, mock_ws):
        mock_ws.return_value = {"success": True, "result": []}
        result = discover_devices()
        assert result["count"] == 0

    @patch("tools.ha_devices.ws_send")
    def test_failure(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": "timeout"}
        result = discover_devices()
        assert result["success"] is False


class TestListDevices:
    @patch("tools.ha_devices.ws_send", return_value=MOCK_DEVICES)
    def test_all(self, mock_ws):
        result = list_devices()
        assert result["success"] is True
        assert result["count"] == 2

    @patch("tools.ha_devices.ws_send", return_value=MOCK_DEVICES)
    def test_filter_by_area(self, mock_ws):
        result = list_devices(area="area-lr")
        assert result["count"] == 1
        assert result["devices"][0]["name"] == "Hue Bridge"


class TestStartConfigFlow:
    @patch("tools.ha_devices.ws_send")
    def test_success(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": {
                "flow_id": "flow-123",
                "step_id": "user",
                "type": "form",
                "data_schema": [{"name": "host", "type": "string"}],
                "description_placeholders": None,
                "errors": {},
            },
        }
        result = start_config_flow("hue")
        assert result["success"] is True
        assert result["flow_id"] == "flow-123"
        assert result["step_id"] == "user"


class TestContinueConfigFlow:
    @patch("tools.ha_devices.ws_send")
    def test_complete(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": {
                "type": "create_entry",
                "flow_id": "flow-123",
                "title": "Philips Hue",
                "step_id": None,
                "data_schema": None,
                "description_placeholders": None,
                "errors": None,
            },
        }
        result = continue_config_flow("flow-123", user_input={"host": "192.168.1.42"})
        assert result["success"] is True
        assert result["type"] == "create_entry"
        assert result["title"] == "Philips Hue"


class TestAreas:
    @patch("tools.ha_devices.ws_send")
    def test_list_areas(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": [
                {"area_id": "area-lr", "name": "Living Room", "floor_id": None},
                {"area_id": "area-br", "name": "Bedroom", "floor_id": None},
            ],
        }
        result = list_areas()
        assert result["success"] is True
        assert result["count"] == 2

    @patch("tools.ha_devices.ws_send")
    def test_create_area(self, mock_ws):
        mock_ws.return_value = {
            "success": True,
            "result": {"area_id": "area-new", "name": "Kitchen"},
        }
        result = create_area("Kitchen")
        assert result["success"] is True
        assert result["area_id"] == "area-new"
        assert result["name"] == "Kitchen"


class TestAssignDevice:
    @patch("tools.ha_devices.ws_send")
    def test_assign(self, mock_ws):
        mock_ws.return_value = {"success": True, "result": {}}
        result = assign_device_to_area("dev-001", "area-lr")
        assert result["success"] is True
        assert result["device_id"] == "dev-001"
        assert result["area_id"] == "area-lr"
        cmd = mock_ws.call_args[0][0]
        assert cmd["type"] == "config/device_registry/update"

    @patch("tools.ha_devices.ws_send")
    def test_failure(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": "not_found"}
        result = assign_device_to_area("bad-id", "area-lr")
        assert result["success"] is False
