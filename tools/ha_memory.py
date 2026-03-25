"""NanoHA Memory — persistent preferences and learned context."""

import json
import logging
import os

log = logging.getLogger(__name__)

MEMORY_DIR = os.environ.get("NANOHA_MEMORY_DIR", os.path.expanduser("~/.nanoha/memory"))


def _ensure_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)


def _memory_path(key: str) -> str:
    safe_key = key.replace("/", "_").replace("..", "_")
    return os.path.join(MEMORY_DIR, f"{safe_key}.json")


def remember(key: str, value) -> dict:
    """Store a value in persistent memory.

    Examples:
        remember("user.preferred_temperature", 22)
        remember("device.nicknames", {"light.living_room": "the big lamp"})
        remember("routines.morning", {"lights": "on", "coffee": "start"})
    """
    _ensure_dir()
    path = _memory_path(key)
    try:
        with open(path, "w") as f:
            json.dump({"key": key, "value": value}, f, indent=2)
        return {"success": True, "key": key, "stored": True}
    except OSError as e:
        log.error("Cannot write memory %s: %s", key, e)
        return {"success": False, "error": f"Cannot save memory: {e}"}


def recall(key: str) -> dict:
    """Retrieve a value from persistent memory."""
    path = _memory_path(key)
    if not os.path.exists(path):
        return {"success": True, "key": key, "found": False, "value": None}
    try:
        with open(path) as f:
            data = json.load(f)
        return {"success": True, "key": key, "found": True, "value": data.get("value")}
    except (OSError, json.JSONDecodeError) as e:
        log.error("Cannot read memory %s: %s", key, e)
        return {"success": False, "error": f"Cannot read memory: {e}"}


def forget(key: str) -> dict:
    """Delete a value from persistent memory."""
    path = _memory_path(key)
    if not os.path.exists(path):
        return {"success": True, "key": key, "existed": False}
    try:
        os.remove(path)
        return {"success": True, "key": key, "existed": True}
    except OSError as e:
        log.error("Cannot delete memory %s: %s", key, e)
        return {"success": False, "error": f"Cannot delete memory: {e}"}


def list_memories() -> dict:
    """List all stored memory keys."""
    _ensure_dir()
    try:
        files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]
        keys = [f[:-5] for f in files]  # strip .json
        return {"success": True, "count": len(keys), "keys": sorted(keys)}
    except OSError as e:
        return {"success": False, "error": str(e)}
