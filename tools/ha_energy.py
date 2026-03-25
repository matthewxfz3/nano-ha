"""NanoHA Energy Tools — monitor and optimize energy usage."""

from tools.ha_client import rest_get, ws_send


def get_energy_sensors() -> dict:
    """List all energy-related sensors (power, energy, voltage, current)."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": "Cannot query sensors. HA may be unreachable."}

    energy_classes = {"energy", "power", "voltage", "current", "gas", "water"}
    sensors = []

    for e in result.get("result", []):
        if not e["entity_id"].startswith("sensor."):
            continue
        attrs = e.get("attributes", {})
        device_class = attrs.get("device_class", "")
        unit = attrs.get("unit_of_measurement", "")

        if device_class in energy_classes or unit in ("W", "kW", "Wh", "kWh", "A", "V"):
            sensors.append({
                "entity_id": e["entity_id"],
                "state": e["state"],
                "unit": unit,
                "device_class": device_class,
                "friendly_name": attrs.get("friendly_name", e["entity_id"]),
            })

    return {"success": True, "count": len(sensors), "sensors": sensors}


def get_energy_summary() -> dict:
    """Get a summary of current energy consumption across all power sensors."""
    result = get_energy_sensors()
    if not result.get("success"):
        return result

    total_watts = 0.0
    high_consumers = []

    for s in result["sensors"]:
        if s["device_class"] == "power" or s["unit"] in ("W", "kW"):
            try:
                value = float(s["state"])
                if s["unit"] == "kW":
                    value *= 1000
                total_watts += value
                if value > 100:
                    high_consumers.append({
                        "name": s["friendly_name"],
                        "watts": round(value, 1),
                    })
            except (ValueError, TypeError):
                continue

    high_consumers.sort(key=lambda x: x["watts"], reverse=True)

    return {
        "success": True,
        "total_watts": round(total_watts, 1),
        "high_consumers": high_consumers[:5],
        "sensor_count": result["count"],
    }


def suggest_savings() -> dict:
    """Analyze current state and suggest energy-saving actions."""
    states = ws_send({"type": "get_states"})
    if not states.get("success"):
        return {"success": False, "error": "Cannot analyze energy. HA may be unreachable."}

    suggestions = []

    for e in states.get("result", []):
        eid = e["entity_id"]
        state = e["state"]
        attrs = e.get("attributes", {})

        # Lights left on
        if eid.startswith("light.") and state == "on":
            brightness = attrs.get("brightness", 255)
            if brightness > 200:
                suggestions.append({
                    "entity_id": eid,
                    "type": "reduce_brightness",
                    "message": f"{attrs.get('friendly_name', eid)} is at full brightness. Reducing to 70% saves ~30% energy.",
                })

        # Climate running when nobody home
        if eid.startswith("climate.") and state in ("heating", "cooling"):
            suggestions.append({
                "entity_id": eid,
                "type": "climate_active",
                "message": f"{attrs.get('friendly_name', eid)} is actively {state}. Consider scheduling or lowering the target.",
            })

        # Media players on
        if eid.startswith("media_player.") and state == "playing":
            pass  # normal usage, no suggestion

        # High power devices
        if eid.startswith("sensor.") and attrs.get("device_class") == "power":
            try:
                watts = float(state)
                if watts > 500:
                    suggestions.append({
                        "entity_id": eid,
                        "type": "high_power",
                        "message": f"{attrs.get('friendly_name', eid)} is using {watts}W. Check if this is expected.",
                    })
            except (ValueError, TypeError):
                continue

    return {"success": True, "count": len(suggestions), "suggestions": suggestions}
