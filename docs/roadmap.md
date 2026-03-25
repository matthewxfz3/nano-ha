# NanoHA Roadmap

## V1 — Foundation (Complete)

- [x] Docker Compose stack (HA, Whisper, Piper)
- [x] Minimal setup.py (LLM key, Telegram, Google Cloud STT)
- [x] `ha_setup` tools: deploy services, detect hardware, create HA user, generate tokens
- [x] `ha_devices` tools: discover devices, config flows, manage areas
- [x] `ha_control` tools: list entities, get states, call services
- [x] `ha_info` tools: state history, health checks, config
- [x] NanoHA Bridge (HA custom conversation agent for Voice PE)
- [x] Agent system prompt + tool definitions
- [x] Shared ha_client module (WebSocket + REST)
- [x] Friendly error messages across all tools
- [x] E2E test suite with mock HA server

## V2 — Enhanced Experience (Complete)

- [x] Automation management tools (list, trigger, enable/disable, reload)
- [x] Proactive monitoring (anomaly detection + event subscription)
- [x] Google Cloud STT option
- [x] Telegram channel support

## V3 — Intelligence (Complete)

- [x] Energy monitoring and optimization suggestions
- [x] Scene learning (pattern analysis + automation suggestions)
- [x] External services (weather via Open-Meteo, news via Google News RSS)
- [x] Agent memory (persistent key-value store)
- [x] Multi-user profile management (person entities, per-user preferences, presence)

## Future — Scale (Complete)

- [x] One-click deployment to Raspberry Pi / mini PC (deploy.sh with arch detection)
- [x] Multi-tenant config (isolated .env, data dirs, compose overrides)
- [x] Managed hosting (Dockerfile + HTTP API for tenant CRUD + health)
- [x] Plugin system (auto-discovery, loader, example plugin)
- [ ] Mobile companion app (deferred)

## Stats

- **163 tests** passing
- **16 tool modules** (ha_setup, ha_control, ha_devices, ha_info, ha_automation, ha_monitor, ha_energy, ha_scenes, ha_memory, ha_users, external_services, plugin_loader, tenant_manager, ha_client, google_cloud_stt, hosting API)
- **1 HA custom component** (bridge)
- **1 plugin** (example)
