"""
core/router.py

Task router — maps natural language input to gstack skill commands.

Example:
    route("build a NLP library") → "plan-ceo-review"
    route("fix the auth bug")    → "investigate"
    route("deploy to production") → "ship"
"""

from __future__ import annotations

import re
from typing import Optional


# ── Routing rules ─────────────────────────────────────────────────────────
# (pattern, skill_name, priority)  — higher priority wins on ties

_RULES: list[tuple[re.Pattern, str, int]] = [
    # Ship / deploy
    (re.compile(r"\b(ship|deploy|release|land|merge|push to prod)\b", re.I), "ship", 10),

    # Investigation / debugging
    (re.compile(r"\b(debug|investigate|bug|broken|crash|error|not working|failing|fix)\b", re.I), "investigate", 8),

    # QA / testing
    (re.compile(r"\b(test|qa|quality|verify|validate|check if it works)\b", re.I), "qa", 7),

    # Code review
    (re.compile(r"\b(review|audit|check|look at|inspect)\b", re.I), "review", 6),

    # Engineering planning
    (re.compile(r"\b(architect|design|plan|implement|how to build|how do I build|structure)\b", re.I), "plan-eng-review", 5),

    # Product / CEO thinking
    (re.compile(r"\b(build|create|make|launch|start|idea|feature|product)\b", re.I), "plan-ceo-review", 4),

    # Office hours / ideation
    (re.compile(r"\b(thinking about|exploring|not sure|help me think|what should|office hours)\b", re.I), "office-hours", 9),
]

# Default when nothing matches
_DEFAULT_SKILL = "plan-ceo-review"


def route(user_input: str) -> str:
    """
    Map user_input to the most appropriate skill name.
    Returns the skill name string (without leading slash).
    """
    text = user_input.strip()
    best_skill = _DEFAULT_SKILL
    best_priority = -1

    for pattern, skill, priority in _RULES:
        if pattern.search(text) and priority > best_priority:
            best_skill = skill
            best_priority = priority

    return best_skill


def route_explicit(command: str) -> Optional[str]:
    """
    If the user explicitly typed a skill command (e.g. /plan-ceo-review),
    return the skill name. Otherwise return None.
    """
    clean = command.strip().lstrip("/")
    from core.skills import SKILLS
    return clean if clean in SKILLS else None
