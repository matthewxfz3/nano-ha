"""Tests for tenant_manager."""

import os
import tempfile
from unittest.mock import patch

from tools.tenant_manager import create_tenant, delete_tenant, get_tenant, list_tenants


class TestTenantManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._patch = patch("tools.tenant_manager.TENANTS_DIR", self.tmpdir)
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_tenant(self):
        result = create_tenant("tenant1", llm_provider="anthropic", llm_api_key="sk-test")
        assert result["success"] is True
        assert result["tenant_id"] == "tenant1"
        assert os.path.exists(os.path.join(self.tmpdir, "tenant1", ".env"))
        assert os.path.isdir(os.path.join(self.tmpdir, "tenant1", "ha_config"))
        assert os.path.isdir(os.path.join(self.tmpdir, "tenant1", "memory"))

    def test_create_duplicate(self):
        create_tenant("dup")
        result = create_tenant("dup")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_list_tenants(self):
        create_tenant("a")
        create_tenant("b")
        result = list_tenants()
        assert result["success"] is True
        assert result["count"] == 2
        ids = [t["tenant_id"] for t in result["tenants"]]
        assert "a" in ids and "b" in ids

    def test_list_empty(self):
        result = list_tenants()
        assert result["count"] == 0

    def test_get_tenant(self):
        create_tenant("t1", llm_api_key="sk-secret-key-12345")
        result = get_tenant("t1")
        assert result["success"] is True
        assert result["config"]["TENANT_ID"] == "t1"
        # API key should be redacted
        assert "..." in result["config"]["LLM_API_KEY"]

    def test_get_nonexistent(self):
        result = get_tenant("nope")
        assert result["success"] is False

    def test_delete_tenant(self):
        create_tenant("to_delete")
        result = delete_tenant("to_delete")
        assert result["success"] is True
        assert not os.path.exists(os.path.join(self.tmpdir, "to_delete"))

    def test_delete_nonexistent(self):
        result = delete_tenant("ghost")
        assert result["success"] is False

    def test_sanitizes_tenant_id(self):
        result = create_tenant("../../etc/evil")
        assert result["success"] is True
        # Should not escape tenants dir
        assert not os.path.exists("/etc/evil")
        files = os.listdir(self.tmpdir)
        assert len(files) == 1
