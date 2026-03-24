"""NanoHA Device Tools — discover, onboard, and manage devices."""


def discover_devices() -> dict:
    """Trigger HA discovery and return found devices/integrations."""
    # TODO: Implement via WebSocket config_entries/flow + discovery
    return {"status": "not_implemented", "devices": []}


def list_devices(area: str = None) -> dict:
    """List all registered devices, optionally filtered by area."""
    # TODO: Implement via WebSocket config/device_registry/list
    return {"status": "not_implemented", "devices": []}


def start_config_flow(handler: str) -> dict:
    """Start an integration config flow (e.g., handler='hue')."""
    # TODO: Implement via WebSocket config_entries/flow
    # Returns flow_id + what user input is needed
    return {"status": "not_implemented", "flow_id": None}


def continue_config_flow(flow_id: str, user_input: dict = None) -> dict:
    """Continue or complete a config flow step."""
    # TODO: Implement via WebSocket config_entries/flow/{flow_id}
    return {"status": "not_implemented"}


def list_areas() -> dict:
    """List all areas/rooms."""
    # TODO: Implement via WebSocket config/area_registry/list
    return {"status": "not_implemented", "areas": []}


def create_area(name: str) -> dict:
    """Create a new area/room."""
    # TODO: Implement via WebSocket config/area_registry/create
    return {"status": "not_implemented", "area_id": None}


def assign_device_to_area(device_id: str, area_id: str) -> dict:
    """Assign a device to a room/area."""
    # TODO: Implement via WebSocket config/device_registry/update
    return {"status": "not_implemented"}
