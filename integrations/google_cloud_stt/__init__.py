"""Google Cloud STT configuration helper for NanoHA.

Configures HA to use Google Cloud Speech-to-Text API instead of local Whisper.
Requires the official Google Cloud integration in Home Assistant.
"""

import json
import logging
import os

from tools.ha_client import rest_post, ws_send

log = logging.getLogger(__name__)


def configure_google_cloud_stt(api_key: str | None = None) -> dict:
    """Configure Google Cloud STT in Home Assistant.

    Uses HA's built-in Google Cloud integration. The API key can be
    passed directly or read from GOOGLE_CLOUD_API_KEY env var.
    """
    key = api_key or os.environ.get("GOOGLE_CLOUD_API_KEY", "")
    if not key:
        return {
            "success": False,
            "error": "Google Cloud API key is required. Set GOOGLE_CLOUD_API_KEY or pass api_key.",
        }

    # Start the Google Cloud config flow
    result = ws_send(
        {
            "type": "config_entries/flow",
            "handler": "google_cloud",
            "show_advanced_options": False,
        }
    )
    if not result.get("success"):
        return {
            "success": False,
            "error": "Cannot start Google Cloud setup. The integration may not be available.",
        }

    flow = result.get("result", {})
    flow_id = flow.get("flow_id")
    if not flow_id:
        return {"success": False, "error": "No flow_id returned from Google Cloud setup."}

    # Submit the API key
    complete = ws_send(
        {
            "type": "config_entries/flow",
            "flow_id": flow_id,
            "api_key": key,
        }
    )
    if not complete.get("success"):
        return {
            "success": False,
            "error": "Google Cloud setup failed. Check your API key.",
        }

    return {
        "success": True,
        "message": "Google Cloud STT configured. You can now select it in the Assist pipeline.",
        "engine": "google_cloud",
    }


def get_stt_engine() -> str:
    """Return which STT engine to use based on config."""
    if os.environ.get("GOOGLE_CLOUD_STT_ENABLED", "").lower() == "true":
        return "google_cloud"
    return "wyoming"
