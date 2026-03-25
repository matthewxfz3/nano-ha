#!/usr/bin/env bash
set -euo pipefail

# NanoHA One-Click Deployment
# Supports: x86_64, ARM64 (Raspberry Pi 4/5, Apple Silicon)
# Usage: curl -sSL https://raw.githubusercontent.com/matthewxfz3/nano-ha/main/deploy.sh | bash

REPO="https://github.com/matthewxfz3/nano-ha.git"
INSTALL_DIR="${NANOHA_DIR:-$HOME/nano-ha}"
ARCH=$(uname -m)

echo "NanoHA — One-Click Deployment"
echo "=============================="
echo "Architecture: $ARCH"
echo "Install to:   $INSTALL_DIR"
echo ""

# Check requirements
check_requirements() {
    local missing=()

    if ! command -v docker &>/dev/null; then
        missing+=("docker")
    fi

    if ! command -v git &>/dev/null; then
        missing+=("git")
    fi

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing requirements: ${missing[*]}"
        echo ""
        echo "Install them first:"
        case "$(uname -s)" in
            Linux)
                echo "  sudo apt update && sudo apt install -y docker.io git python3 python3-pip"
                echo "  sudo usermod -aG docker \$USER && newgrp docker"
                ;;
            Darwin)
                echo "  brew install --cask docker"
                echo "  brew install git python3"
                ;;
        esac
        exit 1
    fi

    # Check Docker is running
    if ! docker info &>/dev/null; then
        echo "Docker is installed but not running. Start Docker first."
        exit 1
    fi

    echo "All requirements met."
}

# Configure for architecture
configure_arch() {
    case "$ARCH" in
        aarch64|arm64)
            echo "Detected ARM64 (Raspberry Pi / Apple Silicon)"
            # Whisper: use tiny model for low-memory devices
            export WHISPER_MODEL="tiny"
            export PIPER_VOICE="en_US-lessac-low"
            ;;
        x86_64|amd64)
            echo "Detected x86_64"
            export WHISPER_MODEL="small"
            export PIPER_VOICE="en_US-lessac-medium"
            ;;
        *)
            echo "Warning: Unknown architecture $ARCH. Using default config."
            export WHISPER_MODEL="tiny"
            export PIPER_VOICE="en_US-lessac-low"
            ;;
    esac
}

# Clone or update repo
install_repo() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing installation..."
        cd "$INSTALL_DIR"
        git pull --rebase origin main
    else
        echo "Cloning NanoHA..."
        git clone "$REPO" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
}

# Generate docker-compose override for arch-specific settings
generate_override() {
    cat > "$INSTALL_DIR/docker-compose.override.yml" <<YAML
services:
  whisper:
    command: --model ${WHISPER_MODEL} --language en
  piper:
    command: --voice ${PIPER_VOICE}
YAML
    echo "Generated docker-compose.override.yml for $ARCH"
}

# Install Python dependencies
install_deps() {
    echo "Installing Python dependencies..."
    if command -v pip3 &>/dev/null; then
        pip3 install --user -q httpx websockets homeassistant home-assistant-frontend PyTurboJPEG 2>/dev/null || \
        pip3 install --user -q --break-system-packages httpx websockets homeassistant home-assistant-frontend PyTurboJPEG 2>/dev/null || \
        echo "Warning: some packages failed to install. Run setup.py for guided install."
    fi
}

# Main
main() {
    check_requirements
    configure_arch
    echo ""
    install_repo
    generate_override
    install_deps
    echo ""
    echo "NanoHA installed to $INSTALL_DIR"
    echo ""
    echo "Next steps:"
    echo "  cd $INSTALL_DIR"
    echo "  python3 setup.py"
    echo ""
    echo "This will ask for your LLM key and optional Telegram/Google Cloud config."
    echo "Then start Home Assistant with: docker compose --profile ha up -d"
}

main
