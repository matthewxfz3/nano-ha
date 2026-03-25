"""Shared Home Assistant client for WebSocket and REST API calls."""

import asyncio
import json
import os

import httpx
import websockets


HA_URL = os.environ.get("HA_URL", "http://homeassistant:8123")
HA_TOKEN = os.environ.get("HA_TOKEN", "")


def _get_token() -> str:
    return HA_TOKEN or os.environ.get("HA_TOKEN", "")


async def ws_command(command: dict, access_token: str = None) -> dict:
    """Send an authenticated WebSocket command to HA and return the result."""
    token = access_token or _get_token()
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url += "/api/websocket"

    async with websockets.connect(ws_url) as ws:
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            return {"success": False, "error": f"Unexpected: {msg}"}

        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            return {"success": False, "error": f"Auth failed: {msg}"}

        command.setdefault("id", 1)
        await ws.send(json.dumps(command))
        msg = json.loads(await ws.recv())
        return msg


def ws_send(command: dict, access_token: str = None) -> dict:
    """Synchronous wrapper for ws_command."""
    return asyncio.run(ws_command(command, access_token))


def rest_get(path: str, access_token: str = None) -> dict:
    """Make an authenticated GET request to HA REST API."""
    token = access_token or _get_token()
    resp = httpx.get(
        f"{HA_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}


def rest_post(path: str, data: dict = None, access_token: str = None) -> dict:
    """Make an authenticated POST request to HA REST API."""
    token = access_token or _get_token()
    resp = httpx.post(
        f"{HA_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=data or {},
        timeout=30,
    )
    if resp.status_code in (200, 201):
        return {"success": True, "data": resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}
