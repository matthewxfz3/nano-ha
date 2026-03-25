"""NanoHA Control Tools — entity states and service calls."""

from tools.ha_client import rest_get, ws_send


def _ws_error_msg(result: dict, action: str) -> str:
    """Extract a human-readable error from a WS result."""
    err = result.get("error", {})
    if isinstance(err, dict):
        return err.get("message", f"Failed to {action}")
    return str(err) or f"Failed to {action}"


def list_entities(domain: str | None = None, area: str | None = None) -> dict:
    """List entities, optionally filtered by domain or area."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Cannot list entities. Home Assistant may be unreachable.",
        }

    entities = result.get("result", [])

    if domain:
        entities = [e for e in entities if e["entity_id"].startswith(f"{domain}.")]

    if area:
        reg = ws_send({"type": "config/entity_registry/list"})
        if reg.get("success"):
            area_entity_ids = {
                e["entity_id"]
                for e in reg.get("result", [])
                if e.get("area_id") == area
            }
            entities = [e for e in entities if e["entity_id"] in area_entity_ids]

    return {
        "success": True,
        "count": len(entities),
        "entities": [
            {
                "entity_id": e["entity_id"],
                "state": e["state"],
                "friendly_name": e.get("attributes", {}).get("friendly_name"),
            }
            for e in entities
        ],
    }


def get_entity_state(entity_id: str) -> dict:
    """Get current state and attributes of a single entity via REST."""
    result = rest_get(f"/api/states/{entity_id}")
    if not result.get("success"):
        return {
            "success": False,
            "error": f"Entity '{entity_id}' not found. Check the entity ID or run list_entities() to see available devices.",
        }

    entity = result["data"]
    return {
        "success": True,
        "entity_id": entity["entity_id"],
        "state": entity["state"],
        "attributes": entity.get("attributes", {}),
        "last_changed": entity.get("last_changed"),
        "last_updated": entity.get("last_updated"),
    }


def call_service(
    domain: str,
    service: str,
    entity_id: str | None = None,
    data: dict | None = None,
) -> dict:
    """Call a Home Assistant service (e.g., light.turn_on)."""
    service_data = dict(data) if data else {}
    target = {}
    if entity_id:
        target["entity_id"] = entity_id

    result = ws_send(
        {
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": service_data,
            "target": target,
        }
    )

    if result.get("success"):
        return {"success": True, "service": f"{domain}.{service}"}
    return {
        "success": False,
        "error": f"Failed to call {domain}.{service}. {_ws_error_msg(result, 'call service')}",
    }
