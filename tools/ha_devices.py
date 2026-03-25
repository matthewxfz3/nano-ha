"""NanoHA Device Tools — discover, onboard, and manage devices."""

from tools.ha_client import ws_send


def discover_devices() -> dict:
    """Trigger HA discovery and return found config flow entries."""
    result = ws_send({"type": "config_entries/flow/progress"})
    if not result.get("success"):
        return {
            "success": False,
            "error": "Cannot scan for devices. Home Assistant may be unreachable.",
        }

    flows = result.get("result", [])
    return {
        "success": True,
        "count": len(flows),
        "discoveries": [
            {
                "flow_id": f["flow_id"],
                "handler": f["handler"],
                "context": f.get("context", {}),
            }
            for f in flows
        ],
    }


def list_devices(area: str | None = None) -> dict:
    """List all registered devices, optionally filtered by area."""
    result = ws_send({"type": "config/device_registry/list"})
    if not result.get("success"):
        return {
            "success": False,
            "error": "Cannot list devices. Home Assistant may be unreachable.",
        }

    devices = result.get("result", [])
    if area:
        devices = [d for d in devices if d.get("area_id") == area]

    return {
        "success": True,
        "count": len(devices),
        "devices": [
            {
                "id": d["id"],
                "name": d.get("name") or d.get("name_by_user"),
                "manufacturer": d.get("manufacturer"),
                "model": d.get("model"),
                "area_id": d.get("area_id"),
                "disabled_by": d.get("disabled_by"),
            }
            for d in devices
        ],
    }


def start_config_flow(handler: str) -> dict:
    """Start an integration config flow (e.g., handler='hue')."""
    result = ws_send(
        {
            "type": "config_entries/flow",
            "handler": handler,
            "show_advanced_options": False,
        }
    )
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Cannot start setup for '{handler}'. Check that the integration name is correct.",
        }

    flow = result.get("result", {})
    return {
        "success": True,
        "flow_id": flow.get("flow_id"),
        "step_id": flow.get("step_id"),
        "type": flow.get("type"),
        "description": flow.get("description_placeholders"),
        "data_schema": flow.get("data_schema"),
        "errors": flow.get("errors"),
    }


def continue_config_flow(flow_id: str, user_input: dict | None = None) -> dict:
    """Continue or complete a config flow step."""
    result = ws_send(
        {
            "type": "config_entries/flow",
            "flow_id": flow_id,
            **(user_input or {}),
        }
    )
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Setup step failed for flow '{flow_id}'. The flow may have expired — try starting over.",
        }

    flow = result.get("result", {})
    return {
        "success": True,
        "type": flow.get("type"),
        "flow_id": flow.get("flow_id"),
        "step_id": flow.get("step_id"),
        "title": flow.get("title"),
        "description": flow.get("description_placeholders"),
        "data_schema": flow.get("data_schema"),
        "errors": flow.get("errors"),
    }


def list_areas() -> dict:
    """List all areas/rooms."""
    result = ws_send({"type": "config/area_registry/list"})
    if not result.get("success"):
        return {
            "success": False,
            "error": "Cannot list areas. Home Assistant may be unreachable.",
        }

    areas = result.get("result", [])
    return {
        "success": True,
        "count": len(areas),
        "areas": [
            {"id": a["area_id"], "name": a["name"], "floor_id": a.get("floor_id")}
            for a in areas
        ],
    }


def create_area(name: str) -> dict:
    """Create a new area/room."""
    result = ws_send({"type": "config/area_registry/create", "name": name})
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Cannot create area '{name}'. It may already exist.",
        }

    area = result.get("result", {})
    return {
        "success": True,
        "area_id": area.get("area_id"),
        "name": area.get("name"),
    }


def assign_device_to_area(device_id: str, area_id: str) -> dict:
    """Assign a device to a room/area."""
    result = ws_send(
        {
            "type": "config/device_registry/update",
            "device_id": device_id,
            "area_id": area_id,
        }
    )
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Cannot assign device '{device_id}' to area '{area_id}'. Check that both IDs are valid.",
        }

    return {
        "success": True,
        "device_id": device_id,
        "area_id": area_id,
    }
