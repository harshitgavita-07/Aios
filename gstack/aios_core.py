"""
aios_core.py

AIOS — Local AI Operating System
Central orchestrator: routes input → skill → Ollama → memory → output.

Fix: `from core.ollama_client import ...` was a wrong import path.
     Inside the gstack package, imports must be relative or use the full
     gstack.core prefix. Changed to `from gstack.core.ollama_client`.
     Same fix applied to skills, router and memory imports.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Optional, Generator

# Fix: was `from core.ollama_client` — that resolves to the top-level
# core/ package (core/agent.py etc), not gstack/core/.
# Correct path is gstack.core.* (absolute) or .core.* (relative).
from gstack.core.ollama_client import generate, generate_stream, health_check, list_models
from gstack.core.skills import get_skill, list_skills, Skill
from gstack.core.router import route, route_explicit
from gstack.core import memory

log = logging.getLogger("aios")


@dataclass
class TaskResult:
    task_id: str
    skill: str
    role: str
    model: str
    input: str
    output: str
    success: bool
    error: Optional[str] = None


class AIOS:
    """
    Local AI Operating System.

    Wraps Ollama with gstack's role-based skill system and JSON memory.
    No external API keys. No cloud. Fully local.
    """

    def __init__(
        self,
        model: str = "llama3",
        temperature: float = 0.7,
        verbose: bool = False,
    ):
        self.model = model
        self.temperature = temperature

        if verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(name)s %(levelname)s %(message)s",
            )

        # Verify Ollama is running
        if not health_check():
            raise RuntimeError(
                "Ollama is not running. Start it with: ollama serve\n"
                f"Then pull a model: ollama pull {model}"
            )

        log.info("AIOS initialised. model=%s", model)

    # ── Main entry points ──────────────────────────────────────────────

    def run(
        self,
        command_or_input: str,
        task: Optional[str] = None,
        stream: bool = False,
        include_context: bool = False,
    ) -> TaskResult:
        """
        Run a task through AIOS.

        Args:
            command_or_input: Either an explicit command ("/review") or
                              natural language ("build a NLP library").
            task: Optional separate task description.
            stream: If True, prints tokens to stdout as they arrive.
            include_context: If True, appends recent task history to prompt.

        Returns:
            TaskResult with output and metadata.
        """
        if task is not None:
            skill_name = route_explicit(command_or_input) or route(command_or_input)
            user_input = task
        else:
            skill_name = route_explicit(command_or_input)
            if skill_name:
                user_input = f"Run the {skill_name} skill. No specific task provided."
            else:
                skill_name = route(command_or_input)
                user_input = command_or_input

        skill = get_skill(skill_name)
        if not skill:
            skill_name = "plan-ceo-review"
            skill = get_skill(skill_name)

        log.info("skill=%s model=%s", skill_name, self.model)

        prompt = self._build_prompt(user_input, skill, include_context)

        try:
            if stream:
                output = self._run_stream(prompt, skill)
            else:
                output = generate(
                    prompt=prompt,
                    model=self.model,
                    system=skill.system_prompt,
                    temperature=self.temperature,
                )

            task_id = memory.save_task(
                skill=skill_name,
                user_input=user_input,
                output=output,
                model=self.model,
            )

            return TaskResult(
                task_id=task_id,
                skill=skill_name,
                role=skill.role,
                model=self.model,
                input=user_input,
                output=output,
                success=True,
            )

        except Exception as e:
            log.error("run failed: %s", e)
            return TaskResult(
                task_id="",
                skill=skill_name,
                role=skill.role if skill else "unknown",
                model=self.model,
                input=user_input,
                output="",
                success=False,
                error=str(e),
            )

    def stream(self, command_or_input: str, task: Optional[str] = None) -> TaskResult:
        """Convenience wrapper for run() with stream=True."""
        return self.run(command_or_input, task=task, stream=True)

    def plan(self, task: str) -> TaskResult:
        return self.run("/plan-ceo-review", task=task)

    def eng_plan(self, task: str) -> TaskResult:
        return self.run("/plan-eng-review", task=task)

    def review(self, task: str) -> TaskResult:
        return self.run("/review", task=task)

    def qa(self, task: str) -> TaskResult:
        return self.run("/qa", task=task)

    def ship(self, task: str) -> TaskResult:
        return self.run("/ship", task=task)

    def investigate(self, bug: str) -> TaskResult:
        return self.run("/investigate", task=bug)

    def office_hours(self, idea: str) -> TaskResult:
        return self.run("/office-hours", task=idea)

    def status(self) -> dict:
        models = list_models()
        return {
            "ollama_running": health_check(),
            "current_model": self.model,
            "model_available": self.model in models,
            "installed_models": models,
            "available_skills": list_skills(),
            "task_count": len(memory.recent_tasks(n=9999)),
        }

    def history(self, n: int = 10) -> list:
        return memory.recent_tasks(n=n)

    def _build_prompt(self, user_input: str, skill: Skill, include_context: bool) -> str:
        parts = []
        if include_context:
            ctx = memory.get_context(n=3)
            if ctx:
                parts.append(ctx)
                parts.append("")
        parts.append(f"## Task\n{user_input}")
        return "\n".join(parts)

    def _run_stream(self, prompt: str, skill: Skill) -> str:
        print(f"\n[{skill.role}]\n", flush=True)
        tokens: list = []
        for token in generate_stream(
            prompt=prompt,
            model=self.model,
            system=skill.system_prompt,
            temperature=self.temperature,
        ):
            print(token, end="", flush=True)
            tokens.append(token)
        print("\n", flush=True)
        return "".join(tokens)
