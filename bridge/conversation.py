"""NanoHA Conversation Agent — forwards voice/text to Nanobot."""

from homeassistant.components.conversation import ConversationEntity, ConversationResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NANOBOT_URL


class NanoHAConversationAgent(ConversationEntity):
    """Conversation agent that forwards to Nanobot."""

    def __init__(self, hass, nanobot_url: str = DEFAULT_NANOBOT_URL):
        self.hass = hass
        self.nanobot_url = nanobot_url
        self._context = []

    @property
    def supported_languages(self):
        return ["en"]

    async def async_process(self, user_input) -> ConversationResult:
        """Process user input by forwarding to Nanobot."""
        session = async_get_clientsession(self.hass)

        self._context.append({"role": "user", "content": user_input.text})

        # Keep last 10 turns
        if len(self._context) > 20:
            self._context = self._context[-20:]

        try:
            async with session.post(
                f"{self.nanobot_url}/v1/chat/completions",
                json={
                    "messages": self._context,
                    "stream": False,
                },
                timeout=30,
            ) as resp:
                data = await resp.json()
                response_text = data["choices"][0]["message"]["content"]
        except Exception:
            response_text = "I'm having trouble connecting. Please try again."

        self._context.append({"role": "assistant", "content": response_text})

        return ConversationResult(response=response_text)
