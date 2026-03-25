"""NanoHA Setup Tools — deploy services, detect hardware, configure HA."""

import asyncio
import json
import os
import subprocess

import httpx
import websockets


HA_URL = os.environ.get("HA_URL", "http://homeassistant:8123")
CLIENT_ID = "https://nanoha.local/"


def check_docker() -> dict:
    """Check if Docker is installed and running."""
    result = subprocess.run(
        ["docker", "info"], capture_output=True, text=True
    )
    return {
        "installed": True,
        "running": result.returncode == 0,
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def detect_hardware() -> dict:
    """Scan for USB Zigbee coordinators and network interfaces."""
    zigbee_dongle = None
    for path in ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1"]:
        if os.path.exists(path):
            zigbee_dongle = path
            break

    return {
        "zigbee_dongle": zigbee_dongle,
    }


def deploy_service(service_name: str) -> dict:
    """Start a Docker Compose service (ha, voice, etc.)."""
    profile_map = {
        "homeassistant": "ha",
        "whisper": "voice",
        "piper": "voice",
    }
    profile = profile_map.get(service_name)

    cmd = ["docker", "compose"]
    if profile:
        cmd += ["--profile", profile]
    cmd += ["up", "-d", service_name]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "service": service_name,
        "success": result.returncode == 0,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def check_service_health(service_name: str = None) -> dict:
    """Check health of one or all services."""
    cmd = ["docker", "compose", "ps", "--format", "json"]
    if service_name:
        cmd.append(service_name)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "output": result.stdout.strip(),
    }


def create_ha_user(
    username: str = "admin",
    password: str = "nanoha",
    name: str = "NanoHA Admin",
    language: str = "en",
) -> dict:
    """Create HA admin user via onboarding API.

    This only works once — on a fresh HA instance before any user exists.
    Returns an auth_code that must be exchanged for tokens.
    """
    resp = httpx.post(
        f"{HA_URL}/api/onboarding/users",
        json={
            "name": name,
            "username": username,
            "password": password,
            "client_id": CLIENT_ID,
            "language": language,
        },
        timeout=30,
    )
    if resp.status_code == 200:
        return {"success": True, "auth_code": resp.json()["auth_code"]}
    return {
        "success": False,
        "status_code": resp.status_code,
        "error": resp.text,
    }


def _exchange_auth_code(auth_code: str) -> dict:
    """Exchange an onboarding auth_code for access + refresh tokens."""
    resp = httpx.post(
        f"{HA_URL}/auth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": auth_code,
        },
        timeout=30,
    )
    if resp.status_code == 200:
        return {"success": True, **resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}


async def _ws_create_long_lived_token(
    access_token: str, client_name: str = "NanoHA Agent", lifespan_days: int = 365
) -> dict:
    """Create a long-lived access token via authenticated WebSocket."""
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url += "/api/websocket"

    async with websockets.connect(ws_url) as ws:
        # HA sends auth_required
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            return {"success": False, "error": f"Unexpected message: {msg}"}

        # Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": access_token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            return {"success": False, "error": f"Auth failed: {msg}"}

        # Request long-lived token
        await ws.send(
            json.dumps(
                {
                    "id": 1,
                    "type": "auth/long_lived_access_token",
                    "client_name": client_name,
                    "lifespan": lifespan_days,
                }
            )
        )
        msg = json.loads(await ws.recv())
        if msg.get("success"):
            return {"success": True, "token": msg["result"]}
        return {"success": False, "error": msg}


def generate_ha_token(
    username: str = "admin", password: str = "nanoha"
) -> dict:
    """Create a long-lived access token for the agent.

    Full flow: onboard user -> exchange auth code -> create long-lived token.
    If user already exists, returns an error (onboarding is one-time).
    """
    # Step 1: Create user (gets auth_code)
    user_result = create_ha_user(username=username, password=password)
    if not user_result.get("success"):
        return user_result

    # Step 2: Exchange auth_code for short-lived access_token
    token_result = _exchange_auth_code(user_result["auth_code"])
    if not token_result.get("success"):
        return token_result

    # Step 3: Use access_token to create long-lived token via WebSocket
    ll_token = asyncio.run(
        _ws_create_long_lived_token(token_result["access_token"])
    )
    return ll_token


async def _ws_command(access_token: str, command: dict) -> dict:
    """Send a single WebSocket command to HA and return the result."""
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url += "/api/websocket"

    async with websockets.connect(ws_url) as ws:
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            return {"success": False, "error": f"Unexpected: {msg}"}

        await ws.send(json.dumps({"type": "auth", "access_token": access_token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            return {"success": False, "error": f"Auth failed: {msg}"}

        command.setdefault("id", 1)
        await ws.send(json.dumps(command))
        msg = json.loads(await ws.recv())
        return msg


def configure_assist_pipeline(
    access_token: str,
    stt_engine: str = "wyoming",
    stt_language: str = "en",
    tts_engine: str = "wyoming",
    tts_language: str = "en",
    tts_voice: str = None,
    conversation_engine: str = "nanoha",
    conversation_language: str = "en",
    pipeline_name: str = "NanoHA Voice",
) -> dict:
    """Create and set as preferred an Assist voice pipeline via WebSocket."""
    # Create the pipeline
    create_cmd = {
        "type": "assist_pipeline/pipeline/create",
        "name": pipeline_name,
        "language": stt_language,
        "conversation_engine": conversation_engine,
        "conversation_language": conversation_language,
        "stt_engine": stt_engine,
        "stt_language": stt_language,
        "tts_engine": tts_engine,
        "tts_language": tts_language,
        "tts_voice": tts_voice,
        "wake_word_entity": None,
        "wake_word_id": None,
    }
    result = asyncio.run(_ws_command(access_token, create_cmd))
    if not result.get("success"):
        return {"success": False, "error": result}

    pipeline_id = result["result"]["id"]

    # Set as preferred
    prefer_cmd = {
        "type": "assist_pipeline/pipeline/set_preferred",
        "pipeline_id": pipeline_id,
    }
    prefer_result = asyncio.run(_ws_command(access_token, prefer_cmd))
    return {
        "success": prefer_result.get("success", False),
        "pipeline_id": pipeline_id,
        "pipeline": result.get("result"),
    }


def get_setup_status() -> dict:
    """Return which services are running and what's configured."""
    health = check_service_health()
    hardware = detect_hardware()
    return {
        "services": health,
        "hardware": hardware,
    }
