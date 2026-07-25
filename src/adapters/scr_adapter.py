"""
SCR Runtime adapter.

This is the ONLY place in AIOS that knows an SCR Runtime process exists.
It is deliberately thin: it starts the Node bridge (scr_bridge.mjs),
speaks newline-delimited JSON to it over stdio, and returns plain dicts.

It never executes a shell command, spawns a browser, or touches the
filesystem itself -- all of that happens inside SCR Runtime (via the
bridge). If SCR Runtime doesn't support a capability, this adapter must
not fake one; the caller gets a clear error instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("aios.adapters.scr")

_BRIDGE_PATH = Path(__file__).parent / "scr_bridge.mjs"
_STARTUP_TIMEOUT_S = 15.0
_COMMAND_TIMEOUT_S = 30.0
_SHUTDOWN_TIMEOUT_S = 5.0


class ScrRuntimeError(RuntimeError):
    """Raised when SCR Runtime is unavailable, fails to start, or disconnects."""


class ScrRuntimeAdapter:
    """
    Manages a single SCR Runtime bridge subprocess for the lifetime of
    the adapter: start() -> run_terminal_command() (any number of times)
    -> shutdown().
    """

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stdout_lines: Optional[asyncio.StreamReader] = None
        self.runtime_status: Optional[str] = None
        self.terminal_status: Optional[str] = None

    async def start(self) -> None:
        """
        Launches the Node bridge and waits for its readiness handshake.

        Raises:
            ScrRuntimeError: if Node is missing, the bridge script is
                missing, SCR Runtime fails to initialize, or startup
                times out.
        """
        node_path = shutil.which("node")
        if node_path is None:
            raise ScrRuntimeError(
                "Node.js was not found on PATH. SCR Runtime requires Node >= 22. "
                "Install Node and ensure `node` is available, then retry."
            )

        if not _BRIDGE_PATH.exists():
            raise ScrRuntimeError(f"SCR bridge script not found at {_BRIDGE_PATH}")

        try:
            self._process = await asyncio.create_subprocess_exec(
                node_path,
                str(_BRIDGE_PATH),
                cwd=str(_BRIDGE_PATH.parent.parent.parent),  # repo root, where node_modules lives
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise ScrRuntimeError(f"Failed to launch SCR bridge process: {exc}") from exc

        try:
            message = await asyncio.wait_for(self._read_message(), timeout=_STARTUP_TIMEOUT_S)
        except asyncio.TimeoutError as exc:
            await self._kill()
            raise ScrRuntimeError(
                "SCR Runtime did not respond within the startup timeout. "
                "Is @scr-runtime/runtime built (`npm run build` in the SCR checkout) "
                "and linked (`npm install` in AIOS)?"
            ) from exc

        if message is None:
            stderr = await self._drain_stderr()
            await self._kill()
            raise ScrRuntimeError(
                "SCR bridge exited before signaling readiness. "
                f"Stderr: {stderr or '(empty)'}"
            )

        if message.get("type") == "error":
            await self._kill()
            raise ScrRuntimeError(
                f"SCR Runtime failed to initialize during '{message.get('phase', 'startup')}': "
                f"{message.get('message', 'unknown error')}"
            )

        if message.get("type") != "ready":
            await self._kill()
            raise ScrRuntimeError(f"Unexpected message from SCR bridge on startup: {message}")

        self.runtime_status = message.get("runtimeStatus")
        self.terminal_status = message.get("terminalStatus")
        log.info(
            "SCR Runtime ready (runtime=%s, terminal=%s)",
            self.runtime_status,
            self.terminal_status,
        )

    async def run_terminal_command(self, command: str) -> dict[str, Any]:
        """
        Executes a real terminal command through SCR Runtime's terminal
        target and returns its result (stdout/stderr/exitCode/durationMs).

        Raises:
            ScrRuntimeError: if the runtime hasn't been started, has
                disconnected, or SCR Runtime reports an execution error.
        """
        if self._process is None or self._process.returncode is not None:
            raise ScrRuntimeError("SCR Runtime is not running -- call start() first")

        await self._send({"type": "run", "command": command})

        try:
            message = await asyncio.wait_for(self._read_message(), timeout=_COMMAND_TIMEOUT_S)
        except asyncio.TimeoutError as exc:
            raise ScrRuntimeError(f"Timed out waiting for SCR Runtime to run: {command}") from exc

        if message is None:
            stderr = await self._drain_stderr()
            raise ScrRuntimeError(
                f"SCR Runtime disconnected while running '{command}'. Stderr: {stderr or '(empty)'}"
            )

        if message.get("type") == "error":
            raise ScrRuntimeError(
                f"SCR Runtime reported an error executing '{command}': "
                f"{message.get('message', 'unknown error')}"
            )

        if message.get("type") != "result":
            raise ScrRuntimeError(f"Unexpected message from SCR bridge: {message}")

        return message

    async def shutdown(self) -> None:
        """Asks SCR Runtime to stop cleanly, then tears down the process."""
        if self._process is None or self._process.returncode is not None:
            return

        try:
            await self._send({"type": "shutdown"})
            await asyncio.wait_for(self._process.wait(), timeout=_SHUTDOWN_TIMEOUT_S)
            log.info("SCR Runtime shut down cleanly")
        except (asyncio.TimeoutError, BrokenPipeError, ConnectionResetError):
            log.warning("SCR Runtime did not shut down cleanly -- terminating")
            await self._kill()

    # -- internal helpers -------------------------------------------------

    async def _send(self, message: dict[str, Any]) -> None:
        assert self._process is not None and self._process.stdin is not None
        line = (json.dumps(message) + "\n").encode("utf-8")
        self._process.stdin.write(line)
        await self._process.stdin.drain()

    async def _read_message(self) -> Optional[dict[str, Any]]:
        assert self._process is not None and self._process.stdout is not None
        raw = await self._process.stdout.readline()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ScrRuntimeError(f"Malformed message from SCR bridge: {raw!r}") from exc

    async def _drain_stderr(self) -> str:
        if self._process is None or self._process.stderr is None:
            return ""
        data = await self._process.stderr.read()
        return data.decode("utf-8", errors="replace").strip()

    async def _kill(self) -> None:
        if self._process is None:
            return
        if self._process.returncode is None:
            self._process.kill()
            await self._process.wait()
