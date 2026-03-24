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

    # Ask LLM provider
    providers = {"1": "anthropic", "2": "openai", "3": "google", "4": "ollama"}
    print("Which LLM provider?")
    print("  1) Claude (Anthropic)")
    print("  2) GPT (OpenAI)")
    print("  3) Gemini (Google)")
    print("  4) Ollama (local)")
    choice = input("Choice [1]: ").strip() or "1"
    provider = providers.get(choice, "anthropic")

    # Ask API key
    api_key = ""
    if provider != "ollama":
        api_key = input(f"Enter your {provider} API key: ").strip()
        if not api_key:
            print("API key is required.")
            sys.exit(1)

    # Write .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "w") as f:
        f.write(f"LLM_PROVIDER={provider}\n")
        f.write(f"LLM_API_KEY={api_key}\n")
        f.write("HA_URL=http://homeassistant:8123\n")
        f.write("HA_TOKEN=\n")

    print()
    print("Starting NanoHA agent...")
    print()

    # Start only the agent (other services deployed by agent on demand)
    subprocess.run(
        ["docker", "compose", "up", "-d", "nanobot"],
        cwd=os.path.dirname(__file__) or ".",
    )

    print()
    print("NanoHA agent is running.")
    print("Chat with your agent to set up your home.")
    print()
    print("  docker compose logs -f nanobot    # see agent logs")
    print("  docker compose exec nanobot nanobot chat  # chat with agent")
    print()


if __name__ == "__main__":
    main()
