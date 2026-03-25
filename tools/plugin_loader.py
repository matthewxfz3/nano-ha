"""NanoHA Plugin System — discover, load, and manage plugins."""

import importlib
import importlib.util
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

PLUGIN_DIR = os.environ.get(
    "NANOHA_PLUGIN_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins"),
)


class Plugin:
    """Represents a loaded plugin."""

    def __init__(self, name: str, module, metadata: dict):
        self.name = name
        self.module = module
        self.metadata = metadata
        self.tools = {}

        # Discover tool functions (any callable with 'tool' in annotations or all public functions)
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            attr = getattr(module, attr_name)
            if callable(attr) and not isinstance(attr, type):
                self.tools[attr_name] = attr


def discover_plugins() -> dict:
    """Scan the plugins directory and return available plugins."""
    if not os.path.isdir(PLUGIN_DIR):
        return {"success": True, "count": 0, "plugins": []}

    plugins = []
    for entry in sorted(os.listdir(PLUGIN_DIR)):
        plugin_path = os.path.join(PLUGIN_DIR, entry)
        init_path = os.path.join(plugin_path, "__init__.py")
        if os.path.isdir(plugin_path) and os.path.exists(init_path):
            # Read metadata from PLUGIN_META if defined
            plugins.append({
                "name": entry,
                "path": plugin_path,
                "has_init": True,
            })

    return {"success": True, "count": len(plugins), "plugins": plugins}


def load_plugin(name: str) -> dict:
    """Load a plugin by name from the plugins directory."""
    plugin_path = os.path.join(PLUGIN_DIR, name)
    init_path = os.path.join(plugin_path, "__init__.py")

    if not os.path.exists(init_path):
        return {"success": False, "error": f"Plugin '{name}' not found at {plugin_path}"}

    try:
        spec = importlib.util.spec_from_file_location(f"plugins.{name}", init_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        metadata = getattr(module, "PLUGIN_META", {"name": name, "version": "0.0.0"})
        plugin = Plugin(name=name, module=module, metadata=metadata)

        log.info("Loaded plugin '%s' with %d tools", name, len(plugin.tools))
        return {
            "success": True,
            "name": name,
            "metadata": metadata,
            "tools": list(plugin.tools.keys()),
        }
    except Exception as e:
        log.error("Failed to load plugin '%s': %s", name, e)
        return {"success": False, "error": f"Failed to load plugin '{name}': {e}"}


def load_all_plugins() -> dict:
    """Discover and load all plugins."""
    discovered = discover_plugins()
    if not discovered.get("success"):
        return discovered

    loaded = []
    errors = []
    for p in discovered["plugins"]:
        result = load_plugin(p["name"])
        if result.get("success"):
            loaded.append(result)
        else:
            errors.append(result)

    return {
        "success": True,
        "loaded": len(loaded),
        "errors": len(errors),
        "plugins": loaded,
        "failed": errors,
    }
