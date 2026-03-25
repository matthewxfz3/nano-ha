"""Tests for hosting API server."""

import json
import shutil
import tempfile
import threading
import time
from http.server import HTTPServer
from unittest.mock import patch

import httpx

from hosting.server import HostingAPIHandler


class TestHostingAPI:
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls._tenant_patch = patch("tools.tenant_manager.TENANTS_DIR", cls.tmpdir)
        cls._tenant_patch.start()

        cls.server = HTTPServer(("127.0.0.1", 18080), HostingAPIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)
        cls.base = "http://127.0.0.1:18080"

    @classmethod
    def teardown_class(cls):
        cls.server.shutdown()
        cls._tenant_patch.stop()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_health(self):
        resp = httpx.get(f"{self.base}/health", timeout=10)
        assert resp.status_code in (200, 503)
        assert "success" in resp.json()

    def test_create_tenant(self):
        resp = httpx.post(
            f"{self.base}/api/tenants",
            json={"tenant_id": "test1", "llm_provider": "anthropic", "llm_api_key": "sk-x"},
        )
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == "test1"

    def test_create_duplicate_tenant(self):
        httpx.post(f"{self.base}/api/tenants", json={"tenant_id": "dup"})
        resp = httpx.post(f"{self.base}/api/tenants", json={"tenant_id": "dup"})
        assert resp.status_code == 409

    def test_create_missing_id(self):
        resp = httpx.post(f"{self.base}/api/tenants", json={})
        assert resp.status_code == 400

    def test_list_tenants(self):
        resp = httpx.get(f"{self.base}/api/tenants")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_get_tenant(self):
        httpx.post(f"{self.base}/api/tenants", json={"tenant_id": "get_me"})
        resp = httpx.get(f"{self.base}/api/tenants/get_me")
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "get_me"

    def test_delete_tenant(self):
        httpx.post(f"{self.base}/api/tenants", json={"tenant_id": "del_me"})
        resp = httpx.delete(f"{self.base}/api/tenants/del_me")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_nonexistent(self):
        resp = httpx.delete(f"{self.base}/api/tenants/ghost")
        assert resp.status_code == 404

    def test_not_found(self):
        resp = httpx.get(f"{self.base}/api/unknown")
        assert resp.status_code == 404
