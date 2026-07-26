"""
Plan Executor for AIOS.

Walks an ExecutionPlan's steps in dependency order and delegates each
one to RuntimeAdapter -- the single execution boundary. PlanExecutor
itself no longer knows anything about plugins, backends, or SCR
Runtime: it only sequences steps, tracks dependency-driven skips, and
turns each step into an Event for observability.

(Refactor note: this used to contain a per-plugin dispatch --
_execute_step/_execute_terminal_step and a SUPPORTED_PLUGINS set --
which duplicated logic that now lives in RuntimeAdapter. There were
never any BrowserPlugin/TerminalPlugin/etc. classes or switch
statements in this codebase to remove; the only thing to simplify was
that one small if-branch.)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from ..adapters import RuntimeAdapter
from ..shared.types import ActionResult, Event, ExecutionPlan, TaskStatus, TaskStep

log = logging.getLogger("aios.execution.plan_executor")

# Event callback may be sync or async; PlanExecutor supports both so it
# can be driven from a plain script or from a Qt/asyncio-backed app.
EventCallback = Callable[[Event], Optional[Awaitable[None]]]


class PlanExecutionError(RuntimeError):
    """Raised when a plan cannot be executed at all (not per-step failure)."""


class PlanExecutor:
    """
    Executes an ExecutionPlan step by step through RuntimeAdapter.

    A step only ever reports success if RuntimeAdapter actually ran it
    through SCR Runtime and got a real result back. RuntimeAdapter is
    solely responsible for deciding whether a plugin is supported and
    for translating steps/results -- PlanExecutor just sequences and
    observes.
    """

    def __init__(
        self,
        runtime_adapter: RuntimeAdapter,
        on_event: Optional[EventCallback] = None,
    ) -> None:
        self._runtime = runtime_adapter
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

            step.status = TaskStatus.RUNNING
            step.started_at = datetime.now()
            log.info("Dispatching step id=%s plugin=%s action=%s", step.id, step.plugin, step.action)

            result = await self._runtime.execute(step)
            step.completed_at = datetime.now()
            results.append(result)

            if result.success:
                completed_ids.add(step.id)
            else:
                failed_ids.add(step.id)
                log.warning("Step %s did not succeed: %s", step.id, result.error)

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
