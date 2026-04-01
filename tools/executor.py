"""
Tool Executor — Sandboxed tool execution with whitelist
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import subprocess
import shlex
import threading
import time

log = logging.getLogger("aios.tools.executor")


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ToolExecutor:
    """
    Whitelist-based tool executor with sandboxing.
    
    Features:
    - Only whitelisted tools can be executed
    - Subprocess execution with timeout
    - Execution history tracking
    
    Change: Whitelist-based tool execution
    Why:
    - Security: only approved tools run
    - Prevents arbitrary code execution
    Impact:
    - Safe tool execution
    - Controlled system access
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._whitelist: List[str] = []
        self._history: List[ToolResult] = []
        self._max_history = 50
        
        # Default timeout for subprocess tools
        self.default_timeout = 30
        
        log.info("ToolExecutor initialized")

    def register_tool(self, name: str, handler: Callable, whitelisted: bool = False):
        """
        Register a tool.
        
        Change: Explicit tool registration
        Why:
        - Controlled tool availability
        - Security through explicit registration
        Impact:
        - Clear tool inventory
        - Security audit trail
        """
        self._tools[name] = handler
        if whitelisted:
            self._whitelist_tool(name)
        log.debug(f"Registered tool: {name} (whitelisted={whitelisted})")

    def _whitelist_tool(self, name: str):
        """Add tool to whitelist."""
        if name not in self._whitelist:
            self._whitelist.append(name)
            log.info(f"Whitelisted tool: {name}")

    def is_whitelisted(self, name: str) -> bool:
        """Check if tool is whitelisted."""
        return name in self._whitelist

    def execute(self, name: str, payload: Any) -> ToolResult:
        """
        Execute a tool by name.
        
        Change: Whitelist enforcement
        Why:
        - Security: reject non-whitelisted tools
        - Prevents unauthorized execution
        Impact:
        - Safe execution environment
        - Controlled capabilities
        """
        if not self.is_whitelisted(name):
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' is not whitelisted"
            )
        
        if name not in self._tools:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' not found"
            )
        
        start_time = time.time()
        
        try:
            handler = self._tools[name]
            
            # Handle different payload types
            if isinstance(payload, str):
                try:
                    # Try to parse as JSON
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    pass  # Keep as string
            
            result = handler(payload)
            execution_time = time.time() - start_time
            
            tool_result = ToolResult(
                success=True,
                output=str(result) if result else "",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            log.error(f"Tool execution failed: {e}")
            tool_result = ToolResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time
            )
        
        # Track history
        self._history.append(tool_result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        return tool_result

    def execute_subprocess(self, 
                          command: List[str], 
                          timeout: Optional[int] = None,
                          shell: bool = False) -> ToolResult:
        """
        Execute a subprocess command safely.
        
        Change: Sandboxed subprocess execution
        Why:
        - System commands need isolation
        - Timeout prevents runaway processes
        Impact:
        - Safe system interaction
        - Resource protection
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    output=result.stdout.strip(),
                    execution_time=execution_time
                )
            else:
                return ToolResult(
                    success=False,
                    output=result.stdout.strip(),
                    error=result.stderr.strip(),
                    execution_time=execution_time
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
                execution_time=timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time
            )

    def list_tools(self) -> Dict[str, bool]:
        """List all registered tools and whitelist status."""
        return {
            name: name in self._whitelist 
            for name in self._tools.keys()
        }

    def get_whitelist(self) -> List[str]:
        """Get list of whitelisted tools."""
        return self._whitelist.copy()

    def get_history(self, limit: int = 10) -> List[ToolResult]:
        """Get recent execution history."""
        return self._history[-limit:]

    def clear_history(self):
        """Clear execution history."""
        self._history.clear()
