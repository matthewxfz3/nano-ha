# NanoHA Roadmap

## V1 — Foundation (Complete)

### Phase 1: Agent + System Setup
- [x] Docker Compose stack (HA, Whisper, Piper)
- [x] Minimal setup.py (start agent, ask LLM key)
- [x] `ha_setup` tools: deploy services, detect hardware, create HA user, generate tokens
- [x] Shared ha_client module (WebSocket + REST)
- [x] E2E test suite with mock HA server

### Phase 2: Device Onboarding
- [x] `ha_devices` tools: discover devices, start/continue config flows, manage areas
- [x] Agent system prompt with onboarding conversation flow
- [x] Support for WiFi devices (auto-discovered by HA)

### Phase 3: Voice Channel
- [x] NanoHA Bridge (HA custom conversation agent)
- [x] Voice PE integration via HA Assist pipeline config
- [x] Conversation context management (multi-turn)

### Phase 4: Home Control
- [x] `ha_control` tools: list entities, get states, call services
- [x] Agent system prompt for natural language device control

### Phase 5: Info + Polish
- [x] `ha_info` tools: state history, health checks, config
- [x] Friendly error messages across all tools
- [x] Test suite (94 tests: unit + E2E)

---

## V2 — Enhanced Experience (Complete)

- [x] Automation management tools (list, trigger, enable/disable, reload)
- [x] Proactive monitoring (anomaly detection: open doors, motion at night, low battery)
- [x] Event subscription tool (watch_events with duration/max limits)
- [x] Google Cloud STT option (alternative to local Whisper)
- [x] Telegram channel support (via Nanobot config)
- [ ] Web chat UI for browser-based interaction

---

## V3 — Intelligence

- [ ] Multi-user voice recognition — personalize responses per household member
- [ ] Energy monitoring and optimization suggestions
- [ ] Scene learning — agent notices patterns and suggests automations
- [ ] External service integration (weather, calendar, news)
- [ ] Agent memory — learns preferences across sessions

---

## Future — Scale

- [ ] One-click deployment to Raspberry Pi / mini PC
- [ ] Multi-tenant architecture (Docker Compose -> Kubernetes)
- [ ] Managed hosting option (NanoHA-as-a-service)
- [ ] Plugin system for third-party tools
- [ ] Mobile companion app
