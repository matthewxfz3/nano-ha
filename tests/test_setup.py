"""Tests for setup.py configuration flow."""

import os
import tempfile
from unittest.mock import MagicMock, patch


class TestSetupEnvGeneration:
    def test_env_file_contains_llm_config(self):
        """Verify .env has LLM provider and key."""
        env_content = (
            "LLM_PROVIDER=anthropic\n"
            "LLM_API_KEY=sk-test\n"
            "HA_URL=http://homeassistant:8123\n"
            "HA_TOKEN=\n"
        )
        assert "LLM_PROVIDER=anthropic" in env_content
        assert "LLM_API_KEY=sk-test" in env_content

    def test_env_file_contains_telegram_config(self):
        """Verify .env has Telegram config when enabled."""
        env_content = (
            "TELEGRAM_ENABLED=true\n"
            "TELEGRAM_BOT_TOKEN=123:ABC\n"
            "TELEGRAM_ALLOW_FROM=[12345]\n"
        )
        assert "TELEGRAM_ENABLED=true" in env_content
        assert "TELEGRAM_BOT_TOKEN=123:ABC" in env_content
        assert "TELEGRAM_ALLOW_FROM=[12345]" in env_content

    def test_env_file_telegram_disabled_by_default(self):
        """Verify Telegram is disabled when skipped."""
        env_content = "TELEGRAM_ENABLED=false\nTELEGRAM_BOT_TOKEN=\n"
        assert "TELEGRAM_ENABLED=false" in env_content
        assert "TELEGRAM_BOT_TOKEN=\n" in env_content

    def test_env_file_contains_gcloud_config(self):
        """Verify .env has Google Cloud STT config when enabled."""
        env_content = (
            "GOOGLE_CLOUD_STT_ENABLED=true\n"
            "GOOGLE_CLOUD_API_KEY=AIza-test\n"
        )
        assert "GOOGLE_CLOUD_STT_ENABLED=true" in env_content
        assert "GOOGLE_CLOUD_API_KEY=AIza-test" in env_content

    def test_env_file_gcloud_disabled_by_default(self):
        """Verify Google Cloud STT is disabled when skipped."""
        env_content = "GOOGLE_CLOUD_STT_ENABLED=false\nGOOGLE_CLOUD_API_KEY=\n"
        assert "GOOGLE_CLOUD_STT_ENABLED=false" in env_content
