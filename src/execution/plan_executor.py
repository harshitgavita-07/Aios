"""
Plan Executor for AIOS.

Walks an ExecutionPlan's steps and dispatches each one to the correct
execution backend via ScrRuntimeAdapter. This is the piece that was
previously missing: app.py used to hardcode a single command instead
of consulting a real plan.

Only plugins with a real, working backend are executed. Everything
else fails loudly with a clear "not implemented" error rather than
faking success -- there is currently exactly one real backend
(SCR Runtime's terminal target, via ScrRuntimeAdapter.run_terminal_command).
Browser/git/docker/etc. plugins are recognized but not yet wired to
any SCR target, and PlanExecutor says so explicitly instead of
pretending otherwise.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from ..adapters import ScrRuntimeAdapter, ScrRuntimeError
from ..shared.types import ActionResult, Event, ExecutionPlan, TaskStatus, TaskStep

log = logging.getLogger("aios.execution.plan_executor")

# Event callback may be sync or async; PlanExecutor supports both so it
# can be driven from a plain script or from a Qt/asyncio-backed app.
EventCallback = Callable[[Event], Optional[Awaitable[None]]]

# Plugins with a real execution backend today. Anything else in a plan
# is a legitimate step the planner produced, but PlanExecutor has
# nothing real to run it against yet.
SUPPORTED_PLUGINS = frozenset({"terminal"})


class PlanExecutionError(RuntimeError):
    """Raised when a plan cannot be executed at all (not per-step failure)."""


class PlanExecutor:
    """
    Executes an ExecutionPlan step by step against real backends.

    A step only ever reports success if a real backend actually ran it
    and returned a real result. Steps whose plugin has no backend yet
    are marked FAILED with a clear, honest error message -- never
    SKIPPED-as-if-fine and never fabricated as successful.
    """

    def __init__(
        self,
        scr_adapter: ScrRuntimeAdapter,
        on_event: Optional[EventCallback] = None,
    ) -> None:
        self._scr = scr_adapter
        self._on_event = on_event

    async def execute(self, plan: ExecutionPlan) -> list[ActionResult]:
        """
        Executes every step in the plan in dependency order and returns
        one ActionResult per step, in the same order as plan.steps.
        """
        await self._emit("ExecutionStarted", {"intent_id": plan.intent_id, "step_count": len(plan.steps)})

        results: list[ActionResult] = []
        completed_ids: set[str] = set()
        failed_ids: set[str] = set()

        for step in self._ordered(plan.steps):
            if any(dep in failed_ids for dep in step.dependencies):
                step.status = TaskStatus.SKIPPED
                result = ActionResult(
                    action_id=step.id,
                    success=False,
                    error=f"Skipped: unmet dependency in {step.dependencies}",
                )
                results.append(result)
                failed_ids.add(step.id)
                await self._emit(
                    "ExecutionProgress",
                    {"step_id": step.id, "status": step.status.value, "description": step.description},
                )
                continue

            result = await self._execute_step(step)
            results.append(result)

            if result.success:
                completed_ids.add(step.id)
            else:
                failed_ids.add(step.id)

            await self._emit(
                "ExecutionProgress",
                {"step_id": step.id, "status": step.status.value, "description": step.description},
            )

        await self._emit(
            "ExecutionFinished",
            {
                "intent_id": plan.intent_id,
                "succeeded": len(completed_ids),
                "failed": len(failed_ids),
                "total": len(plan.steps),
            },
        )
        return results

    async def _execute_step(self, step: TaskStep) -> ActionResult:
        step.status = TaskStatus.RUNNING
        step.started_at = datetime.now()

        if step.plugin not in SUPPORTED_PLUGINS:
            step.status = TaskStatus.FAILED
            step.error = (
                f"Plugin '{step.plugin}' has no execution backend yet. "
                f"Only {sorted(SUPPORTED_PLUGINS)} are currently wired to SCR Runtime."
            )
            step.completed_at = datetime.now()
            log.warning("Step %s not executed: %s", step.id, step.error)
            return ActionResult(action_id=step.id, success=False, error=step.error)

        if step.plugin == "terminal":
            return await self._execute_terminal_step(step)

        # Unreachable given SUPPORTED_PLUGINS, but keeps the branch honest
        # rather than silently falling through.
        raise PlanExecutionError(f"No dispatch implemented for plugin '{step.plugin}'")

    async def _execute_terminal_step(self, step: TaskStep) -> ActionResult:
        command = step.parameters.get("command")
        if not command:
            step.status = TaskStatus.FAILED
            step.error = "Terminal step has no 'command' parameter"
            step.completed_at = datetime.now()
            return ActionResult(action_id=step.id, success=False, error=step.error)

        try:
            outcome: dict[str, Any] = await self._scr.run_terminal_command(command)
        except ScrRuntimeError as exc:
            step.status = TaskStatus.FAILED
            step.error = str(exc)
            step.completed_at = datetime.now()
            log.error("SCR Runtime failed to execute step %s: %s", step.id, exc)
            return ActionResult(action_id=step.id, success=False, error=step.error)

        success = outcome.get("exitCode") == 0
        step.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        step.result = outcome
        step.error = None if success else f"Command exited with code {outcome.get('exitCode')}"
        step.completed_at = datetime.now()

        return ActionResult(
            action_id=step.id,
            success=success,
            data=outcome,
            error=step.error,
            duration_ms=int(outcome.get("durationMs", 0)),
        )

    @staticmethod
    def _ordered(steps: list[TaskStep]) -> list[TaskStep]:
        """
        Returns steps respecting declared dependencies where possible.

        Today's PlanningEngine only ever produces plans with a single
        step and no cross-step dependencies, so this is a stable
        topological sort that degrades to "plan order" for that case,
        while still being correct once multi-step plans exist.
        """
        by_id = {step.id: step for step in steps}
        visited: set[str] = set()
        ordered: list[TaskStep] = []

        def visit(step: TaskStep) -> None:
            if step.id in visited:
                return
            visited.add(step.id)
            for dep_id in step.dependencies:
                dep = by_id.get(dep_id)
                if dep is not None:
                    visit(dep)
            ordered.append(step)

        for step in steps:
            visit(step)

        return ordered

    async def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._on_event is None:
            return
        event = Event(type=event_type, source="plan_executor", payload=payload)
        maybe_awaitable = self._on_event(event)
        if maybe_awaitable is not None:
            await maybe_awaitable
