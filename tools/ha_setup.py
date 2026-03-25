"""NanoHA Setup Tools — deploy services, detect hardware, configure HA."""

import logging
import os
import subprocess

import httpx

from tools.ha_client import HA_URL, ws_send

log = logging.getLogger(__name__)

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
    if result.returncode != 0:
        log.error("Failed to deploy %s: %s", service_name, result.stderr.strip())
    return {
        "service": service_name,
        "success": result.returncode == 0,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def check_service_health(service_name: str | None = None) -> dict:
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
    try:
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
    except httpx.ConnectError as e:
        log.error("Cannot connect to HA: %s", e)
        return {"success": False, "error": f"Cannot connect to HA: {e}"}
    except httpx.TimeoutException:
        log.error("Timeout connecting to HA")
        return {"success": False, "error": "Timeout connecting to HA"}

    if resp.status_code == 200:
        return {"success": True, "auth_code": resp.json()["auth_code"]}
    return {
        "success": False,
        "status_code": resp.status_code,
        "error": resp.text,
    }


def _exchange_auth_code(auth_code: str) -> dict:
    """Exchange an onboarding auth_code for access + refresh tokens."""
    try:
        resp = httpx.post(
            f"{HA_URL}/auth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": auth_code,
            },
            timeout=30,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.error("Token exchange failed: %s", e)
        return {"success": False, "error": str(e)}

    if resp.status_code == 200:
        return {"success": True, **resp.json()}
    return {"success": False, "status_code": resp.status_code, "error": resp.text}


def generate_ha_token(
    username: str = "admin", password: str = "nanoha"
) -> dict:
    """Create a long-lived access token for the agent.

    Full flow: onboard user -> exchange auth code -> create long-lived token.
    If user already exists, returns an error (onboarding is one-time).
    """
    user_result = create_ha_user(username=username, password=password)
    if not user_result.get("success"):
        return user_result

    token_result = _exchange_auth_code(user_result["auth_code"])
    if not token_result.get("success"):
        return token_result

    # Create long-lived token via shared WebSocket client
    result = ws_send(
        {
            "type": "auth/long_lived_access_token",
            "client_name": "NanoHA Agent",
            "lifespan": 365,
        },
        access_token=token_result["access_token"],
    )
    if result.get("success"):
        return {"success": True, "token": result["result"]}
    return {"success": False, "error": result}


def configure_assist_pipeline(
    access_token: str,
    stt_engine: str = "wyoming",
    stt_language: str = "en",
    tts_engine: str = "wyoming",
    tts_language: str = "en",
    tts_voice: str | None = None,
    conversation_engine: str = "nanoha",
    conversation_language: str = "en",
    pipeline_name: str = "NanoHA Voice",
) -> dict:
    """Create and set as preferred an Assist voice pipeline via WebSocket."""
    result = ws_send(
        {
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
        },
        access_token=access_token,
    )
    if not result.get("success"):
        return {"success": False, "error": result}

    pipeline_id = result["result"]["id"]

    prefer_result = ws_send(
        {
            "type": "assist_pipeline/pipeline/set_preferred",
            "pipeline_id": pipeline_id,
        },
        access_token=access_token,
    )
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
