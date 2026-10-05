"""Verified delegation, in about 30 lines. No GUI, no model, no network.

An agent says "done". AIOS does not take its word for it: the default file checks
look at the real disk and ignore what the agent reported.
Run from the repo root:  python examples/verified_delegation.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import IntentEngine, PlanningEngine, VerificationEngine
from src.shared.types import ActionResult, TaskStep


def main() -> None:
    goal = "create a file notes.txt and run the tests"
    intent = IntentEngine().parse(goal)
    plan = PlanningEngine().create_plan(intent)
    print(f"goal: {goal!r}\n  domain={intent.domain.value} steps={len(plan.steps)} risk={plan.risk_level.value}")

    verifier = VerificationEngine(max_retries=0)
    step = TaskStep(id="s1", description="create notes.txt", action="create", plugin="filesystem")

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "notes.txt")
        # The agent claims success, but never wrote the file.
        claim = ActionResult(action_id="s1", success=True, data={"exists": True, "content": "hello"})
        v = verifier.verify(claim, {"path": path, "content_contains": "hello"}, step)
        print(f"\nclaim: 'file created'  ->  verified={v.success}  failures={v.failures}")

        with open(path, "w") as f:
            f.write("hello")
        v = verifier.verify(claim, {"path": path, "content_contains": "hello"}, step)
        print(f"after really creating it ->  verified={v.success}")


if __name__ == "__main__":
    main()
