"""NanoHA Monitor Tools — event subscription and anomaly detection."""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import websockets

from tools.ha_client import HA_URL, _get_token, _get_ws_url

log = logging.getLogger(__name__)


async def subscribe_events(
    event_type: str | None = None,
    duration_seconds: int = 60,
    max_events: int = 50,
    access_token: str | None = None,
) -> dict:
    """Subscribe to HA events and collect them for a duration.

    Args:
        event_type: Filter to specific event type (e.g., "state_changed"). None = all.
        duration_seconds: How long to listen.
        max_events: Stop after collecting this many events.
    """
    token = access_token or _get_token()
    ws_url = _get_ws_url()
    events = []

    try:
        async with websockets.connect(ws_url) as ws:
            # Auth handshake
            msg = json.loads(await ws.recv())
            if msg.get("type") != "auth_required":
                return {"success": False, "error": "Unexpected HA response."}

            await ws.send(json.dumps({"type": "auth", "access_token": token}))
            msg = json.loads(await ws.recv())
            if msg.get("type") != "auth_ok":
                return {"success": False, "error": "Authentication failed."}

            # Subscribe
            sub_cmd = {"id": 1, "type": "subscribe_events"}
            if event_type:
                sub_cmd["event_type"] = event_type
            await ws.send(json.dumps(sub_cmd))

            # Consume subscription confirmation
            msg = json.loads(await ws.recv())
            if not msg.get("success"):
                return {"success": False, "error": "Failed to subscribe to events."}

            # Collect events
            try:
                end_time = asyncio.get_event_loop().time() + duration_seconds
                while len(events) < max_events:
                    remaining = end_time - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        break
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 5))
                        msg = json.loads(raw)
                        if msg.get("type") == "event":
                            event_data = msg.get("event", {})
                            events.append({
                                "event_type": event_data.get("event_type"),
                                "entity_id": event_data.get("data", {}).get("entity_id"),
                                "new_state": event_data.get("data", {}).get("new_state", {}).get("state"),
                                "old_state": event_data.get("data", {}).get("old_state", {}).get("state"),
                                "time": event_data.get("time_fired"),
                            })
                    except asyncio.TimeoutError:
                        continue
            except asyncio.CancelledError:
                pass

    except (OSError, websockets.exceptions.WebSocketException) as e:
        log.error("Event subscription failed: %s", e)
        return {"success": False, "error": f"Cannot connect to HA: {e}"}

    return {"success": True, "count": len(events), "events": events}


def watch_events(
    event_type: str | None = None,
    duration_seconds: int = 60,
    max_events: int = 50,
) -> dict:
    """Synchronous wrapper for subscribe_events."""
    return asyncio.run(
        subscribe_events(event_type, duration_seconds, max_events)
    )


def check_anomalies(hours: int = 1) -> dict:
    """Check for recent anomalous events (motion at night, doors opened, etc.).

    Scans recent state changes and flags potentially concerning ones.
    """
    from tools.ha_client import ws_send

    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": "Cannot check for anomalies. HA may be unreachable."}

    now = datetime.now(timezone.utc)
    is_night = now.hour < 6 or now.hour >= 23
    anomalies = []

    for entity in result.get("result", []):
        eid = entity["entity_id"]
        state = entity["state"]
        attrs = entity.get("attributes", {})

        # Motion detected at night
        if is_night and eid.startswith("binary_sensor.") and state == "on":
            device_class = attrs.get("device_class", "")
            if device_class in ("motion", "occupancy", "presence"):
                anomalies.append({
                    "entity_id": eid,
                    "type": "motion_at_night",
                    "message": f"Motion detected at {attrs.get('friendly_name', eid)} during night hours.",
                })

        # Door/window open
        if eid.startswith("binary_sensor.") and state == "on":
            device_class = attrs.get("device_class", "")
            if device_class in ("door", "window", "garage_door"):
                anomalies.append({
                    "entity_id": eid,
                    "type": "open_entry",
                    "message": f"{attrs.get('friendly_name', eid)} is currently open.",
                })

        # Low battery
        if eid.startswith("sensor.") and "battery" in eid:
            try:
                level = float(state)
                if level < 15:
                    anomalies.append({
                        "entity_id": eid,
                        "type": "low_battery",
                        "message": f"{attrs.get('friendly_name', eid)} battery is at {level}%.",
                    })
            except (ValueError, TypeError):
                pass

    return {
        "success": True,
        "count": len(anomalies),
        "is_night": is_night,
        "anomalies": anomalies,
    }
