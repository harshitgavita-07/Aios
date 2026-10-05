"""Tests for the live core: intent -> plan -> execute -> verify. Pure Python, no GUI, no Node."""
import asyncio
import os

from src import IntentEngine, PlanningEngine, VerificationEngine
from src.execution import PlanExecutor
from src.shared.types import ActionResult, ExecutionPlan, IntentDomain, TaskStatus, TaskStep


def test_intent_classifies_filesystem_and_scores():
    i = IntentEngine().parse("create a file notes.txt in /tmp")
    assert i.domain == IntentDomain.FILESYSTEM
    assert 0 < i.confidence <= 1 and i.required_plugins == ["filesystem"]


def test_intent_flags_risky_requests_for_approval():
    assert IntentEngine().parse("publish the new version to npm").requires_approval


def test_planner_returns_runnable_plan():
    plan = PlanningEngine().create_plan(IntentEngine().parse("create a file notes.txt"))
    assert plan.steps and all(s.id and s.plugin for s in plan.steps)


def test_verifier_rejects_failed_action():
    r = ActionResult(action_id="a", success=False, error="boom")
    v = VerificationEngine(max_retries=0).verify(r, {}, TaskStep("a", "x", "run"))
    assert not v.success and v.confidence == 0.0


def test_verifier_accepts_run_with_exit_code_zero():
    r = ActionResult(action_id="a", success=True, data={"exit_code": 0, "stdout": "ok"})
    v = VerificationEngine(max_retries=0).verify(r, {"exit_code": 0}, TaskStep("a", "x", "run"))
    assert v.checks_performed  # the strategy for "run" actually executed


def _create_step():
    return TaskStep("a", "x", "create")


def test_default_file_check_ignores_false_claim(tmp_path):
    claim = ActionResult(action_id="a", success=True, data={"exists": True, "content": "hello"})
    v = VerificationEngine(max_retries=0).verify(
        claim, {"path": str(tmp_path / "nope.txt"), "content_contains": "hello"}, _create_step())
    assert not v.success and len(v.failures) == 2  # file_exists and content_check both fail


def test_default_file_check_passes_on_real_file(tmp_path):
    f = tmp_path / "ok.txt"; f.write_text("hello world")
    claim = ActionResult(action_id="a", success=True)  # no self-reported data at all
    v = VerificationEngine(max_retries=0).verify(
        claim, {"path": str(f), "content_contains": "hello"}, _create_step())
    assert v.success and v.evidence["file_exists"]["verified_on_disk"] is True


def test_default_content_check_catches_wrong_content(tmp_path):
    f = tmp_path / "ok.txt"; f.write_text("something else")
    v = VerificationEngine(max_retries=0).verify(
        ActionResult(action_id="a", success=True), {"path": str(f), "content_contains": "hello"}, _create_step())
    assert not v.success and any("content_check" in x for x in v.failures)


def test_file_check_fails_closed_without_path():
    claim = ActionResult(action_id="a", success=True, data={"exists": True})
    v = VerificationEngine(max_retries=0).verify(claim, {}, _create_step())
    assert not v.success  # an agent's own claim is never proof


def test_delete_verified_on_disk(tmp_path):
    f = tmp_path / "gone.txt"
    step = TaskStep("a", "x", "delete")
    claim = ActionResult(action_id="a", success=True, data={"missing": True})
    eng = VerificationEngine(max_retries=0)
    f.write_text("still here")
    assert not eng.verify(claim, {"path": str(f)}, step).success  # claim says gone, file exists
    f.unlink()
    assert eng.verify(claim, {"path": str(f)}, step).success


def test_directory_verified_on_disk(tmp_path):
    d = tmp_path / "d"
    step = TaskStep("a", "x", "clone")
    claim = ActionResult(action_id="a", success=True, data={"exists": True})
    eng = VerificationEngine(max_retries=0)
    assert not eng.verify(claim, {"path": str(d)}, step).success
    d.mkdir()
    assert "directory_exists" in eng.verify(claim, {"path": str(d)}, step).evidence


def test_custom_verifier_can_still_override_default(tmp_path):
    eng = VerificationEngine(max_retries=0)
    eng.register_verifier("file_exists", lambda r, e: os.path.isfile(e["path"]))
    eng.register_verifier("content_check", lambda r, e: os.path.isfile(e["path"]))
    claim = ActionResult(action_id="a", success=True, data={"exists": True})
    step = TaskStep("a", "x", "create")
    target = tmp_path / "f.txt"
    assert not eng.verify(claim, {"path": str(target)}, step).success
    target.write_text("hi")
    assert eng.verify(claim, {"path": str(target)}, step).success


class FakeRuntime:
    def __init__(self, fail_ids=()):
        self.fail_ids, self.ran = set(fail_ids), []

    async def execute(self, step):
        self.ran.append(step.id)
        ok = step.id not in self.fail_ids
        return ActionResult(action_id=step.id, success=ok, error=None if ok else "nope")


def run(plan, rt):
    return asyncio.run(PlanExecutor(rt).execute(plan))


def test_executor_runs_in_dependency_order():
    plan = ExecutionPlan(intent_id="i", steps=[TaskStep("b", "b", "run", dependencies=["a"]),
                                                TaskStep("a", "a", "run")])
    rt = FakeRuntime()
    res = run(plan, rt)
    assert rt.ran == ["a", "b"] and all(r.success for r in res)


def test_executor_skips_steps_with_failed_dependency():
    plan = ExecutionPlan(intent_id="i", steps=[TaskStep("a", "a", "run"),
                                                TaskStep("b", "b", "run", dependencies=["a"])])
    rt = FakeRuntime(fail_ids={"a"})
    res = run(plan, rt)
    assert rt.ran == ["a"]  # b never reached the runtime
    assert [r.success for r in res] == [False, False]
    assert plan.steps[1].status == TaskStatus.SKIPPED


def test_executor_emits_events():
    events = []
    plan = ExecutionPlan(intent_id="i", steps=[TaskStep("a", "a", "run")])
    asyncio.run(PlanExecutor(FakeRuntime(), on_event=events.append).execute(plan))
    assert [e.type for e in events] == ["ExecutionStarted", "ExecutionProgress", "ExecutionFinished"]
