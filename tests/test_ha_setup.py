"""Tests for ha_setup tools."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from tools.ha_setup import (
    _exchange_auth_code,
    check_docker,
    configure_assist_pipeline,
    create_ha_user,
    detect_hardware,
    deploy_service,
    generate_ha_token,
)


class TestCheckDocker:
    @patch("tools.ha_setup.subprocess.run")
    def test_docker_running(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = check_docker()
        assert result["installed"] is True
        assert result["running"] is True
        assert result["error"] is None

    @patch("tools.ha_setup.subprocess.run")
    def test_docker_not_running(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Cannot connect")
        result = check_docker()
        assert result["running"] is False
        assert result["error"] == "Cannot connect"


class TestDetectHardware:
    @patch("os.path.exists", return_value=False)
    def test_no_dongle(self, mock_exists):
        result = detect_hardware()
        assert result["zigbee_dongle"] is None

    @patch("os.path.exists", side_effect=lambda p: p == "/dev/ttyUSB0")
    def test_dongle_found(self, mock_exists):
        result = detect_hardware()
        assert result["zigbee_dongle"] == "/dev/ttyUSB0"


class TestDeployService:
    @patch("tools.ha_setup.subprocess.run")
    def test_deploy_ha(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Started", stderr="")
        result = deploy_service("homeassistant")
        assert result["success"] is True
        assert result["service"] == "homeassistant"
        cmd = mock_run.call_args[0][0]
        assert "--profile" in cmd
        assert "ha" in cmd

    @patch("tools.ha_setup.subprocess.run")
    def test_deploy_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        result = deploy_service("homeassistant")
        assert result["success"] is False
        assert result["error"] == "Error"


class TestCreateHaUser:
    @patch("tools.ha_setup.httpx.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"auth_code": "abc123"},
        )
        result = create_ha_user()
        assert result["success"] is True
        assert result["auth_code"] == "abc123"

    @patch("tools.ha_setup.httpx.post")
    def test_already_onboarded(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=403,
            text="User step already done",
        )
        result = create_ha_user()
        assert result["success"] is False
        assert result["status_code"] == 403

    @patch("tools.ha_setup.httpx.post")
    def test_connection_error(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        result = create_ha_user()
        assert result["success"] is False
        assert "Cannot connect" in result["error"]

    @patch("tools.ha_setup.httpx.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        result = create_ha_user()
        assert result["success"] is False
        assert "Timeout" in result["error"]


class TestExchangeAuthCode:
    @patch("tools.ha_setup.httpx.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok123",
                "refresh_token": "ref456",
                "token_type": "Bearer",
                "expires_in": 1800,
            },
        )
        result = _exchange_auth_code("abc123")
        assert result["success"] is True
        assert result["access_token"] == "tok123"

    @patch("tools.ha_setup.httpx.post")
    def test_invalid_code(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=400,
            text="Invalid code",
        )
        result = _exchange_auth_code("bad_code")
        assert result["success"] is False


class TestConfigureAssistPipeline:
    @patch("tools.ha_setup.ws_send")
    def test_create_and_set_preferred(self, mock_ws):
        mock_ws.side_effect = [
            {
                "success": True,
                "result": {
                    "id": "pipeline-001",
                    "name": "NanoHA Voice",
                    "conversation_engine": "nanoha",
                },
            },
            {"success": True, "result": None},
        ]
        result = configure_assist_pipeline(access_token="tok123")
        assert result["success"] is True
        assert result["pipeline_id"] == "pipeline-001"
        assert mock_ws.call_count == 2

    @patch("tools.ha_setup.ws_send")
    def test_create_fails(self, mock_ws):
        mock_ws.return_value = {"success": False, "error": {"message": "fail"}}
        result = configure_assist_pipeline(access_token="tok123")
        assert result["success"] is False


class TestGenerateHaToken:
    @patch("tools.ha_setup.ws_send")
    @patch("tools.ha_setup._exchange_auth_code")
    @patch("tools.ha_setup.create_ha_user")
    def test_full_flow(self, mock_user, mock_exchange, mock_ws):
        mock_user.return_value = {"success": True, "auth_code": "code123"}
        mock_exchange.return_value = {"success": True, "access_token": "short_tok"}
        mock_ws.return_value = {"success": True, "result": "long_lived_tok"}
        result = generate_ha_token()
        assert result["success"] is True
        assert result["token"] == "long_lived_tok"

    @patch("tools.ha_setup.create_ha_user")
    def test_user_creation_fails(self, mock_user):
        mock_user.return_value = {"success": False, "error": "already done"}
        result = generate_ha_token()
        assert result["success"] is False
