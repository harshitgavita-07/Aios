"""
AIOS -- Application Bootstrap

This replaces the pre-PR-#22 entry point, which imported
`runtime.aios_runtime` and a `core/`/`tools/`/`ui/`/`gstack/` layer that
no longer exists in this repository (removed in 5b9a380, "Feature/aios
v1 beta (#22)"). See repository history for details -- that code is
kept only as historical reference and is not restored here.

Current architecture:

    AIOS (this process)                     SCR Runtime (Node subprocess)
    ----------------------------------       ------------------------------
    IntentEngine    -> parses a goal
    PlanningEngine  -> builds an ExecutionPlan
    VerificationEngine -> checks the result   TerminalTarget.run(command)
                                               (real child_process execution)

    AIOS coordinates. SCR Runtime executes. Nothing here spawns a shell,
    a browser, or touches the filesystem directly -- that all happens
    inside SCR Runtime, via src/adapters/scr_adapter.py.

This is intentionally the smallest possible vertical slice: it proves
Intent -> Planning -> SCR Runtime -> Execution -> Verification -> Result
end to end. No workspace, UI, memory, or storage layer exists yet --
those are separate, later milestones.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from src import IntentEngine, PlanningEngine, VerificationEngine
from src.shared.types import ActionResult
from src.adapters import ScrRuntimeAdapter, ScrRuntimeError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("aios")


def _working_directory_command() -> str:
    """The real shell command for 'print the working directory', per OS."""
    return "cd" if sys.platform == "win32" else "pwd"


async def main() -> int:
    log.info("=" * 60)
    log.info("AIOS -- orchestrator + SCR Runtime vertical slice")
    log.info("=" * 60)

    # -- Orchestration layer: AIOS decides what to do --------------------
    intent_engine = IntentEngine()
    planning_engine = PlanningEngine()
    verification_engine = VerificationEngine()

    intent = intent_engine.parse(
        "run a terminal command to show the current working directory"
    )
    plan = planning_engine.create_plan(intent)
    log.info(
        "Intent parsed: domain=%s confidence=%.2f -- plan has %d step(s)",
        intent.domain.value,
        intent.confidence,
        len(plan.steps),
    )

    # -- Execution layer: SCR Runtime does the real work -----------------
    scr = ScrRuntimeAdapter()
    exit_code = 0
    try:
        await scr.start()

        command = _working_directory_command()
        outcome = await scr.run_terminal_command(command)
        log.info(
            "SCR Runtime executed '%s' -> exit=%s (%dms)",
            outcome["command"],
            outcome["exitCode"],
            outcome["durationMs"],
        )

        # -- Verification layer: AIOS checks the real result -------------
        action_result = ActionResult(
            action_id=plan.steps[0].id if plan.steps else "adhoc-terminal-check",
            success=outcome["exitCode"] == 0,
            data=outcome,
            duration_ms=outcome["durationMs"],
        )
        verification = verification_engine.verify(
            action_result,
            expected={"exitCode": 0},
        )

        print(f"stdout: {outcome['stdout'].strip()}")
        print(f"stderr: {outcome['stderr'].strip()}")
        print(f"exit code: {outcome['exitCode']}")
        print(f"verified: {verification.success} (confidence={verification.confidence:.2f})")

        if not verification.success:
            exit_code = 1

    except ScrRuntimeError as exc:
        log.error("SCR Runtime unavailable: %s", exc)
        exit_code = 1
    finally:
        await scr.shutdown()

    log.info("AIOS shutdown complete")
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
