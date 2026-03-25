#!/usr/bin/env python3
"""NanoHA setup — minimal bootstrap that starts the agent."""

import os
import shutil
import subprocess
import sys


def main():
    print("NanoHA — Nano Home Agent")
    print("=" * 40)
    print()

    # Check Docker
    if not shutil.which("docker"):
        print("Docker is required but not installed.")
        print("Install it from https://docs.docker.com/get-docker/")
        sys.exit(1)

    result = subprocess.run(
        ["docker", "info"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Docker is installed but not running. Please start Docker.")
        sys.exit(1)

    print("Docker is running.")
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
            user_id = input("Your Telegram user ID (from @userinfobot, or leave empty for all): ").strip()
            if user_id:
                telegram_allow = f"[{user_id}]"
        else:
            print("Skipping Telegram — no token provided.")

    # Google Cloud STT (optional)
    print()
    gcloud_stt_enabled = "false"
    gcloud_api_key = ""
    use_gcloud = input("Use Google Cloud STT instead of local Whisper? (y/N): ").strip().lower()
    if use_gcloud == "y":
        gcloud_api_key = input("Google Cloud API key: ").strip()
        if gcloud_api_key:
            gcloud_stt_enabled = "true"
        else:
            print("Skipping Google Cloud STT — no API key provided. Will use local Whisper.")

    # Write .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path, "w") as f:
            f.write(f"LLM_PROVIDER={provider}\n")
            f.write(f"LLM_API_KEY={api_key}\n")
            f.write("HA_URL=http://homeassistant:8123\n")
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
    print()
    print("Next steps:")
    print("  1. Start Home Assistant:  docker compose --profile ha up -d")
    print("  2. Install nanobot:       pip install nanobot-ai")
    print("  3. Chat with the agent:   nanobot chat")
    if telegram_enabled == "true":
        print(f"  4. Or message your bot on Telegram")
    print()


if __name__ == "__main__":
    main()
