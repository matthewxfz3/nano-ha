"""NanoHA Info Tools — history, health checks, diagnostics."""

import subprocess

import httpx

from tools.ha_client import HA_URL, rest_get, ws_send


def get_history(entity_id: str, hours: int = 24) -> dict:
    """Get state history for an entity over the past N hours."""
    from datetime import datetime, timedelta, timezone

    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = rest_get(
        f"/api/history/period/{start}",
        # filter to single entity for efficiency
    )
    if not result.get("success"):
        return result

    # REST returns array of arrays; find matching entity
    data = result.get("data", [])
    for entity_history in data:
        if entity_history and entity_history[0].get("entity_id") == entity_id:
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

    # Check HA
    try:
        resp = httpx.get(f"{HA_URL}/api/", timeout=5)
        services["homeassistant"] = resp.status_code == 200
    except Exception:
        services["homeassistant"] = False

    # Check Whisper (Wyoming port 10300)
    try:
        resp = httpx.get("http://whisper:10300/", timeout=5)
        services["whisper"] = True
    except Exception:
        services["whisper"] = False

    # Check Piper (Wyoming port 10200)
    try:
        resp = httpx.get("http://piper:10200/", timeout=5)
        services["piper"] = True
    except Exception:
        services["piper"] = False

    # Check Docker containers
    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        capture_output=True,
        text=True,
    )
    services["docker_output"] = result.stdout.strip() if result.returncode == 0 else None

    all_healthy = all(
        v for k, v in services.items() if k != "docker_output"
    )
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
