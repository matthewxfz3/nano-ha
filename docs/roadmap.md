# NanoHA Roadmap

## V1 — Foundation (Current)

### Phase 1: Agent + System Setup
- [ ] Docker Compose stack (HA, Whisper, Piper, Nanobot)
- [ ] Minimal setup.py (start agent, ask LLM key)
- [ ] `ha_setup` tools: deploy services, detect hardware, create HA user, generate tokens

### Phase 2: Device Onboarding
- [ ] `ha_devices` tools: discover devices, start/continue config flows, manage areas
- [ ] Agent-guided onboarding conversation flow
- [ ] Support for WiFi devices (auto-discovered by HA)
- [ ] Support for Zigbee devices (via Zigbee2MQTT, when coordinator present)

### Phase 3: Voice Channel
- [ ] NanoHA Bridge (HA custom conversation agent)
- [ ] Voice PE integration via HA Assist pipeline
- [ ] Conversation context management (multi-turn)

### Phase 4: Home Control
- [ ] `ha_control` tools: list entities, get states, call services
- [ ] Natural language device control ("turn on the lights", "set to 22 degrees")

### Phase 5: Info + Polish
- [ ] `ha_info` tools: state history, health checks, error logs
- [ ] Friendly error messages
- [ ] Test suite

---

## V2 — Enhanced Experience

- [ ] Cloud STT/TTS option (OpenAI Whisper API + ElevenLabs) for higher voice quality
- [ ] Proactive monitoring — agent alerts on anomalies ("motion at front door at 2 AM")
- [ ] Scheduled automations via agent ("every morning at 7, turn on lights gradually")
- [ ] Web chat UI for browser-based interaction
- [ ] Telegram/WhatsApp channel (Nanobot has built-in support)

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
