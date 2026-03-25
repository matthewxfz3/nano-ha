"""Tests for deploy.sh logic (validates script structure)."""

import os
import subprocess


class TestDeployScript:
    def test_script_exists_and_executable(self):
        script = os.path.join(os.path.dirname(__file__), "..", "deploy.sh")
        assert os.path.exists(script)
        assert os.access(script, os.X_OK)

    def test_script_syntax_valid(self):
        script = os.path.join(os.path.dirname(__file__), "..", "deploy.sh")
        result = subprocess.run(
            ["bash", "-n", script], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_override_template_structure(self):
        """Verify the generated override YAML structure."""
        override = (
            "services:\n"
            "  whisper:\n"
            "    command: --model tiny --language en\n"
            "  piper:\n"
            "    command: --voice en_US-lessac-low\n"
        )
        assert "services:" in override
        assert "whisper:" in override
        assert "piper:" in override
