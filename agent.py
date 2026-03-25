#!/usr/bin/env python3
"""NanoHA Agent — minimal agent loop using Gemini with tool calling."""

import json
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nanoha")

# Config
GEMINI_API_KEY = os.environ.get("LLM_API_KEY", "")
GEMINI_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Ensure tools are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools.ha_client
tools.ha_client.HA_URL = os.environ.get("HA_URL", "http://localhost:8123")

# Import all tool modules
from tools import ha_setup, ha_control, ha_devices, ha_info, ha_automation, ha_monitor, ha_energy, ha_scenes, ha_memory, ha_users

# Tool registry: name -> callable
TOOLS = {
    "list_entities": ha_control.list_entities,
    "get_entity_state": ha_control.get_entity_state,
    "call_service": ha_control.call_service,
    "list_devices": ha_devices.list_devices,
    "discover_devices": ha_devices.discover_devices,
    "list_areas": ha_devices.list_areas,
    "create_area": ha_devices.create_area,
    "start_config_flow": ha_devices.start_config_flow,
    "continue_config_flow": ha_devices.continue_config_flow,
    "assign_device_to_area": ha_devices.assign_device_to_area,
    "get_history": ha_info.get_history,
    "health_check": ha_info.health_check,
    "get_config": ha_info.get_config,
    "list_automations": ha_automation.list_automations,
    "trigger_automation": ha_automation.trigger_automation,
    "check_anomalies": ha_monitor.check_anomalies,
    "get_energy_sensors": ha_energy.get_energy_sensors,
    "get_energy_summary": ha_energy.get_energy_summary,
    "suggest_savings": ha_energy.suggest_savings,
    "suggest_automations": ha_scenes.suggest_automations,
    "who_is_home": ha_users.who_is_home,
    "remember": ha_memory.remember,
    "recall": ha_memory.recall,
    "check_docker": ha_setup.check_docker,
    "deploy_service": ha_setup.deploy_service,
    "get_setup_status": ha_setup.get_setup_status,
}

# Gemini tool declarations
TOOL_DECLARATIONS = [
    {"name": "list_entities", "description": "List all home entities, filter by domain or area", "parameters": {"type": "object", "properties": {"domain": {"type": "string"}, "area": {"type": "string"}}}},
    {"name": "get_entity_state", "description": "Get state of a specific entity", "parameters": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}},
    {"name": "call_service", "description": "Control a device (turn_on, turn_off, etc.)", "parameters": {"type": "object", "properties": {"domain": {"type": "string"}, "service": {"type": "string"}, "entity_id": {"type": "string"}, "data": {"type": "object"}}, "required": ["domain", "service"]}},
    {"name": "list_devices", "description": "List registered devices", "parameters": {"type": "object", "properties": {"area": {"type": "string"}}}},
    {"name": "discover_devices", "description": "Scan for new devices on the network", "parameters": {"type": "object", "properties": {}}},
    {"name": "list_areas", "description": "List all rooms/areas", "parameters": {"type": "object", "properties": {}}},
    {"name": "create_area", "description": "Create a new room", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "get_config", "description": "Get HA configuration", "parameters": {"type": "object", "properties": {}}},
    {"name": "health_check", "description": "Check all service health", "parameters": {"type": "object", "properties": {}}},
    {"name": "list_automations", "description": "List all automations", "parameters": {"type": "object", "properties": {}}},
    {"name": "check_anomalies", "description": "Check for open doors, motion at night, low battery", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_energy_summary", "description": "Get energy consumption summary", "parameters": {"type": "object", "properties": {}}},
    {"name": "suggest_automations", "description": "Suggest automations based on current state", "parameters": {"type": "object", "properties": {}}},
    {"name": "who_is_home", "description": "Check who is home", "parameters": {"type": "object", "properties": {}}},
    {"name": "remember", "description": "Store something in memory", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {}}, "required": ["key", "value"]}},
    {"name": "recall", "description": "Retrieve from memory", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
]

SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "config", "nanobot", "system_prompt.md")).read()


def call_gemini(messages: list, tools_enabled: bool = True) -> dict:
    """Call Gemini API with messages and optional tool declarations."""
    payload = {
        "contents": messages,
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    }
    if tools_enabled:
        payload["tools"] = [{"functionDeclarations": TOOL_DECLARATIONS}]

    resp = httpx.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=60,
    )
    if resp.status_code != 200:
        return {"error": f"Gemini API error {resp.status_code}: {resp.text[:200]}"}
    return resp.json()


def execute_tool_call(name: str, args: dict) -> str:
    """Execute a tool and return the result as a string."""
    fn = TOOLS.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**args)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def send_message(user_text: str, conversation: list = None) -> str:
    """Send a message to the agent and get a response. Handles tool calls."""
    if conversation is None:
        conversation = []

    conversation.append({"role": "user", "parts": [{"text": user_text}]})

    # Agent loop — up to 10 tool call rounds
    for _ in range(10):
        response = call_gemini(conversation)
        if "error" in response:
            return f"Error: {response['error']}"

        candidates = response.get("candidates", [])
        if not candidates:
            return "No response from agent."

        parts = candidates[0].get("content", {}).get("parts", [])
        conversation.append({"role": "model", "parts": parts})

        # Check for tool calls
        tool_calls = [p for p in parts if "functionCall" in p]
        if not tool_calls:
            # No tool calls — extract text response
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            return " ".join(text_parts).strip() or "Done."

        # Execute tool calls and add results
        tool_results = []
        for tc in tool_calls:
            fc = tc["functionCall"]
            log.info("Tool call: %s(%s)", fc["name"], json.dumps(fc.get("args", {}))[:100])
            result = execute_tool_call(fc["name"], fc.get("args", {}))
            log.info("Tool result: %s", result[:200])
            tool_results.append({
                "functionResponse": {
                    "name": fc["name"],
                    "response": {"result": result},
                }
            })
        conversation.append({"role": "user", "parts": tool_results})

    return "I made several tool calls but couldn't complete the task. Try a simpler question."


def chat():
    """Interactive chat loop."""
    print("NanoHA Agent (Gemini 2.5 Flash)")
    print("Type 'quit' to exit.")
    print()

    conversation = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        response = send_message(user_input, conversation)
        print(f"Agent: {response}")
        print()


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: LLM_API_KEY not set. Run: export LLM_API_KEY=your-gemini-key")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--message":
        msg = " ".join(sys.argv[2:])
        print(send_message(msg))
    else:
        chat()
