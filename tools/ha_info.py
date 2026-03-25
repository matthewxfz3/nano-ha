"""NanoHA Info Tools — history, health checks, diagnostics."""

import logging
import subprocess
from datetime import datetime, timedelta, timezone

import httpx

from tools.ha_client import HA_URL, rest_get, ws_send

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5


def get_history(entity_id: str, hours: int = 24) -> dict:
    """Get state history for an entity over the past N hours."""
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = rest_get(
        f"/api/history/period/{start}?filter_entity_id={entity_id}&minimal_response",
    )
    if not result.get("success"):
        return result

    data = result.get("data", [])
    # With filter_entity_id, result is [[state1, state2, ...]] for the single entity
    if data and data[0]:
        entity_history = data[0]
        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(entity_history),
            "history": [
                {
                    "state": h["state"],
                    "last_changed": h.get("last_changed"),
                }
                for h in entity_history
            ],
        }

    return {"success": True, "entity_id": entity_id, "count": 0, "history": []}


def health_check() -> dict:
    """Check health of all NanoHA services."""
    services = {}

    for name, url in [
        ("homeassistant", f"{HA_URL}/api/"),
        ("whisper", "http://whisper:10300/"),
        ("piper", "http://piper:10200/"),
    ]:
        try:
            resp = httpx.get(url, timeout=DEFAULT_TIMEOUT)
            services[name] = resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.warning("%s unreachable: %s", name, e)
            services[name] = False

    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    services["docker_output"] = result.stdout.strip() if result.returncode == 0 else None

    all_healthy = all(v for k, v in services.items() if k != "docker_output")
    return {"success": True, "all_healthy": all_healthy, "services": services}


def get_config() -> dict:
    """Get HA configuration summary."""
    result = ws_send({"type": "get_config"})
    if not result.get("success"):
        return {"success": False, "error": result}

    config = result.get("result", {})
    return {
        "success": True,
        "location_name": config.get("location_name"),
        "version": config.get("version"),
        "unit_system": config.get("unit_system"),
        "components": config.get("components", []),
    }
