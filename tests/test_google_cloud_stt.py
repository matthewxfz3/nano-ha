"""Tests for Google Cloud STT integration."""

import os
from unittest.mock import patch

from integrations.google_cloud_stt import configure_google_cloud_stt, get_stt_engine


class TestConfigureGoogleCloudSTT:
    @patch("integrations.google_cloud_stt.ws_send")
    def test_success(self, mock_ws):
        mock_ws.side_effect = [
            # Start config flow
            {"success": True, "result": {"flow_id": "gcloud-flow-1", "step_id": "user"}},
            # Submit API key
            {"success": True, "result": {"type": "create_entry", "title": "Google Cloud"}},
        ]
        result = configure_google_cloud_stt(api_key="AIza-test-key")
        assert result["success"] is True
        assert result["engine"] == "google_cloud"

    @patch("integrations.google_cloud_stt.ws_send")
    def test_no_api_key(self, mock_ws):
        result = configure_google_cloud_stt(api_key="")
        assert result["success"] is False
        assert "API key" in result["error"]

    @patch("integrations.google_cloud_stt.ws_send")
    def test_flow_start_fails(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": "unknown handler"}
        result = configure_google_cloud_stt(api_key="AIza-test")
        assert result["success"] is False
        assert "integration" in result["error"].lower()

    @patch("integrations.google_cloud_stt.ws_send")
    def test_api_key_rejected(self, mock_ws):
        mock_ws.side_effect = [
            {"success": True, "result": {"flow_id": "flow-1", "step_id": "user"}},
            {"success": False, "error": "invalid_key"},
        ]
        result = configure_google_cloud_stt(api_key="bad-key")
        assert result["success"] is False
        assert "API key" in result["error"]


class TestGetSTTEngine:
    def test_default_is_wyoming(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GOOGLE_CLOUD_STT_ENABLED", None)
            assert get_stt_engine() == "wyoming"

    def test_google_cloud_when_enabled(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_STT_ENABLED": "true"}):
            assert get_stt_engine() == "google_cloud"

    def test_wyoming_when_disabled(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_STT_ENABLED": "false"}):
            assert get_stt_engine() == "wyoming"
