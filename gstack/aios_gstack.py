"""
aios_gstack.py

Python wrapper for gstack CLI.

gstack (https://github.com/garrytan/gstack) is a Claude Code skill system
that runs Markdown prompt templates. This wrapper provides two execution modes:

MODE 1 — Direct (default, recommended):
    AIOS reads gstack's skill definitions and executes them via Ollama locally.
    No Claude Code required. Works offline. Uses Ollama as the LLM.

MODE 2 — Subprocess bridge (requires Claude Code + gstack installed):
    Calls the actual gstack CLI via subprocess for full fidelity.
    Requires: npm install -g @anthropic-ai/claude-code, gstack installed.

Usage:
    from aios_gstack import run_gstack, GStackRunner

    # Direct mode (Ollama, no Claude Code needed)
    result = run_gstack("/plan-ceo-review", "Build BharatLang NLP library")

    # Check if native gstack is available
    runner = GStackRunner()
    print(runner.available)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Fix: was `from aios_core import ...` — bare import only works if
# Python is launched from inside gstack/. Use absolute package path.
from gstack.aios_core import AIOS, TaskResult

log = logging.getLogger("aios.gstack")

# Default gstack install locations
_GSTACK_PATHS = [
    Path.home() / ".claude" / "skills" / "gstack",
    Path(".claude") / "skills" / "gstack",
    Path(".agents") / "skills" / "gstack",
]


class GStackRunner:
    """
    Intelligent gstack runner.

    Checks if native gstack is installed and uses it if available.
    Falls back to AIOS direct mode (Ollama) otherwise.
    """

    def __init__(self, model: str = "llama3", prefer_native: bool = False):
        self.model = model
        self.prefer_native = prefer_native
        self._aios: Optional[AIOS] = None

        # Find native gstack
        self.gstack_dir: Optional[Path] = self._find_gstack()
        self.has_claude_code: bool = shutil.which("claude") is not None

        self.available = self.gstack_dir is not None and self.has_claude_code
        log.info(
            "GStackRunner: native=%s gstack_dir=%s",
            self.available,
            self.gstack_dir,
        )

    @property
    def aios(self) -> AIOS:
        if self._aios is None:
            self._aios = AIOS(model=self.model)
        return self._aios

    def run(
        self,
        command: str,
        task: str,
        use_native: Optional[bool] = None,
        stream: bool = False,
    ) -> TaskResult:
        """
        Run a gstack skill command with a task description.

        Args:
            command: Skill name like "/plan-ceo-review" or "plan-ceo-review"
            task:    Task description to analyse
            use_native: Override native/direct mode. None = auto-detect.
            stream:  Stream output to stdout as it generates.
        """
        should_use_native = (
            use_native if use_native is not None
            else (self.prefer_native and self.available)
        )

        if should_use_native:
            return self._run_native(command, task)
        else:
            return self.aios.run(command, task=task, stream=stream)

    def _run_native(self, command: str, task: str) -> TaskResult:
        """
        Execute gstack via Claude Code subprocess.

        This method starts a Claude Code session and injects the gstack
        skill command. It requires Claude Code and gstack to be installed.

        Note: Claude Code is interactive by nature. This subprocess approach
        works best for non-interactive, single-shot tasks.
        """
        if not self.available:
            raise RuntimeError(
                "Native gstack not available. "
                "Install Claude Code and gstack, or use direct mode."
            )

        skill = command.lstrip("/")
        skill_path = self.gstack_dir / skill / "SKILL.md"

        if not skill_path.exists():
            log.warning(
                "Skill file not found: %s — falling back to AIOS direct mode",
                skill_path,
            )
            return self.aios.run(command, task=task)

        # Build the Claude Code invocation
        # Claude Code accepts -p flag for non-interactive print mode
        prompt = (
            f"Read and execute the skill at {skill_path}. "
            f"Apply it to this task: {task}"
        )

        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.gstack_dir.parent.parent.parent,  # repo root
            )
            output = result.stdout.strip() or result.stderr.strip()
            success = result.returncode == 0
        except subprocess.TimeoutExpired:
            output = "Claude Code timed out after 300 seconds."
            success = False
        except FileNotFoundError:
            output = "Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code"
            success = False

        return TaskResult(
            task_id="native",
            skill=skill,
            role=skill,
            model="claude-via-claude-code",
            input=task,
            output=output,
            success=success,
            error=None if success else output,
        )

    def _find_gstack(self) -> Optional[Path]:
        for p in _GSTACK_PATHS:
            if p.exists() and (p / "review" / "SKILL.md").exists():
                return p
        return None

    def status(self) -> dict:
        return {
            "mode": "native" if (self.available and self.prefer_native) else "direct",
            "native_gstack_available": self.available,
            "gstack_dir": str(self.gstack_dir) if self.gstack_dir else None,
            "has_claude_code": self.has_claude_code,
            **self.aios.status(),
        }


# ── Module-level convenience function ────────────────────────────────────

def run_gstack(
    command: str,
    task: str,
    model: str = "llama3",
    stream: bool = False,
) -> TaskResult:
    """
    Run a gstack skill locally via Ollama.

    This is the primary entry point for AIOS-gstack integration.
    Always runs in direct mode (Ollama) — no Claude Code required.

    Args:
        command: Skill command, e.g. "/plan-ceo-review" or "/review"
        task:    Task description
        model:   Ollama model name (default: "llama3")
        stream:  Stream output to stdout

    Returns:
        TaskResult with the skill's response

    Example:
        result = run_gstack("/plan-ceo-review", "Build BharatLang NLP library")
        print(result.output)

        result = run_gstack("/review", "Check the authentication module for security issues")
        print(result.output)
    """
    aios = AIOS(model=model)
    return aios.run(command, task=task, stream=stream)
