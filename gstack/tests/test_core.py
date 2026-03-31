"""
tests/test_core.py — unit tests for router, skills, memory.
No Ollama required — tests the pure-Python logic only.
"""

import sys, os, json, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest


class TestRouter(unittest.TestCase):
    def setUp(self):
        from core.router import route, route_explicit
        self.route = route
        self.route_explicit = route_explicit

    def test_natural_language_build(self):
        self.assertEqual(self.route("build a NLP library"), "plan-ceo-review")

    def test_natural_language_fix(self):
        result = self.route("fix the authentication bug")
        self.assertEqual(result, "investigate")

    def test_natural_language_deploy(self):
        result = self.route("deploy to production")
        self.assertEqual(result, "ship")

    def test_natural_language_test(self):
        result = self.route("test the login flow")
        self.assertEqual(result, "qa")

    def test_natural_language_review(self):
        result = self.route("review the pull request")
        self.assertEqual(result, "review")

    def test_explicit_command_with_slash(self):
        result = self.route_explicit("/review")
        self.assertEqual(result, "review")

    def test_explicit_command_without_slash(self):
        result = self.route_explicit("plan-ceo-review")
        self.assertEqual(result, "plan-ceo-review")

    def test_explicit_command_unknown(self):
        result = self.route_explicit("/nonexistent")
        self.assertIsNone(result)

    def test_office_hours_routing(self):
        result = self.route("I'm not sure what to build, help me think")
        self.assertEqual(result, "office-hours")


class TestSkills(unittest.TestCase):
    def setUp(self):
        from core.skills import get_skill, list_skills
        self.get_skill = get_skill
        self.list_skills = list_skills

    def test_get_known_skill(self):
        skill = self.get_skill("plan-ceo-review")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "plan-ceo-review")
        self.assertIn("CEO", skill.role)
        self.assertTrue(len(skill.system_prompt) > 100)

    def test_get_skill_with_slash(self):
        skill = self.get_skill("/review")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "review")

    def test_get_unknown_skill(self):
        self.assertIsNone(self.get_skill("nonexistent"))

    def test_all_skills_have_system_prompt(self):
        for name in self.list_skills():
            skill = self.get_skill(name)
            self.assertGreater(len(skill.system_prompt), 50, f"{name} has short prompt")

    def test_list_skills_not_empty(self):
        skills = self.list_skills()
        self.assertGreater(len(skills), 5)
        self.assertIn("plan-ceo-review", skills)
        self.assertIn("review", skills)
        self.assertIn("ship", skills)


class TestMemory(unittest.TestCase):
    def setUp(self):
        # Redirect memory to temp dir for tests
        import core.memory as mem
        self._mem = mem
        self._orig_file = mem._MEMORY_FILE
        self._tmpdir = tempfile.mkdtemp()
        mem._MEMORY_DIR = pathlib.Path(self._tmpdir)
        mem._MEMORY_FILE = pathlib.Path(self._tmpdir) / "test_memory.json"

    def tearDown(self):
        self._mem._MEMORY_FILE = self._orig_file
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_retrieve(self):
        task_id = self._mem.save_task(
            skill="review",
            user_input="check auth module",
            output="Found 2 issues",
            model="llama3",
        )
        self.assertIsNotNone(task_id)
        task = self._mem.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["skill"], "review")
        self.assertEqual(task["input"], "check auth module")

    def test_recent_tasks(self):
        self._mem.save_task("review", "task 1", "output 1")
        self._mem.save_task("ship", "task 2", "output 2")
        tasks = self._mem.recent_tasks(n=5)
        self.assertEqual(len(tasks), 2)
        # Most recent first
        self.assertEqual(tasks[0]["skill"], "ship")

    def test_get_context(self):
        self._mem.save_task("review", "check auth", "found bug")
        ctx = self._mem.get_context(n=1)
        self.assertIn("review", ctx)
        self.assertIn("check auth", ctx)

    def test_config_set_get(self):
        self._mem.config_set("model", "llama3.2")
        val = self._mem.config_get("model")
        self.assertEqual(val, "llama3.2")

    def test_config_get_default(self):
        val = self._mem.config_get("nonexistent", default="fallback")
        self.assertEqual(val, "fallback")

    def test_clear_all(self):
        self._mem.save_task("review", "task", "output")
        self._mem.clear_all()
        tasks = self._mem.recent_tasks()
        self.assertEqual(len(tasks), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
