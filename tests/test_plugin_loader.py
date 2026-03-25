"""Tests for plugin_loader."""

import os
import tempfile
from unittest.mock import patch

from tools.plugin_loader import discover_plugins, load_all_plugins, load_plugin


class TestDiscoverPlugins:
    def test_finds_example_plugin(self):
        result = discover_plugins()
        assert result["success"] is True
        assert result["count"] >= 1
        names = [p["name"] for p in result["plugins"]]
        assert "example_plugin" in names

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("tools.plugin_loader.PLUGIN_DIR", tmpdir):
                result = discover_plugins()
                assert result["count"] == 0

    def test_missing_dir(self):
        with patch("tools.plugin_loader.PLUGIN_DIR", "/nonexistent"):
            result = discover_plugins()
            assert result["count"] == 0


class TestLoadPlugin:
    def test_load_example(self):
        result = load_plugin("example_plugin")
        assert result["success"] is True
        assert result["name"] == "example_plugin"
        assert "greet" in result["tools"]
        assert "add_numbers" in result["tools"]
        assert "get_plugin_info" in result["tools"]
        assert result["metadata"]["version"] == "1.0.0"

    def test_load_nonexistent(self):
        result = load_plugin("no_such_plugin")
        assert result["success"] is False
        assert "not found" in result["error"]


class TestLoadAllPlugins:
    def test_loads_all(self):
        result = load_all_plugins()
        assert result["success"] is True
        assert result["loaded"] >= 1
        names = [p["name"] for p in result["plugins"]]
        assert "example_plugin" in names


class TestExamplePlugin:
    def test_greet(self):
        from plugins.example_plugin import greet
        result = greet("NanoHA")
        assert result["success"] is True
        assert "NanoHA" in result["message"]

    def test_add_numbers(self):
        from plugins.example_plugin import add_numbers
        result = add_numbers(3, 4)
        assert result["result"] == 7

    def test_plugin_info(self):
        from plugins.example_plugin import get_plugin_info
        result = get_plugin_info()
        assert result["name"] == "example_plugin"
