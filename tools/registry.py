"""
Aios tool registry — whitelist-only tool execution.

Only tools explicitly registered here can be called. No dynamic
discovery of arbitrary modules — safety by design.
"""

import json
import logging
from typing import Callable

log = logging.getLogger("aios.tools")

# Whitelisted tool names — must be registered explicitly
_WHITELIST: set[str] = {
    "think_tool",
    "calculator",
    "file_read", 
    "file_write",
    "list_directory",
    "system_info",
    "run_command",
    "open_application",
    "take_screenshot",
    "get_running_processes",
    "control_window"
}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all whitelisted built-in tools."""
        try:
            from tools.think_tool import run_think
            self._tools["think_tool"] = run_think
        except Exception as e:
            log.warning("Could not register think_tool: %s", e)
        
        # Register system tools
        try:
            from tools.system_tools import SystemTools
            system_tools = SystemTools()
            tool_dict = system_tools.get_tools_dict()
            for name, func in tool_dict.items():
                if name in _WHITELIST:
                    self._tools[name] = func
                    log.info("Registered system tool: %s", name)
        except Exception as e:
            log.warning("Could not register system tools: %s", e)

    def register(self, name: str, fn: Callable) -> None:
        """Register a new tool. Name must be in the whitelist."""
        if name not in _WHITELIST:
            raise ValueError(
                f"Tool '{name}' is not whitelisted. "
                f"Add it to _WHITELIST in tools/registry.py first."
            )
        self._tools[name] = fn
        log.info("tool registered: %s", name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def run(self, name: str, payload: str) -> str:
        """Execute a whitelisted tool with the given payload string."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
        try:
            return self._tools[name](payload)
        except Exception as e:
            log.error("tool '%s' raised: %s", name, e)
            return json.dumps({"status": "error", "error": str(e)})

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())
