"""NanoHA Scene Learning — detect patterns and suggest automations."""

from collections import defaultdict

from tools.ha_client import rest_get, ws_send


def analyze_patterns(entity_id: str, days: int = 7) -> dict:
    """Analyze state change patterns for an entity over N days.

    Returns time-of-day distribution and most common state transitions.
    """
    from datetime import datetime, timedelta, timezone

    start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    result = rest_get(
        f"/api/history/period/{start}?filter_entity_id={entity_id}&minimal_response",
    )
    if not result.get("success"):
        return {"success": False, "error": f"Cannot get history for {entity_id}."}

    data = result.get("data", [])
    if not data or not data[0]:
        return {"success": True, "entity_id": entity_id, "patterns": [], "message": "No history found."}

    history = data[0]
    hour_counts = defaultdict(int)
    transitions = defaultdict(int)
    prev_state = None

    for entry in history:
        state = entry.get("state", "")
        changed = entry.get("last_changed", "")
        if changed:
            try:
                dt = datetime.fromisoformat(changed.replace("Z", "+00:00"))
                hour_counts[dt.hour] += 1
            except (ValueError, TypeError):
                pass
        if prev_state and prev_state != state:
            transitions[f"{prev_state} -> {state}"] += 1
        prev_state = state

    peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "success": True,
        "entity_id": entity_id,
        "days_analyzed": days,
        "total_changes": len(history),
        "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
        "top_transitions": [{"transition": t, "count": c} for t, c in top_transitions],
    }


def suggest_automations() -> dict:
    """Scan all entities and suggest automations based on current state patterns."""
    states = ws_send({"type": "get_states"})
    if not states.get("success"):
        return {"success": False, "error": "Cannot analyze patterns. HA may be unreachable."}

    suggestions = []
    lights_on = []
    presence_sensors = []
    climate_entities = []

    for e in states.get("result", []):
        eid = e["entity_id"]
        state = e["state"]
        attrs = e.get("attributes", {})
        name = attrs.get("friendly_name", eid)

        if eid.startswith("light.") and state == "on":
            lights_on.append(name)

        if eid.startswith("binary_sensor."):
            dc = attrs.get("device_class", "")
            if dc in ("presence", "occupancy", "motion"):
                presence_sensors.append({"entity_id": eid, "name": name, "state": state})

        if eid.startswith("climate."):
            climate_entities.append({"entity_id": eid, "name": name, "state": state})

    # Suggest presence-based light control
    if lights_on and presence_sensors:
        suggestions.append({
            "type": "presence_lights",
            "message": f"You have {len(lights_on)} lights on and {len(presence_sensors)} presence sensors. "
                       f"Consider: turn off lights when no presence detected for 10 minutes.",
            "trigger": "presence sensor off for 10 min",
            "action": "turn off lights in same area",
        })

    # Suggest climate scheduling
    if climate_entities:
        for c in climate_entities:
            if c["state"] in ("heating", "cooling"):
                suggestions.append({
                    "type": "climate_schedule",
                    "message": f"{c['name']} is actively {c['state']}. "
                               f"Consider: schedule to lower temperature at night and when away.",
                    "trigger": "time-based (e.g., 11 PM or when nobody home)",
                    "action": f"set {c['name']} to eco mode",
                })

    # Suggest goodnight routine
    if len(lights_on) >= 2:
        suggestions.append({
            "type": "goodnight_routine",
            "message": f"You have {len(lights_on)} lights on. "
                       f"Consider: a 'Goodnight' automation that turns off all lights and locks doors.",
            "trigger": "voice command or time-based (e.g., 11 PM)",
            "action": "turn off all lights, lock doors, set alarm",
        })

    return {"success": True, "count": len(suggestions), "suggestions": suggestions}
