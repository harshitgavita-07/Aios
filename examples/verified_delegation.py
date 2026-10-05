"""Verified delegation, in about 40 lines. No GUI, no model, no network.

An agent says "done". AIOS does not take its word for it: it checks the real world.
Run from the repo root:  python examples/verified_delegation.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import IntentEngine, PlanningEngine, VerificationEngine
from src.shared.types import ActionResult, TaskStep


def check_file_on_disk(result: ActionResult, expected: dict) -> bool:
    """Independent evidence: look at the disk, ignore what the agent claims."""
    return os.path.isfile(expected["path"])


def check_content_on_disk(result: ActionResult, expected: dict) -> bool:
    try:
        text = open(expected["path"]).read()
    except OSError:
        return False
    return expected.get("content_contains", "") in text


def main() -> None:
    goal = "create a file notes.txt and run the tests"
    intent = IntentEngine().parse(goal)
    plan = PlanningEngine().create_plan(intent)
    print(f"goal: {goal!r}\n  domain={intent.domain.value} steps={len(plan.steps)} risk={plan.risk_level.value}")

    verifier = VerificationEngine(max_retries=0)
    verifier.register_verifier("file_exists", check_file_on_disk)
    verifier.register_verifier("content_check", check_content_on_disk)
    step = TaskStep(id="s1", description="create notes.txt", action="create", plugin="filesystem")

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "notes.txt")
        # The agent claims success, but never wrote the file.
        claim = ActionResult(action_id="s1", success=True, data={"exists": True})
        v = verifier.verify(claim, {"path": path}, step)
        print(f"\nclaim: 'file created'  ->  verified={v.success}  failures={v.failures}")

        open(path, "w").write("hello")
        v = verifier.verify(claim, {"path": path, "content_contains": "hello"}, step)
        print(f"after really creating it ->  verified={v.success}")


if __name__ == "__main__":
    main()
