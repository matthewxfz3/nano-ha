#!/usr/bin/env python3
"""NanoHA setup — bootstrap agent and Home Assistant."""

import os
import shutil
import subprocess
import sys

HA_DEPS = [
    "homeassistant",
    "home-assistant-frontend",
    "home-assistant-intents",
    "PyTurboJPEG",
    "httpx",
    "websockets",
    "setuptools",
    # Components required for mobile_app / default_config
    "hassil",
    "pymicro-vad",
    "go2rtc-client",
    "ha-ffmpeg",
    "av",
    "mutagen",
    "aiodiscover",
    "aiodhcpwatcher",
    "aiousbwatcher",
    "async-upnp-client",
    "pyserial",
]


def _pip_install(packages: list[str]):
    """Install packages via pip, handling --break-system-packages if needed."""
    cmd = [sys.executable, "-m", "pip", "install", "--user", "-q"] + packages
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "break-system-packages" in result.stderr:
        cmd.insert(5, "--break-system-packages")
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: pip install failed: {result.stderr[:200]}")
        return False
    return True


def main():
    print("NanoHA — Nano Home Agent")
    print("=" * 40)
    print()

    # Check Docker (optional — needed only for Docker-based deployment)
    has_docker = bool(shutil.which("docker"))
    if has_docker:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        has_docker = result.returncode == 0
    if has_docker:
        print("Docker: available")
    else:
        print("Docker: not available (will install HA via pip)")
    print()

    # LLM provider
    providers = {"1": "anthropic", "2": "openai", "3": "google", "4": "ollama"}
    print("Which LLM provider?")
    print("  1) Claude (Anthropic)")
    print("  2) GPT (OpenAI)")
    print("  3) Gemini (Google)")
    print("  4) Ollama (local)")
    choice = input("Choice [1]: ").strip() or "1"
    provider = providers.get(choice, "anthropic")

    api_key = ""
    if provider != "ollama":
        api_key = input(f"Enter your {provider} API key: ").strip()
        if not api_key:
            print("API key is required.")
            sys.exit(1)

    # Telegram (optional)
    print()
    telegram_enabled = "false"
    telegram_token = ""
    telegram_allow = "[]"
    use_telegram = input("Enable Telegram channel? (y/N): ").strip().lower()
    if use_telegram == "y":
        telegram_token = input("Telegram bot token (from @BotFather): ").strip()
        if telegram_token:
            telegram_enabled = "true"
            user_id = input("Your Telegram user ID (from @userinfobot, or empty for all): ").strip()
            if user_id:
                telegram_allow = f"[{user_id}]"

    # Google Cloud STT (optional)
    print()
    gcloud_stt_enabled = "false"
    gcloud_api_key = ""
    use_gcloud = input("Use Google Cloud STT instead of local Whisper? (y/N): ").strip().lower()
    if use_gcloud == "y":
        gcloud_api_key = input("Google Cloud API key: ").strip()
        if gcloud_api_key:
            gcloud_stt_enabled = "true"

    # Write .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path, "w") as f:
            f.write(f"LLM_PROVIDER={provider}\n")
            f.write(f"LLM_API_KEY={api_key}\n")
            f.write("HA_URL=http://localhost:8123\n")
            f.write("HA_TOKEN=\n")
            f.write(f"TELEGRAM_ENABLED={telegram_enabled}\n")
            f.write(f"TELEGRAM_BOT_TOKEN={telegram_token}\n")
            f.write(f"TELEGRAM_ALLOW_FROM={telegram_allow}\n")
            f.write(f"GOOGLE_CLOUD_STT_ENABLED={gcloud_stt_enabled}\n")
            f.write(f"GOOGLE_CLOUD_API_KEY={gcloud_api_key}\n")
    except OSError as e:
        print(f"Error writing .env: {e}")
        sys.exit(1)

    print()
    print("Configuration saved to .env")

    # Install HA dependencies
    if has_docker:
        print()
        print("Docker is available. You can run HA via Docker:")
        print("  docker compose --profile ha up -d")
        print()
        print("Or install HA locally:")
        install_local = input("Install HA Core locally via pip? (y/N): ").strip().lower()
        if install_local != "y":
            print()
            print("Next steps:")
            print("  1. docker compose --profile ha up -d")
            print("  2. pip install httpx websockets")
            print("  3. python3 agent.py")
            return
    else:
        print()
        install_local = "y"

    if install_local == "y":
        print()
        print("Installing Home Assistant Core + frontend...")
        print("(This may take a few minutes on first install)")
        if _pip_install(HA_DEPS):
            print("Home Assistant installed successfully.")
        else:
            print("Some packages failed. You may need to install manually:")
            print(f"  pip install {' '.join(HA_DEPS)}")

    # Start HA
    print()
    start_ha = input("Start Home Assistant now? (Y/n): ").strip().lower()
    if start_ha != "n":
        ha_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "ha")
        hass_bin = shutil.which("hass")
        if not hass_bin:
            # Check user bin
            user_bin = os.path.expanduser("~/Library/Python/3.14/bin/hass")
            if os.path.exists(user_bin):
                hass_bin = user_bin
            else:
                user_bin2 = os.path.expanduser("~/.local/bin/hass")
                if os.path.exists(user_bin2):
                    hass_bin = user_bin2

        if hass_bin:
            print(f"Starting HA: {hass_bin} --config {ha_config}")
            subprocess.Popen(
                [hass_bin, "--config", ha_config],
                stdout=open("/tmp/hass.log", "w"),
                stderr=subprocess.STDOUT,
            )
            print("Home Assistant starting in background (log: /tmp/hass.log)")
            print("It takes 30-60 seconds on first boot.")
        else:
            print("Cannot find 'hass' binary. Start manually:")
            print(f"  hass --config {ha_config}")

    print()
    print("Next steps:")
    print("  1. Wait for HA to be ready: curl http://localhost:8123/api/")
    print("  2. Run the agent: PYTHONPATH=. python3 agent.py")
    print("  3. Or send a message: PYTHONPATH=. python3 agent.py --message 'Hello'")
    if telegram_enabled == "true":
        print("  4. Or message your bot on Telegram")
    print()


if __name__ == "__main__":
    main()
