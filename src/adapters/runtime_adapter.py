"""
RuntimeAdapter -- the single execution-facing boundary between AIOS
orchestration and @scr-runtime/runtime.

This is deliberately the only class PlanExecutor talks to. It has one
public method (execute) plus lifecycle (start/shutdown) and a
capability query; everything else is private.

RuntimeAdapter never contains planning or verification logic -- it
only translates a TaskStep into whatever ScrRuntimeAdapter/SCR Runtime
actually supports, and translates the raw result back into an
ActionResult. It does not decide *what* to run (PlanningEngine's job)
and does not judge *whether* the result was good enough
(VerificationEngine's job).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .scr_adapter import ScrRuntimeAdapter, ScrRuntimeError
from ..shared.types import ActionResult, TaskStatus, TaskStep

log = logging.getLogger("aios.adapters.runtime")


class RuntimeAdapter:
    """
    Delegates all execution to @scr-runtime/runtime via ScrRuntimeAdapter.

    Capabilities reflect what SCR Runtime's Node bridge actually wires
    up today -- not what the npm package could theoretically support.
    Right now that's exactly one thing: real terminal command execution
    through SCR's TerminalTarget. Browser/filesystem/git/clipboard/OCR/
    keyboard/mouse/window-management/screenshots/processes are real SCR
    Runtime concepts in principle, but none of them are wired through
    scr_bridge.mjs yet, so they are correctly reported as unavailable
    rather than invented.
    """

    # Plugin name (TaskStep.plugin) -> whether scr_bridge.mjs currently
    # wires that capability through to a real SCR Runtime target.
    _CAPABILITIES: frozenset[str] = frozenset({"terminal"})

    def __init__(self, scr: ScrRuntimeAdapter) -> None:
        self._scr = scr

    # -- lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        """Starts the one underlying SCR Runtime process. Idempotent per process."""
        await self._scr.start()

    async def shutdown(self) -> None:
        """Stops the underlying SCR Runtime process cleanly."""
        await self._scr.shutdown()

    # -- capability introspection ---------------------------------------------

    def capabilities(self) -> frozenset[str]:
        """Returns the set of plugin names RuntimeAdapter can currently execute."""
        return self._CAPABILITIES

    def supports(self, plugin: str) -> bool:
        return plugin in self._CAPABILITIES

    # -- the single public execution API --------------------------------------

    async def execute(self, step: TaskStep) -> ActionResult:
        """
        Executes one TaskStep through SCR Runtime and returns a real
        ActionResult. Never fabricates success: an unsupported plugin,
        a malformed step, or a runtime-level failure all come back as
        success=False with a clear error, never a silent skip.
        """
        log.info(
            "Executing step id=%s plugin=%s action=%s",
            step.id, step.plugin, step.action,
        )
        started = time.monotonic()

        if not self.supports(step.plugin):
            return self._fail(
                step,
                f"Plugin '{step.plugin}' has no execution backend yet. "
                f"Currently supported: {sorted(self._CAPABILITIES)}.",
            )

        try:
            request = self._to_runtime_request(step)
        except ValueError as exc:
            return self._fail(step, str(exc))

        try:
            response = await self._dispatch(step.plugin, request)
        except ScrRuntimeError as exc:
            log.error(
                "Runtime execution failed id=%s plugin=%s action=%s error=%s",
                step.id, step.plugin, step.action, exc,
            )
            return self._fail(step, str(exc))

        duration_ms = int((time.monotonic() - started) * 1000)
        return self._to_action_result(step, response, duration_ms)

    # -- request/response translation (private) -------------------------------

    async def _dispatch(self, plugin: str, request: dict[str, Any]) -> dict[str, Any]:
        """Routes a translated request to the one real backend that exists today."""
        if plugin == "terminal":
            return await self._scr.run_terminal_command(request["command"])
        # Unreachable: supports() already filtered to _CAPABILITIES.
        raise ScrRuntimeError(f"No dispatch path for plugin '{plugin}'")

    @staticmethod
    def _to_runtime_request(step: TaskStep) -> dict[str, Any]:
        """
        Translates a TaskStep's parameters into whatever shape the
        target backend needs. For 'terminal' that's just the literal
        command string PlanningEngine put in parameters['command']
        (see PlanningEngine's known NL->command gap, documented in
        app.py) -- RuntimeAdapter does not attempt to reinterpret it.
        """
        if step.plugin == "terminal":
            command = step.parameters.get("command")
            if not command:
                raise ValueError(f"Step {step.id} (terminal) has no 'command' parameter")
            return {"command": command}
        raise ValueError(f"No request translation for plugin '{step.plugin}'")

    @staticmethod
    def _to_action_result(step: TaskStep, response: dict[str, Any], duration_ms: int) -> ActionResult:
        success = response.get("exitCode") == 0
        step.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        step.result = response
        step.error = None if success else f"Command exited with code {response.get('exitCode')}"
        return ActionResult(
            action_id=step.id,
            success=success,
            data=response,
            error=step.error,
            duration_ms=int(response.get("durationMs", duration_ms)),
        )

    @staticmethod
    def _fail(step: TaskStep, message: str) -> ActionResult:
        step.status = TaskStatus.FAILED
        step.error = message
        return ActionResult(action_id=step.id, success=False, error=message)
