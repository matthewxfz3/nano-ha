"""NanoHA Bridge — Home Assistant custom component for voice channel."""

from .const import DOMAIN


async def async_setup_entry(hass, entry):
    """Set up NanoHA Bridge from a config entry."""
    # TODO: Register conversation agent
    return True


async def async_unload_entry(hass, entry):
    """Unload NanoHA Bridge."""
    return True
