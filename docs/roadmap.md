# NanoHA Roadmap

## V1 — Foundation (Current)

### Phase 1: Agent + System Setup
- [x] Docker Compose stack (HA, Whisper, Piper)
- [x] Minimal setup.py (start agent, ask LLM key)
- [x] `ha_setup` tools: deploy services, detect hardware, create HA user, generate tokens
- [x] Shared ha_client module (WebSocket + REST)
- [x] E2E test suite with mock HA server (68 tests)

### Phase 2: Device Onboarding
- [x] `ha_devices` tools: discover devices, start/continue config flows, manage areas
- [ ] Agent system prompt with onboarding conversation flow
- [x] Support for WiFi devices (auto-discovered by HA)

### Phase 3: Voice Channel
- [x] NanoHA Bridge (HA custom conversation agent)
- [x] Voice PE integration via HA Assist pipeline config
- [x] Conversation context management (multi-turn)

### Phase 4: Home Control
- [x] `ha_control` tools: list entities, get states, call services
- [ ] Agent system prompt for natural language device control

### Phase 5: Info + Polish
- [x] `ha_info` tools: state history, health checks, config
- [ ] Friendly error messages across all tools
- [x] Test suite (unit + E2E)

---

## V2 — Enhanced Experience

- [ ] Automation management tools (list, create, trigger, enable/disable)
- [ ] Proactive monitoring (event subscription, anomaly detection)
- [ ] Cloud STT/TTS option (OpenAI Whisper API + ElevenLabs)
- [ ] Scheduled automations via agent ("every morning at 7, turn on lights gradually")
- [ ] Web chat UI for browser-based interaction
- [ ] Telegram/WhatsApp channel (Nanobot built-in support)

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
