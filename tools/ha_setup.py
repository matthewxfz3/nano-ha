"""NanoHA Setup Tools — deploy services, detect hardware, configure HA."""

import os
import subprocess


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


def create_ha_user(username: str = "admin", password: str = "nanoha") -> dict:
    """Create HA admin user via onboarding API."""
    # TODO: Implement HA onboarding API call
    # POST http://homeassistant:8123/api/onboarding/users
    return {"status": "not_implemented"}


def generate_ha_token() -> dict:
    """Create a long-lived access token for the agent."""
    # TODO: Implement via HA auth API
    return {"status": "not_implemented"}


def configure_assist_pipeline(
    stt: str = "whisper", tts: str = "piper", agent: str = "nanoha"
) -> dict:
    """Set up HA voice pipeline via WebSocket."""
    # TODO: Implement via WebSocket API
    return {"status": "not_implemented"}


def get_setup_status() -> dict:
    """Return which services are running and what's configured."""
    health = check_service_health()
    hardware = detect_hardware()
    return {
        "services": health,
        "hardware": hardware,
    }
