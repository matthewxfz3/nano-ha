"""NanoHA User Tools — multi-user profile management and preferences."""

import json
import logging
import os

from tools.ha_client import ws_send
from tools.ha_memory import recall, remember

log = logging.getLogger(__name__)


def list_persons() -> dict:
    """List all person entities from HA (household members)."""
    result = ws_send({"type": "get_states"})
    if not result.get("success"):
        return {"success": False, "error": "Cannot list persons. HA may be unreachable."}

    persons = [
        {
            "entity_id": e["entity_id"],
            "name": e.get("attributes", {}).get("friendly_name", e["entity_id"]),
            "state": e["state"],  # home/not_home/zone
            "source": e.get("attributes", {}).get("source"),
        }
        for e in result.get("result", [])
        if e["entity_id"].startswith("person.")
    ]
    return {"success": True, "count": len(persons), "persons": persons}


def get_user_profile(user_name: str) -> dict:
    """Get a user's profile and preferences from memory."""
    result = recall(f"user.{user_name}")
    if result.get("found"):
        return {"success": True, "user": user_name, "profile": result["value"]}
    return {
        "success": True,
        "user": user_name,
        "profile": None,
        "message": f"No profile found for '{user_name}'. Use set_user_preference to create one.",
    }


def set_user_preference(user_name: str, key: str, value) -> dict:
    """Set a preference for a user.

    Examples:
        set_user_preference("matt", "preferred_temperature", 22)
        set_user_preference("matt", "wake_time", "07:00")
        set_user_preference("matt", "favorite_lights", ["living_room", "office"])
    """
    profile_result = recall(f"user.{user_name}")
    profile = profile_result.get("value") or {}
    profile[key] = value
    remember(f"user.{user_name}", profile)
    return {"success": True, "user": user_name, "key": key, "value": value}


def get_user_preference(user_name: str, key: str) -> dict:
    """Get a specific preference for a user."""
    profile_result = recall(f"user.{user_name}")
    profile = profile_result.get("value") or {}
    if key in profile:
        return {"success": True, "user": user_name, "key": key, "value": profile[key]}
    return {"success": True, "user": user_name, "key": key, "value": None, "found": False}


def who_is_home() -> dict:
    """Check which household members are currently home."""
    result = list_persons()
    if not result.get("success"):
        return result

    home = [p for p in result["persons"] if p["state"] == "home"]
    away = [p for p in result["persons"] if p["state"] != "home"]
    return {
        "success": True,
        "home": [p["name"] for p in home],
        "away": [p["name"] for p in away],
        "anyone_home": len(home) > 0,
    }


def get_context_for_user(user_name: str) -> dict:
    """Get full context for a user: profile + presence + preferences.

    Used by the agent to personalize responses.
    """
    profile = get_user_profile(user_name)
    persons = list_persons()

    presence = "unknown"
    if persons.get("success"):
        for p in persons.get("persons", []):
            if user_name.lower() in p["name"].lower():
                presence = p["state"]
                break

    return {
        "success": True,
        "user": user_name,
        "presence": presence,
        "profile": profile.get("profile"),
    }
