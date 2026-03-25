"""Example NanoHA Plugin — demonstrates the plugin interface.

To create your own plugin:
1. Create a directory under plugins/ with an __init__.py
2. Define PLUGIN_META with name, version, description
3. Add public functions — they become tools the agent can call
"""

PLUGIN_META = {
    "name": "example_plugin",
    "version": "1.0.0",
    "description": "Example plugin showing how to extend NanoHA",
    "author": "NanoHA",
}


def greet(name: str = "World") -> dict:
    """Say hello — example tool function."""
    return {"success": True, "message": f"Hello, {name}! This is the example plugin."}


def add_numbers(a: float, b: float) -> dict:
    """Add two numbers — example tool with parameters."""
    return {"success": True, "result": a + b}


def get_plugin_info() -> dict:
    """Return plugin metadata."""
    return {"success": True, **PLUGIN_META}
