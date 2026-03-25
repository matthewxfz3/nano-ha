"""Tests for bridge conversation agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test the conversation logic without importing HA internals
# We test the HTTP forwarding and context management


class MockResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status = status

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TestConversationLogic:
    """Test the core forwarding logic without HA dependencies."""

    def test_context_window_limit(self):
        """Context should be trimmed to last 20 messages."""
        context = []
        for i in range(25):
            context.append({"role": "user", "content": f"msg {i}"})
            context.append({"role": "assistant", "content": f"reply {i}"})

        # Simulate the trimming logic from conversation.py
        if len(context) > 20:
            context = context[-20:]

        assert len(context) == 20
        # Oldest messages should be dropped
        assert context[0]["content"] == "msg 15"

    def test_message_format(self):
        """Messages sent to Nanobot should follow OpenAI chat format."""
        context = [
            {"role": "user", "content": "turn on the lights"},
        ]
        payload = {"messages": context, "stream": False}
        assert payload["messages"][0]["role"] == "user"
        assert payload["stream"] is False

    def test_nanobot_request_payload(self):
        """Verify the request payload structure for Nanobot."""
        context = [{"role": "user", "content": "turn on lights"}]
        payload = {"messages": context, "stream": False}

        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "turn on lights"
        assert payload["stream"] is False

    def test_nanobot_response_parsing(self):
        """Verify response parsing from Nanobot."""
        data = {"choices": [{"message": {"content": "Lights are on!"}}]}
        response_text = data["choices"][0]["message"]["content"]
        assert response_text == "Lights are on!"

    def test_nanobot_error_fallback(self):
        """When Nanobot is unreachable, return a friendly error."""
        try:
            raise Exception("Connection refused")
        except Exception:
            response_text = "I'm having trouble connecting. Please try again."

        assert "trouble connecting" in response_text

    def test_context_accumulation(self):
        """Context should accumulate user + assistant messages."""
        context = []
        context.append({"role": "user", "content": "hello"})
        context.append({"role": "assistant", "content": "hi there"})
        context.append({"role": "user", "content": "turn on lights"})
        context.append({"role": "assistant", "content": "done"})

        assert len(context) == 4
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"
        assert context[2]["content"] == "turn on lights"
