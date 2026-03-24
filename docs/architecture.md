# NanoHA Architecture

## Overview

NanoHA is a Docker Compose stack that bundles a smart home platform (Home Assistant), local voice processing (Whisper + Piper), and an AI agent (Nanobot) into a single deployable unit.

The key design principle: **the agent is the primary interface**. Users don't configure Home Assistant directly. They talk to the agent, and the agent configures everything.

## Components

```
+--------------------------------------------------+
|  NanoHA (Docker Compose)                         |
|                                                   |
|  +------------+  +-----------+  +--------------+ |
|  | Home       |  | Whisper   |  | Nanobot      | |
|  | Assistant  |  | (STT)     |  | (AI Agent)   | |
|  | Core       |  +-----------+  |              | |
|  |            |  | Piper     |  | Tools:       | |
|  |            |  | (TTS)     |  |  - ha_setup  | |
|  |            |  +-----------+  |  - ha_devices| |
|  +------------+                 |  - ha_control| |
|       ^                         |  - ha_info   | |
|       |                         +--------------+ |
|       v                              ^           |
|  +------------------------------------------+   |
|  | NanoHA Bridge (HA custom component)       |   |
|  | Conversation Agent: voice <-> Nanobot     |   |
|  +------------------------------------------+   |
+--------------------------------------------------+
         ^
         |
    Voice PE (WiFi mic + speaker)
```

## Service Roles

### Nanobot (AI Agent)
- Lightweight Python agent (~4,000 lines of code)
- Multi-LLM: Claude, GPT, Gemini, DeepSeek, Ollama
- Executes tools to interact with Home Assistant
- Maintains conversation context and memory
- Starts first; deploys other services on demand

### Home Assistant Core
- Smart home platform with 2,000+ device integrations
- Manages device state, automations, and history
- Provides the Assist voice pipeline (STT -> conversation agent -> TTS)
- Deployed by the agent during onboarding

### Whisper (Speech-to-Text)
- Local Faster Whisper via Wyoming protocol
- Transcribes voice from Voice PE to text
- No cloud dependency, no API key needed
- Deployed when voice control is requested

### Piper (Text-to-Speech)
- Local neural TTS via Wyoming protocol
- Converts agent responses to speech
- Plays through Voice PE speaker
- Deployed alongside Whisper

### NanoHA Bridge
- Home Assistant custom component
- Registers as a conversation agent in HA's Assist pipeline
- Forwards transcribed text from Whisper to Nanobot
- Returns Nanobot's response to Piper for speech output

## Agent Tools

| Tool | Purpose | HA API |
|---|---|---|
| `ha_setup.deploy_service()` | Start Docker services | Docker Compose |
| `ha_setup.create_ha_user()` | Create admin account | HA onboarding API |
| `ha_setup.generate_ha_token()` | Create access token | HA auth API |
| `ha_setup.configure_assist_pipeline()` | Wire voice pipeline | WebSocket |
| `ha_devices.discover_devices()` | Find new devices | HA discovery + WebSocket |
| `ha_devices.start_config_flow()` | Begin device setup | WebSocket config_entries/flow |
| `ha_devices.create_area()` | Create room/area | WebSocket area_registry |
| `ha_control.call_service()` | Control devices | WebSocket call_service |
| `ha_control.list_entities()` | Query device states | WebSocket get_states |
| `ha_info.get_history()` | State history | REST /api/history |
| `ha_info.health_check()` | System status | All services |

## Communication

- **Agent <-> HA**: WebSocket API via `python-hass-client` (primary), REST API (fallback for history)
- **Voice PE <-> HA**: Wyoming protocol over WiFi
- **Bridge <-> Nanobot**: HTTP within Docker network
- **User <-> Agent**: Voice (via Voice PE), CLI, or messaging (Telegram/WhatsApp via Nanobot)

## Incremental Deployment

Not all services start at once. The agent deploys them as needed:

1. `setup.py` starts **Nanobot only**
2. Agent deploys **Home Assistant** when user wants to set up devices
3. Agent deploys **Whisper + Piper** when user has a Voice PE
4. Agent can add **Zigbee2MQTT** in the future if Zigbee devices are present

This keeps the initial footprint small and avoids running unnecessary services.
