"""End-to-end tests using mock HA server.

Tests the full tool chain against a simulated HA instance:
REST API, WebSocket API, onboarding flow, device management, and control.
"""

import os
import time

import pytest

from tests.mock_ha_server import MockHAServer


@pytest.fixture(scope="module")
def ha_server():
    """Start mock HA server for the test module."""
    server = MockHAServer(http_port=18123, ws_port=18124)
    server.start()
    time.sleep(0.2)  # let servers bind

    # Point tools at mock server
    os.environ["HA_URL"] = server.http_url
    os.environ["HA_TOKEN"] = "test-token"
    os.environ["HA_WS_URL"] = server.ws_url

    # ha_client reads HA_URL at import time, so patch module vars
    import tools.ha_client
    tools.ha_client.HA_URL = server.http_url
    tools.ha_client.HA_WS_URL = server.ws_url

    import tools.ha_setup
    tools.ha_setup.HA_URL = server.http_url

    import tools.ha_info
    tools.ha_info.HA_URL = server.http_url

    yield server
    server.stop()


class TestOnboardingFlow:
    """Test the full onboarding: create user -> exchange code -> get token."""

    def test_create_user(self, ha_server):
        from tools.ha_setup import create_ha_user
        result = create_ha_user(username="admin", password="test123")
        assert result["success"] is True
        assert "auth_code" in result

    def test_create_user_twice_fails(self, ha_server):
        from tools.ha_setup import create_ha_user
        result = create_ha_user(username="admin2", password="test")
        assert result["success"] is False
        assert result["status_code"] == 403

    def test_exchange_auth_code(self, ha_server):
        from tools.ha_setup import _exchange_auth_code
        result = _exchange_auth_code("test-auth-code-123")
        assert result["success"] is True
        assert "access_token" in result

    def test_exchange_bad_code(self, ha_server):
        from tools.ha_setup import _exchange_auth_code
        result = _exchange_auth_code("bad-code")
        assert result["success"] is False


class TestEntityControl:
    """Test entity listing, state queries, and service calls."""

    def test_list_all_entities(self, ha_server):
        from tools.ha_control import list_entities
        result = list_entities()
        assert result["success"] is True
        assert result["count"] == 2
        ids = [e["entity_id"] for e in result["entities"]]
        assert "light.living_room" in ids
        assert "sensor.temperature" in ids

    def test_list_entities_by_domain(self, ha_server):
        from tools.ha_control import list_entities
        result = list_entities(domain="light")
        assert result["success"] is True
        assert result["count"] == 1
        assert result["entities"][0]["entity_id"] == "light.living_room"

    def test_list_entities_by_area(self, ha_server):
        from tools.ha_control import list_entities
        result = list_entities(area="area-lr")
        assert result["success"] is True
        assert result["count"] == 2  # mock assigns all to area-lr

    def test_get_entity_state(self, ha_server):
        from tools.ha_control import get_entity_state
        result = get_entity_state("light.living_room")
        assert result["success"] is True
        assert result["state"] == "off"
        assert result["entity_id"] == "light.living_room"

    def test_get_entity_not_found(self, ha_server):
        from tools.ha_control import get_entity_state
        result = get_entity_state("light.nonexistent")
        assert result["success"] is False

    def test_call_service_turn_on(self, ha_server):
        from tools.ha_control import call_service, get_entity_state

        # Turn on the light
        result = call_service("light", "turn_on", entity_id="light.living_room")
        assert result["success"] is True

        # Verify state changed
        state = get_entity_state("light.living_room")
        assert state["success"] is True
        assert state["state"] == "on"


class TestDeviceManagement:
    """Test device discovery, areas, and assignment."""

    def test_discover_devices(self, ha_server):
        from tools.ha_devices import discover_devices
        result = discover_devices()
        assert result["success"] is True
        assert isinstance(result["discoveries"], list)

    def test_list_devices(self, ha_server):
        from tools.ha_devices import list_devices
        result = list_devices()
        assert result["success"] is True
        assert result["count"] == 1
        assert result["devices"][0]["name"] == "Test Light"

    def test_list_areas(self, ha_server):
        from tools.ha_devices import list_areas
        result = list_areas()
        assert result["success"] is True
        assert result["count"] >= 1

    def test_create_area(self, ha_server):
        from tools.ha_devices import create_area
        result = create_area("Kitchen")
        assert result["success"] is True
        assert result["name"] == "Kitchen"
        assert result["area_id"] is not None

    def test_assign_device_to_area(self, ha_server):
        from tools.ha_devices import assign_device_to_area
        result = assign_device_to_area("dev-001", "area-lr")
        assert result["success"] is True
        assert result["device_id"] == "dev-001"


class TestInfoTools:
    """Test history, config, and health check."""

    def test_get_history(self, ha_server):
        from tools.ha_info import get_history
        result = get_history("light.living_room", hours=24)
        assert result["success"] is True
        assert result["entity_id"] == "light.living_room"

    def test_get_config(self, ha_server):
        from tools.ha_info import get_config
        result = get_config()
        assert result["success"] is True
        assert result["version"] == "2026.3.3"
        assert result["location_name"] == "NanoHA Test"
        assert "light" in result["components"]

    def test_health_check_ha_reachable(self, ha_server):
        from tools.ha_info import health_check
        result = health_check()
        assert result["success"] is True
        assert result["services"]["homeassistant"] is True


class TestFullOnboardingScenario:
    """Simulate the complete agent-guided onboarding flow."""

    def test_full_scenario(self, ha_server):
        """
        Scenario: User sets up NanoHA from scratch.
        1. Create HA user
        2. Get access token
        3. List available areas
        4. Create a new area
        5. Discover devices
        6. List devices
        7. Assign device to area
        8. Turn on a light
        9. Check state
        10. Get config
        """
        from tests.mock_ha_server import state as mock_state
        mock_state.onboarded = False  # reset for this test

        from tools.ha_setup import create_ha_user, _exchange_auth_code
        from tools.ha_devices import list_areas, create_area, list_devices, assign_device_to_area
        from tools.ha_control import call_service, get_entity_state, list_entities
        from tools.ha_info import get_config

        # Reset light state
        for e in mock_state.entities:
            if e["entity_id"] == "light.living_room":
                e["state"] = "off"

        # 1. Create user
        user = create_ha_user()
        assert user["success"], f"Create user failed: {user}"

        # 2. Exchange code
        tokens = _exchange_auth_code(user["auth_code"])
        assert tokens["success"], f"Token exchange failed: {tokens}"

        # 3. List areas
        areas = list_areas()
        assert areas["success"]
        initial_count = areas["count"]

        # 4. Create bedroom
        bedroom = create_area("Bedroom")
        assert bedroom["success"]

        # 5. Verify area created
        areas2 = list_areas()
        assert areas2["count"] == initial_count + 1

        # 6. List devices
        devices = list_devices()
        assert devices["success"]
        assert devices["count"] >= 1

        # 7. Assign device to bedroom
        assign = assign_device_to_area(devices["devices"][0]["id"], bedroom["area_id"])
        assert assign["success"]

        # 8. Turn on light
        svc = call_service("light", "turn_on", entity_id="light.living_room")
        assert svc["success"]

        # 9. Verify state
        light_state = get_entity_state("light.living_room")
        assert light_state["success"]
        assert light_state["state"] == "on"

        # 10. Get config
        config = get_config()
        assert config["success"]
        assert config["version"] == "2026.3.3"
