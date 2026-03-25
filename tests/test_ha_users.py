"""Tests for ha_users tools."""

import tempfile
from unittest.mock import patch

from tools.ha_users import (
    get_context_for_user,
    get_user_preference,
    get_user_profile,
    list_persons,
    set_user_preference,
    who_is_home,
)

MOCK_STATES = {
    "success": True,
    "result": [
        {
            "entity_id": "person.matt",
            "state": "home",
            "attributes": {"friendly_name": "Matt", "source": "device_tracker.phone"},
        },
        {
            "entity_id": "person.alice",
            "state": "not_home",
            "attributes": {"friendly_name": "Alice", "source": "device_tracker.alice_phone"},
        },
        {"entity_id": "light.living_room", "state": "on", "attributes": {}},
    ],
}


class TestListPersons:
    @patch("tools.ha_users.ws_send", return_value=MOCK_STATES)
    def test_filters_persons(self, mock_ws):
        result = list_persons()
        assert result["success"] is True
        assert result["count"] == 2
        names = [p["name"] for p in result["persons"]]
        assert "Matt" in names
        assert "Alice" in names

    @patch("tools.ha_users.ws_send", return_value={"success": False})
    def test_failure(self, mock_ws):
        result = list_persons()
        assert result["success"] is False


class TestWhoIsHome:
    @patch("tools.ha_users.ws_send", return_value=MOCK_STATES)
    def test_home_and_away(self, mock_ws):
        result = who_is_home()
        assert result["success"] is True
        assert "Matt" in result["home"]
        assert "Alice" in result["away"]
        assert result["anyone_home"] is True


class TestUserPreferences:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._patch = patch("tools.ha_memory.MEMORY_DIR", self.tmpdir)
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_set_and_get_preference(self):
        set_user_preference("matt", "preferred_temperature", 22)
        result = get_user_preference("matt", "preferred_temperature")
        assert result["value"] == 22

    def test_get_missing_preference(self):
        result = get_user_preference("matt", "nonexistent")
        assert result["value"] is None
        assert result["found"] is False

    def test_profile_accumulates(self):
        set_user_preference("matt", "wake_time", "07:00")
        set_user_preference("matt", "preferred_temperature", 22)
        profile = get_user_profile("matt")
        assert profile["profile"]["wake_time"] == "07:00"
        assert profile["profile"]["preferred_temperature"] == 22

    def test_no_profile(self):
        result = get_user_profile("unknown")
        assert result["profile"] is None


class TestGetContext:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._patch = patch("tools.ha_memory.MEMORY_DIR", self.tmpdir)
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("tools.ha_users.ws_send", return_value=MOCK_STATES)
    def test_full_context(self, mock_ws):
        set_user_preference("matt", "wake_time", "07:00")
        result = get_context_for_user("Matt")
        assert result["success"] is True
        assert result["presence"] == "home"
        assert result["profile"]["wake_time"] == "07:00"

    @patch("tools.ha_users.ws_send", return_value=MOCK_STATES)
    def test_unknown_user(self, mock_ws):
        result = get_context_for_user("unknown")
        assert result["presence"] == "unknown"
        assert result["profile"] is None
