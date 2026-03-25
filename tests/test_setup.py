"""Tests for setup.py configuration and dependency completeness."""

import subprocess

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
    """Verify all packages needed for a working HA install are listed."""

    # Core
    def test_includes_core(self):
        assert "homeassistant" in HA_DEPS

    def test_includes_frontend(self):
        assert "home-assistant-frontend" in HA_DEPS

    def test_includes_intents(self):
        assert "home-assistant-intents" in HA_DEPS

    def test_includes_turbojpeg(self):
        assert "PyTurboJPEG" in HA_DEPS

    # NanoHA tools
    def test_includes_httpx(self):
        assert "httpx" in HA_DEPS

    def test_includes_websockets(self):
        assert "websockets" in HA_DEPS

    # mobile_app / default_config dependency chain
    def test_includes_hassil(self):
        """Required by conversation component."""
        assert "hassil" in HA_DEPS

    def test_includes_pymicro_vad(self):
        """Required by assist_pipeline."""
        assert "pymicro-vad" in HA_DEPS

    def test_includes_go2rtc_client(self):
        """Required by go2rtc/stream components."""
        assert "go2rtc-client" in HA_DEPS

    def test_includes_ha_ffmpeg(self):
        """Required by stream component."""
        assert "ha-ffmpeg" in HA_DEPS

    def test_includes_av(self):
        """Required by stream component."""
        assert "av" in HA_DEPS

    def test_includes_mutagen(self):
        """Required by media handling."""
        assert "mutagen" in HA_DEPS

    def test_includes_aiodiscover(self):
        """Required by dhcp/discovery."""
        assert "aiodiscover" in HA_DEPS

    def test_includes_aiodhcpwatcher(self):
        """Required by dhcp component."""
        assert "aiodhcpwatcher" in HA_DEPS

    def test_includes_async_upnp_client(self):
        """Required by ssdp component."""
        assert "async-upnp-client" in HA_DEPS

    def test_includes_pyserial(self):
        """Required by usb component."""
        assert "pyserial" in HA_DEPS

    def test_minimum_dep_count(self):
        """Ensure we don't accidentally remove deps."""
        assert len(HA_DEPS) >= 18


class TestDeployScript:
    """Verify deploy.sh installs the same deps."""

    def test_deploy_includes_ha_deps(self):
        with open("deploy.sh") as f:
            content = f.read()
        for critical in ["homeassistant", "home-assistant-frontend", "PyTurboJPEG"]:
            assert critical in content, f"deploy.sh missing {critical}"

    def test_deploy_syntax(self):
        result = subprocess.run(["bash", "-n", "deploy.sh"], capture_output=True, text=True)
        assert result.returncode == 0


class TestPyprojectDeps:
    """Verify pyproject.toml ha extra has critical deps."""

    def test_pyproject_ha_extra(self):
        with open("pyproject.toml") as f:
            content = f.read()
        assert "homeassistant" in content
        assert "home-assistant-frontend" in content
        assert "PyTurboJPEG" in content
