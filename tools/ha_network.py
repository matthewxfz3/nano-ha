"""NanoHA Network Tools — scan for devices on the local network."""

import logging
import subprocess

log = logging.getLogger(__name__)


def scan_esphome_devices() -> dict:
    """Scan for ESPHome devices via mDNS (includes Voice PE)."""
    try:
        proc = subprocess.run(
            ["dns-sd", "-B", "_esphomelib._tcp", "local."],
            capture_output=True, text=True, timeout=8,
        )
    except FileNotFoundError:
        # Linux: try avahi-browse
        try:
            proc = subprocess.run(
                ["avahi-browse", "-t", "-r", "_esphomelib._tcp"],
                capture_output=True, text=True, timeout=8,
            )
        except FileNotFoundError:
            return {"success": False, "error": "No mDNS tool found. Install avahi-utils (Linux) or use macOS."}
    except subprocess.TimeoutExpired:
        # dns-sd doesn't exit on its own, timeout is expected
        proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    # dns-sd runs indefinitely, so we use a different approach
    try:
        result = subprocess.run(
            ["bash", "-c", "dns-sd -B _esphomelib._tcp local. & PID=$!; sleep 5; kill $PID 2>/dev/null; wait $PID 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        output = ""

    devices = []
    for line in output.splitlines():
        if "Instance Name" in line or "STARTING" in line or "DATE" in line or "Browsing" in line:
            continue
        if line.strip() and "Add" in line:
            parts = line.split()
            # Instance name is everything after the last known column
            # Format: Timestamp A/R Flags if Domain ServiceType InstanceName...
            if len(parts) >= 7:
                instance = " ".join(parts[6:])
                devices.append({"name": instance, "raw": line.strip()})

    return {"success": True, "count": len(devices), "devices": devices}


def resolve_device_ip(hostname: str) -> dict:
    """Resolve a .local hostname to an IP address."""
    if not hostname.endswith(".local") and not hostname.endswith(".local."):
        hostname = hostname + ".local"

    try:
        result = subprocess.run(
            ["bash", "-c", f"dns-sd -G v4 {hostname} & PID=$!; sleep 3; kill $PID 2>/dev/null; wait $PID 2>/dev/null"],
            capture_output=True, text=True, timeout=8,
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"success": False, "error": f"Cannot resolve {hostname}"}

    for line in output.splitlines():
        if "Add" in line and "." in line:
            parts = line.split()
            for part in parts:
                if part.count(".") == 3 and all(p.isdigit() for p in part.split(".")):
                    return {"success": True, "hostname": hostname, "ip": part}

    return {"success": False, "error": f"Cannot resolve {hostname}"}


def scan_and_resolve() -> dict:
    """Scan for ESPHome devices and resolve their IPs."""
    scan = scan_esphome_devices()
    if not scan.get("success") or scan["count"] == 0:
        return scan

    resolved = []
    for dev in scan["devices"]:
        name = dev["name"]
        hostname = name.replace(" ", "-") + ".local"
        ip_result = resolve_device_ip(hostname)
        resolved.append({
            "name": name,
            "hostname": hostname,
            "ip": ip_result.get("ip", "unknown"),
        })

    return {"success": True, "count": len(resolved), "devices": resolved}


def test_esphome_connectivity(host: str, port: int = 6053) -> dict:
    """Test TCP connectivity to an ESPHome device using IPv4 explicitly."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.close()
        return {"success": True, "host": host, "port": port}
    except OSError as e:
        return {"success": False, "host": host, "port": port, "error": str(e)}


def setup_esphome_device(host: str, access_token: str = None) -> dict:
    """Add an ESPHome device to HA via REST config flow.

    Always pass an IPv4 address (not hostname) to avoid Errno 65 from asyncio
    trying IPv6 first on macOS when the device only accepts IPv4.
    """
    from tools.ha_client import rest_post

    # Start ESPHome config flow
    result = rest_post(
        "/api/config/config_entries/flow",
        {"handler": "esphome", "show_advanced_options": False},
        access_token=access_token,
    )
    if not result.get("success"):
        return {"success": False, "error": f"Cannot start ESPHome flow: {result}"}

    flow_id = result.get("data", {}).get("flow_id")
    if not flow_id:
        return {"success": False, "error": "No flow_id in response"}

    # Submit the host — use IPv4 address to bypass asyncio IPv6 preference
    complete = rest_post(
        f"/api/config/config_entries/flow/{flow_id}",
        {"host": host, "port": 6053},
        access_token=access_token,
    )
    if not complete.get("success"):
        return {"success": False, "error": f"ESPHome setup failed: {complete}"}

    data = complete.get("data", {})
    return {
        "success": True,
        "type": data.get("type"),
        "title": data.get("title"),
        "flow_id": data.get("flow_id"),
        "step_id": data.get("step_id"),
    }


def add_voice_pe_to_ha(access_token: str = None) -> dict:
    """Scan for Voice PE devices, verify connectivity, and add to HA.

    One-shot convenience function for automated setup: scan → resolve IP →
    test IPv4 TCP → REST config flow.
    """
    devices = scan_and_resolve()
    if not devices.get("success") or devices.get("count", 0) == 0:
        return {"success": False, "error": "No ESPHome devices found on network"}

    results = []
    for dev in devices["devices"]:
        ip = dev.get("ip")
        if not ip or ip == "unknown":
            results.append({"name": dev["name"], "success": False, "error": "IP not resolved"})
            continue

        conn = test_esphome_connectivity(ip)
        if not conn["success"]:
            results.append({
                "name": dev["name"],
                "success": False,
                "error": f"TCP connect failed: {conn['error']}",
            })
            continue

        setup = setup_esphome_device(ip, access_token=access_token)
        results.append({"name": dev["name"], "ip": ip, **setup})

    return {"success": any(r.get("success") for r in results), "devices": results}
