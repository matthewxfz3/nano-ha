"""Mock Home Assistant server for E2E testing.

Simulates HA's REST API and WebSocket API with in-memory state.
"""

import asyncio
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import websockets


class MockHAState:
    """Shared state for the mock HA server."""

    def __init__(self):
        self.onboarded = False
        self.auth_codes = {}  # code -> user
        self.tokens = {"test-token": "admin"}  # token -> user
        self.entities = [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {"friendly_name": "Living Room", "brightness": 0},
                "last_changed": "2026-03-24T10:00:00Z",
                "last_updated": "2026-03-24T10:00:00Z",
            },
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"friendly_name": "Temperature", "unit_of_measurement": "°C"},
                "last_changed": "2026-03-24T10:00:00Z",
                "last_updated": "2026-03-24T10:00:00Z",
            },
        ]
        self.areas = [
            {"area_id": "area-lr", "name": "Living Room", "floor_id": None},
        ]
        self.devices = [
            {
                "id": "dev-001",
                "name": "Test Light",
                "manufacturer": "Test",
                "model": "TL-100",
                "area_id": "area-lr",
                "disabled_by": None,
                "name_by_user": None,
            },
        ]
        self.config = {
            "location_name": "NanoHA Test",
            "version": "2026.3.3",
            "unit_system": {"temperature": "°C"},
            "components": ["light", "sensor"],
        }
        self.service_calls = []


state = MockHAState()


class MockHAHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler simulating HA REST API."""

    def log_message(self, format, *args):
        pass  # suppress logs during tests

    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return token in state.tokens
        return False

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/":
            self._send_json({"message": "API running."})
            return

        if not self._check_auth():
            self._send_json({"message": "Unauthorized"}, 401)
            return

        if path == "/api/states":
            self._send_json(state.entities)
            return

        if path.startswith("/api/states/"):
            entity_id = path[len("/api/states/"):]
            for e in state.entities:
                if e["entity_id"] == entity_id:
                    self._send_json(e)
                    return
            self._send_json({"message": "Entity not found"}, 404)
            return

        if path.startswith("/api/history/period"):
            qs = parse_qs(parsed.query)
            filter_id = qs.get("filter_entity_id", [None])[0]
            if filter_id:
                history = [e for e in state.entities if e["entity_id"] == filter_id]
                self._send_json([history] if history else [])
            else:
                self._send_json([state.entities])
            return

        self._send_json({"message": "Not found"}, 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        parsed = urlparse(self.path)
        path = parsed.path

        # Onboarding — no auth required
        if path == "/api/onboarding/users":
            if state.onboarded:
                self._send_json({"message": "User step already done"}, 403)
                return
            data = json.loads(body)
            code = "test-auth-code-123"
            state.auth_codes[code] = data.get("username", "admin")
            state.onboarded = True
            self._send_json({"auth_code": code})
            return

        # Token exchange — no auth required
        if path == "/auth/token":
            form_data = body.decode()
            params = dict(p.split("=") for p in form_data.split("&") if "=" in p)
            code = params.get("code", "")
            if code in state.auth_codes:
                token = "short-lived-test-token"
                state.tokens[token] = state.auth_codes[code]
                self._send_json({
                    "access_token": token,
                    "refresh_token": "test-refresh",
                    "token_type": "Bearer",
                    "expires_in": 1800,
                })
                return
            self._send_json({"error": "invalid_grant"}, 400)
            return

        if not self._check_auth():
            self._send_json({"message": "Unauthorized"}, 401)
            return

        if path.startswith("/api/services/"):
            parts = path.split("/")
            domain = parts[3] if len(parts) > 3 else ""
            service = parts[4] if len(parts) > 4 else ""
            data = json.loads(body) if body else {}
            state.service_calls.append({"domain": domain, "service": service, "data": data})
            self._send_json([])
            return

        self._send_json({"message": "Not found"}, 404)


async def _ws_handler(websocket):
    """WebSocket handler simulating HA WS API."""
    # Send auth_required
    await websocket.send(json.dumps({"type": "auth_required", "ha_version": "2026.3.3"}))

    # Wait for auth
    msg = json.loads(await websocket.recv())
    if msg.get("type") != "auth" or msg.get("access_token") not in state.tokens:
        await websocket.send(json.dumps({"type": "auth_invalid", "message": "Invalid token"}))
        return
    await websocket.send(json.dumps({"type": "auth_ok", "ha_version": "2026.3.3"}))

    # Handle commands
    async for raw in websocket:
        msg = json.loads(raw)
        msg_id = msg.get("id", 1)
        msg_type = msg.get("type", "")

        if msg_type == "get_states":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": state.entities,
            }))

        elif msg_type == "get_config":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": state.config,
            }))

        elif msg_type == "call_service":
            domain = msg.get("domain", "")
            service = msg.get("service", "")
            state.service_calls.append({"domain": domain, "service": service})
            # Simulate state change for light.turn_on
            if domain == "light" and service == "turn_on":
                target = msg.get("target", {})
                eid = target.get("entity_id", "")
                for e in state.entities:
                    if e["entity_id"] == eid:
                        e["state"] = "on"
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": {"context": {}},
            }))

        elif msg_type == "config/area_registry/list":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": state.areas,
            }))

        elif msg_type == "config/area_registry/create":
            new_area = {
                "area_id": f"area-{len(state.areas)+1}",
                "name": msg.get("name", "Unknown"),
                "floor_id": None,
            }
            state.areas.append(new_area)
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": new_area,
            }))

        elif msg_type == "config/device_registry/list":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": state.devices,
            }))

        elif msg_type == "config/device_registry/update":
            device_id = msg.get("device_id")
            area_id = msg.get("area_id")
            for d in state.devices:
                if d["id"] == device_id:
                    d["area_id"] = area_id
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": {},
            }))

        elif msg_type == "config_entries/flow/progress":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": [],
            }))

        elif msg_type == "auth/long_lived_access_token":
            ll_token = "long-lived-test-token"
            state.tokens[ll_token] = "admin"
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": ll_token,
            }))

        elif msg_type == "config/entity_registry/list":
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": True,
                "result": [
                    {"entity_id": e["entity_id"], "area_id": "area-lr"}
                    for e in state.entities
                ],
            }))

        else:
            await websocket.send(json.dumps({
                "id": msg_id, "type": "result", "success": False,
                "error": {"code": "unknown_command", "message": f"Unknown: {msg_type}"},
            }))


class MockHAServer:
    """Manages both HTTP and WebSocket mock servers."""

    def __init__(self, http_port=18123, ws_port=18124):
        self.http_port = http_port
        self.ws_port = ws_port
        self._http_server = None
        self._http_thread = None
        self._ws_thread = None

    def start(self):
        """Start both servers in background threads."""
        global state
        state = MockHAState()

        # HTTP server
        self._http_server = HTTPServer(("127.0.0.1", self.http_port), MockHAHTTPHandler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()

        # WebSocket server — use asyncio.run with serve() context manager
        def run_ws():
            async def serve():
                async with websockets.serve(_ws_handler, "127.0.0.1", self.ws_port):
                    await asyncio.get_running_loop().create_future()  # run forever

            asyncio.run(serve())

        self._ws_thread = threading.Thread(target=run_ws, daemon=True)
        self._ws_thread.start()

    def stop(self):
        """Stop both servers."""
        if self._http_server:
            self._http_server.shutdown()

    @property
    def http_url(self) -> str:
        return f"http://127.0.0.1:{self.http_port}"

    @property
    def ws_url(self) -> str:
        return f"ws://127.0.0.1:{self.ws_port}"
