"""NanoHA Automation Tools — list, create, trigger, enable/disable automations."""

from tools.ha_client import ws_send


def list_automations() -> dict:
    """List all automations with their current state."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": "Cannot list automations. HA may be unreachable."}

    automations = [
        {
            "entity_id": e["entity_id"],
            "name": e.get("attributes", {}).get("friendly_name", e["entity_id"]),
            "state": e["state"],
            "last_triggered": e.get("attributes", {}).get("last_triggered"),
        }
        for e in result.get("result", [])
        if e["entity_id"].startswith("automation.")
    ]
    return {"success": True, "count": len(automations), "automations": automations}


def trigger_automation(entity_id: str) -> dict:
    """Manually trigger an automation."""
    result = ws_send(
        {
            "type": "call_service",
            "domain": "automation",
            "service": "trigger",
            "target": {"entity_id": entity_id},
        }
    )
    if result.get("success"):
        return {"success": True, "triggered": entity_id}
    return {
        "success": False,
        "error": f"Cannot trigger '{entity_id}'. Check that the automation exists and is enabled.",
    }


def enable_automation(entity_id: str) -> dict:
    """Enable an automation."""
    result = ws_send(
        {
            "type": "call_service",
            "domain": "automation",
            "service": "turn_on",
            "target": {"entity_id": entity_id},
        }
    )
    if result.get("success"):
        return {"success": True, "enabled": entity_id}
    return {"success": False, "error": f"Cannot enable '{entity_id}'."}


def disable_automation(entity_id: str) -> dict:
    """Disable an automation."""
    result = ws_send(
        {
            "type": "call_service",
            "domain": "automation",
            "service": "turn_off",
            "target": {"entity_id": entity_id},
        }
    )
    if result.get("success"):
        return {"success": True, "disabled": entity_id}
    return {"success": False, "error": f"Cannot disable '{entity_id}'."}


def reload_automations() -> dict:
    """Reload all automations from configuration."""
    result = ws_send(
        {
            "type": "call_service",
            "domain": "automation",
            "service": "reload",
        }
    )
    if result.get("success"):
        return {"success": True, "message": "Automations reloaded."}
    return {"success": False, "error": "Failed to reload automations."}
