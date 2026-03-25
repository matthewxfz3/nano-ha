"""NanoHA Control Tools — entity states and service calls."""

from tools.ha_client import ws_send


def list_entities(domain: str = None, area: str = None) -> dict:
    """List entities, optionally filtered by domain or area."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": result}

    entities = result.get("result", [])

    if domain:
        entities = [e for e in entities if e["entity_id"].startswith(f"{domain}.")]

    if area:
        # Get area->entity mapping via entity registry
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
    """Get current state and attributes of an entity."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": result}

    for entity in result.get("result", []):
        if entity["entity_id"] == entity_id:
            return {
                "success": True,
                "entity_id": entity["entity_id"],
                "state": entity["state"],
                "attributes": entity.get("attributes", {}),
                "last_changed": entity.get("last_changed"),
                "last_updated": entity.get("last_updated"),
            }

    return {"success": False, "error": f"Entity {entity_id} not found"}


def call_service(
    domain: str,
    service: str,
    entity_id: str = None,
    data: dict = None,
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
    return {"success": False, "error": result}
