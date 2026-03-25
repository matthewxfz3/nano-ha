"""Live agent smoke tests — verifies agent + Gemini + HA tools work end-to-end.

Run against a live HA instance:
    HA_URL=http://localhost:8123 HA_TOKEN=... LLM_API_KEY=... \
    PYTHONPATH=. python3 -m pytest tests/test_agent_live.py -v

Skip in CI (no live HA): these tests are gated on NANOHA_LIVE_TEST=1
"""

import os
import sys

import pytest

LIVE = os.environ.get("NANOHA_LIVE_TEST", "") == "1"
skip_reason = "Set NANOHA_LIVE_TEST=1 with HA_URL, HA_TOKEN, LLM_API_KEY to run"

if LIVE:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent import send_message


@pytest.mark.skipif(not LIVE, reason=skip_reason)
class TestAgentBasicResponses:
    """Agent should respond coherently to basic questions."""

    def test_greeting(self):
        resp = send_message("Hello")
        assert len(resp) > 5
        assert "error" not in resp.lower() or "Error" not in resp

    def test_identity(self):
        resp = send_message("What are you?")
        # Should mention home / smart home / NanoHA
        lower = resp.lower()
        assert any(w in lower for w in ["home", "nanoha", "agent", "assistant"])


@pytest.mark.skipif(not LIVE, reason=skip_reason)
class TestAgentToolCalls:
    """Agent should use tools when asked about the home."""

    def test_ha_version(self):
        resp = send_message("What version of Home Assistant is running?")
        assert "2026" in resp or "version" in resp.lower()

    def test_list_areas(self):
        resp = send_message("What rooms do I have?")
        lower = resp.lower()
        assert any(w in lower for w in ["living room", "kitchen", "bedroom", "office"])

    def test_list_devices(self):
        resp = send_message("List all my devices")
        # Fresh install has at least the backup device
        lower = resp.lower()
        assert "backup" in lower or "device" in lower or "no " in lower

    def test_anomaly_check(self):
        resp = send_message("Is anything unusual happening at home?")
        lower = resp.lower()
        # Should respond with anomaly status
        assert any(w in lower for w in ["no anomal", "nothing unusual", "everything", "no issues", "no unusual"])

    def test_entity_listing(self):
        resp = send_message("Show me all sensors")
        lower = resp.lower()
        assert "sensor" in lower or "backup" in lower or "no " in lower


@pytest.mark.skipif(not LIVE, reason=skip_reason)
class TestAgentMultiStep:
    """Agent should handle multi-step reasoning."""

    def test_health_and_config(self):
        resp = send_message("Check the system health and tell me the HA config")
        lower = resp.lower()
        # Should mention version or health status
        assert any(w in lower for w in ["2026", "running", "healthy", "version", "home"])

    def test_area_and_devices(self):
        resp = send_message("List my areas and devices")
        lower = resp.lower()
        assert any(w in lower for w in ["living room", "kitchen", "bedroom", "area", "room", "device", "no device", "backup"])


@pytest.mark.skipif(not LIVE, reason=skip_reason)
class TestAgentErrorHandling:
    """Agent should handle bad requests gracefully."""

    def test_nonexistent_entity(self):
        resp = send_message("What is the state of sensor.fake_nonexistent_xyz?")
        lower = resp.lower()
        # Should not crash, should mention not found or similar
        assert len(resp) > 5
        assert "error" not in resp[:5].lower()  # not a raw error

    def test_unknown_device(self):
        resp = send_message("Turn on the quantum flux capacitor")
        # Should respond gracefully, not crash
        assert len(resp) > 5
