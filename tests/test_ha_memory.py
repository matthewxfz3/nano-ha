"""Tests for ha_memory tools."""

import os
import tempfile
from unittest.mock import patch

from tools.ha_memory import forget, list_memories, recall, remember


class TestMemory:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._patch = patch("tools.ha_memory.MEMORY_DIR", self.tmpdir)
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_remember_and_recall(self):
        result = remember("test.key", {"value": 42})
        assert result["success"] is True

        result = recall("test.key")
        assert result["success"] is True
        assert result["found"] is True
        assert result["value"] == {"value": 42}

    def test_recall_nonexistent(self):
        result = recall("nonexistent")
        assert result["success"] is True
        assert result["found"] is False
        assert result["value"] is None

    def test_forget(self):
        remember("to_forget", "data")
        result = forget("to_forget")
        assert result["success"] is True
        assert result["existed"] is True

        result = recall("to_forget")
        assert result["found"] is False

    def test_forget_nonexistent(self):
        result = forget("never_existed")
        assert result["success"] is True
        assert result["existed"] is False

    def test_list_memories(self):
        remember("a", 1)
        remember("b", 2)
        remember("c", 3)
        result = list_memories()
        assert result["success"] is True
        assert result["count"] == 3
        assert "a" in result["keys"]
        assert "b" in result["keys"]

    def test_overwrite(self):
        remember("key", "old")
        remember("key", "new")
        result = recall("key")
        assert result["value"] == "new"

    def test_complex_values(self):
        remember("prefs", {
            "temperature": 22,
            "lights": ["living_room", "bedroom"],
            "schedule": {"wake": "07:00", "sleep": "23:00"},
        })
        result = recall("prefs")
        assert result["value"]["temperature"] == 22
        assert len(result["value"]["lights"]) == 2

    def test_sanitizes_key(self):
        result = remember("user/../../etc/passwd", "hack")
        assert result["success"] is True
        # File should be written inside tmpdir, not escaped via path traversal
        files = os.listdir(self.tmpdir)
        assert len(files) == 1
        # No subdirectories created (no actual path traversal)
        assert all(os.path.isfile(os.path.join(self.tmpdir, f)) for f in files)
