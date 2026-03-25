"""NanoHA Managed Hosting — HTTP API for tenant provisioning and health."""

import json
import logging
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add parent to path so tools/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tenant_manager import create_tenant, delete_tenant, get_tenant, list_tenants
from tools.ha_info import health_check

log = logging.getLogger(__name__)

HOST = os.environ.get("HOSTING_HOST", "0.0.0.0")
PORT = int(os.environ.get("HOSTING_PORT", "8080"))


class HostingAPIHandler(BaseHTTPRequestHandler):
    """HTTP API for managed hosting operations."""

    def log_message(self, format, *args):
        log.info(format, *args)

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body)

    def do_GET(self):
        if self.path == "/health":
            result = health_check()
            status = 200 if result.get("all_healthy") or result.get("success") else 503
            self._send_json(result, status)
            return

        if self.path == "/api/tenants":
            self._send_json(list_tenants())
            return

        if self.path.startswith("/api/tenants/"):
            tenant_id = self.path.split("/")[-1]
            self._send_json(get_tenant(tenant_id))
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/api/tenants":
            body = self._read_body()
            tenant_id = body.get("tenant_id", "")
            if not tenant_id:
                self._send_json({"error": "tenant_id is required"}, 400)
                return
            result = create_tenant(
                tenant_id=tenant_id,
                llm_provider=body.get("llm_provider", "anthropic"),
                llm_api_key=body.get("llm_api_key", ""),
            )
            status = 201 if result.get("success") else 409
            self._send_json(result, status)
            return

        self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        if self.path.startswith("/api/tenants/"):
            tenant_id = self.path.split("/")[-1]
            result = delete_tenant(tenant_id)
            status = 200 if result.get("success") else 404
            self._send_json(result, status)
            return

        self._send_json({"error": "Not found"}, 404)


def run_server():
    server = HTTPServer((HOST, PORT), HostingAPIHandler)
    log.info("NanoHA Hosting API running on %s:%d", HOST, PORT)
    print(f"NanoHA Hosting API running on {HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
