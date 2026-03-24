"""NanoHA Control Tools — entity states and service calls."""


def list_entities(domain: str = None, area: str = None) -> dict:
    """List entities, optionally filtered by domain or area."""
    # TODO: Implement via WebSocket get_states
    return {"status": "not_implemented", "entities": []}


def get_entity_state(entity_id: str) -> dict:
    """Get current state and attributes of an entity."""
    # TODO: Implement via WebSocket get_states + filter
    return {"status": "not_implemented"}


def call_service(
    domain: str,
    service: str,
    entity_id: str = None,
    data: dict = None,
) -> dict:
    """Call a Home Assistant service (e.g., light.turn_on)."""
    # TODO: Implement via WebSocket call_service
    return {"status": "not_implemented"}
