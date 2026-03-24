"""NanoHA Info Tools — history, health checks, diagnostics."""


def get_history(entity_id: str, hours: int = 24) -> dict:
    """Get state history for an entity."""
    # TODO: Implement via REST GET /api/history/period
    return {"status": "not_implemented", "history": []}


def health_check() -> dict:
    """Check health of all NanoHA services."""
    # TODO: Ping HA, Whisper, Piper, Nanobot
    return {"status": "not_implemented", "services": {}}


def get_config() -> dict:
    """Get HA configuration summary."""
    # TODO: Implement via WebSocket get_config
    return {"status": "not_implemented"}
