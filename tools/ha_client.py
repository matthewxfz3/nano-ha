"""Shared Home Assistant client for WebSocket and REST API calls."""

import asyncio
import json
import logging
import os

import httpx
import websockets

from tools.constants import DEFAULT_TIMEOUT, WS_COMMAND_START_ID

log = logging.getLogger(__name__)

HA_URL = os.environ.get("HA_URL", "http://homeassistant:8123")
HA_WS_URL = os.environ.get("HA_WS_URL", "")


def _get_token() -> str:
    """Read HA_TOKEN from env at call time (supports runtime injection)."""
    return os.environ.get("HA_TOKEN", "")


def _get_ws_url() -> str:
    """Get WebSocket URL, derived from HA_URL if not explicitly set."""
    ws_override = os.environ.get("HA_WS_URL", "") or HA_WS_URL
    if ws_override:
        return ws_override
    return HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"


async def ws_command(command: dict, access_token: str | None = None) -> dict:
    """Send an authenticated WebSocket command to HA and return the result."""
    token = access_token or _get_token()
    ws_url = _get_ws_url()

    async with websockets.connect(ws_url) as ws:
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            return {"success": False, "error": f"Unexpected: {msg}"}

        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            log.error("WebSocket auth failed: %s", msg)
            return {"success": False, "error": f"Auth failed: {msg}"}

        command.setdefault("id", WS_COMMAND_START_ID)
        await ws.send(json.dumps(command))
        msg = json.loads(await ws.recv())
        return msg


def ws_send(command: dict, access_token: str | None = None) -> dict:
    """Synchronous wrapper for ws_command."""
    return asyncio.run(ws_command(command, access_token))


def rest_get(path: str, access_token: str | None = None) -> dict:
    """Make an authenticated GET request to HA REST API."""
    token = access_token or _get_token()
    try:
        resp = httpx.get(
            f"{HA_URL}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=DEFAULT_TIMEOUT,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.error("REST GET %s failed: %s", path, e)
        return {"success": False, "error": str(e)}

    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}


def rest_post(path: str, data: dict | None = None, access_token: str | None = None) -> dict:
    """Make an authenticated POST request to HA REST API."""
    token = access_token or _get_token()
    try:
        resp = httpx.post(
            f"{HA_URL}{path}",
            headers={"Authorization": f"Bearer {token}"},
            json=data or {},
            timeout=DEFAULT_TIMEOUT,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.error("REST POST %s failed: %s", path, e)
        return {"success": False, "error": str(e)}

    if resp.status_code in (200, 201):
        return {"success": True, "data": resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}
