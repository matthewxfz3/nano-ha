"""NanoHA Conversation Agent — forwards voice/text to Nanobot."""

import logging

import aiohttp
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEFAULT_CONTEXT_WINDOW, DEFAULT_NANOBOT_URL, DEFAULT_REQUEST_TIMEOUT

log = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up NanoHA conversation entity."""
    nanobot_url = entry.data.get("nanobot_url", DEFAULT_NANOBOT_URL)
    async_add_entities([NanoHAConversationAgent(hass, entry, nanobot_url)])


class NanoHAConversationAgent(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Conversation agent that forwards to Nanobot."""

    _attr_has_entity_name = True
    _attr_name = "NanoHA Agent"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        nanobot_url: str,
    ):
        self.hass = hass
        self.entry = entry
        self.nanobot_url = nanobot_url
        self._context: list[dict] = []
        self._attr_unique_id = f"{entry.entry_id}_conversation"

    @property
    def supported_languages(self) -> list[str] | str:
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register as conversation agent when added to HA."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister conversation agent when removed."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process user input by forwarding to Nanobot."""
        session = async_get_clientsession(self.hass)

        self._context.append({"role": "user", "content": user_input.text})
        if len(self._context) > DEFAULT_CONTEXT_WINDOW:
            self._context = self._context[-DEFAULT_CONTEXT_WINDOW:]

        try:
            resp = await session.post(
                f"{self.nanobot_url}/v1/chat/completions",
                json={"messages": self._context, "stream": False},
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            data = await resp.json()
            response_text = data["choices"][0]["message"]["content"]
        except (aiohttp.ClientError, TimeoutError, KeyError) as e:
            log.warning("Nanobot request failed: %s", e)
            response_text = "I'm having trouble connecting. Please try again."

        self._context.append({"role": "assistant", "content": response_text})

        intent_response = conversation.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )
