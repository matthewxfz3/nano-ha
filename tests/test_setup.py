"""Tests for setup.py configuration flow."""

from setup import HA_DEPS


class TestSetupEnvGeneration:
    def test_env_file_contains_llm_config(self):
        env_content = "LLM_PROVIDER=anthropic\nLLM_API_KEY=sk-test\nHA_URL=http://localhost:8123\nHA_TOKEN=\n"
        assert "LLM_PROVIDER=anthropic" in env_content
        assert "LLM_API_KEY=sk-test" in env_content
        assert "HA_URL=http://localhost:8123" in env_content

    def test_env_file_contains_telegram_config(self):
        env_content = "TELEGRAM_ENABLED=true\nTELEGRAM_BOT_TOKEN=123:ABC\nTELEGRAM_ALLOW_FROM=[12345]\n"
        assert "TELEGRAM_ENABLED=true" in env_content
        assert "TELEGRAM_BOT_TOKEN=123:ABC" in env_content

    def test_env_file_telegram_disabled_by_default(self):
        env_content = "TELEGRAM_ENABLED=false\nTELEGRAM_BOT_TOKEN=\n"
        assert "TELEGRAM_ENABLED=false" in env_content

    def test_env_file_contains_gcloud_config(self):
        env_content = "GOOGLE_CLOUD_STT_ENABLED=true\nGOOGLE_CLOUD_API_KEY=AIza-test\n"
        assert "GOOGLE_CLOUD_STT_ENABLED=true" in env_content

    def test_env_file_gcloud_disabled_by_default(self):
        env_content = "GOOGLE_CLOUD_STT_ENABLED=false\nGOOGLE_CLOUD_API_KEY=\n"
        assert "GOOGLE_CLOUD_STT_ENABLED=false" in env_content


class TestHADeps:
    def test_includes_frontend(self):
        assert "home-assistant-frontend" in HA_DEPS

    def test_includes_core(self):
        assert "homeassistant" in HA_DEPS

    def test_includes_turbojpeg(self):
        assert "PyTurboJPEG" in HA_DEPS

    def test_includes_httpx(self):
        assert "httpx" in HA_DEPS

    def test_includes_websockets(self):
        assert "websockets" in HA_DEPS
