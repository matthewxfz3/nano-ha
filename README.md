# NanoHA

A frictionless smart home agent. Deploy in 2 steps, then talk to your AI agent to set up and manage your entire home.

NanoHA bundles Home Assistant, local voice processing, and a lightweight AI agent (Nanobot) into a single Docker stack. The agent handles everything: deploying services, discovering devices, onboarding them, and controlling your home — all through conversation.

## What It Does

- **Agent-guided setup**: No YAML editing. No manual configuration. Talk to the agent, it deploys and configures everything.
- **Voice control**: Speak to your Home Assistant Voice PE device. The agent listens, thinks, acts, and responds.
- **Device onboarding**: Say "I have new lights" and the agent discovers, pairs, and assigns them to rooms.
- **Home control**: "Turn on the living room lights", "Is anyone home?", "What was the temperature yesterday?"
- **Multi-LLM**: Works with Claude, GPT, Gemini, or local models via Ollama.
- **Private**: Voice processing runs locally (Whisper + Piper). Your data stays on your machine.

## Setup

### Prerequisites

- Docker installed and running
- An LLM API key (Anthropic, OpenAI, or Google) — or Ollama for local models
- Home Assistant Voice PE (optional, for voice control)

### Install

```bash
git clone https://github.com/matthewxfz/nano-ha && cd nano-ha
python setup.py
```

The setup script asks two questions (LLM provider and API key), then starts the agent. From there, the agent takes over:

```
Agent: "Hi! Let's set up your smart home. I'll start Home Assistant..."
       "Home Assistant is ready. What devices do you have?"
You:   "Smart lights and a presence sensor"
Agent: "Let me scan your network..."
```

The agent deploys services as needed, discovers your devices, walks you through pairing, and assigns them to rooms.

## Architecture

```
Docker Compose
  |-- Home Assistant Core     (smart home platform)
  |-- Whisper                 (local speech-to-text)
  |-- Piper                   (local text-to-speech)
  |-- Nanobot                 (AI agent with tools)
  |-- NanoHA Bridge           (voice channel: Voice PE <-> agent)
```

Only the agent starts initially. It deploys other services incrementally based on what you need.

See [docs/architecture.md](docs/architecture.md) for details.

## How It Works

1. **You speak** to Voice PE (or type via CLI/Telegram)
2. **Whisper** transcribes your speech to text
3. **NanoHA Bridge** forwards the text to the agent
4. **Nanobot** reasons about your request, calls Home Assistant tools
5. **Response text** goes back through **Piper** (text-to-speech) to Voice PE

## Project Structure

```
nano-ha/
  docker-compose.yml      All services
  setup.py                Minimal setup (starts agent)
  tools/                  Agent tools (HA control, device mgmt, setup)
  bridge/                 HA custom component (voice channel)
  config/                 Pre-configured HA and Nanobot settings
  docs/                   Architecture, roadmap, onboarding flow
  tests/                  Test suite
```

## Docs

- [Architecture](docs/architecture.md) — system design and components
- [Roadmap](docs/roadmap.md) — what's next
- [Onboarding Flow](docs/onboarding-flow.md) — detailed agent conversation examples

## License

MIT
