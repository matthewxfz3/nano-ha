# NanoHA Roadmap

## V1 — Foundation (Complete)

- [x] Docker Compose stack (HA, Whisper, Piper)
- [x] Minimal setup.py (LLM key, Telegram, Google Cloud STT)
- [x] `ha_setup` tools: deploy services, detect hardware, create HA user, generate tokens
- [x] `ha_devices` tools: discover devices, config flows, manage areas
- [x] `ha_control` tools: list entities, get states, call services
- [x] `ha_info` tools: state history, health checks, config
- [x] NanoHA Bridge (HA custom conversation agent for Voice PE)
- [x] Agent system prompt + 26 tool definitions
- [x] Shared ha_client module (WebSocket + REST)
- [x] Friendly error messages across all tools
- [x] E2E test suite with mock HA server

## V2 — Enhanced Experience (Complete)

- [x] Automation management tools (list, trigger, enable/disable, reload)
- [x] Proactive monitoring (anomaly detection + event subscription)
- [x] Google Cloud STT option
- [x] Telegram channel support
- [ ] Web chat UI (deferred)

## V3 — Intelligence (Complete)

- [x] Energy monitoring and optimization suggestions
- [x] Scene learning (pattern analysis + automation suggestions)
- [x] External services (weather via Open-Meteo, news via Google News RSS)
- [x] Agent memory (persistent key-value store with path traversal protection)
- [ ] Multi-user voice recognition (requires real hardware testing)

## Future — Scale

- [ ] One-click deployment to Raspberry Pi / mini PC
- [ ] Multi-tenant architecture (Docker Compose -> Kubernetes)
- [ ] Managed hosting option (NanoHA-as-a-service)
- [ ] Plugin system for third-party tools
- [ ] Mobile companion app
