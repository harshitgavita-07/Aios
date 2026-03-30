"""
Aios planner — intent detection and routing.

Classifies user input into one of three intents:
  chat        → standard LLM response
  tool        → route to tool executor (e.g. run a shell command)
  system      → internal Aios commands (clear memory, list models, etc.)

Uses keyword + pattern matching — zero latency, no extra deps.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class Plan(NamedTuple):
    intent: str       # "chat" | "tool" | "system"
    action: str       # sub-action label
    confidence: float
    payload: str      # cleaned payload for the action handler


# ── Intent patterns ───────────────────────────────────────────────────────

# System commands — Aios meta-operations
_SYSTEM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(clear|reset|new)\s+(chat|memory|history|conversation)\b", re.I), "clear_memory"),
    (re.compile(r"\b(list|show)\s+models?\b", re.I),                                  "list_models"),
    (re.compile(r"\b(what model|which model|current model)\b", re.I),                 "current_model"),
    (re.compile(r"\b(switch|change|use)\s+model\b", re.I),                            "switch_model"),
    (re.compile(r"\b(show|display)\s+(hardware|gpu|cpu|specs?)\b", re.I),              "show_hardware"),
    (re.compile(r"\b(help|commands|what can you do)\b", re.I),                        "help"),
]

# Tool execution — user wants Aios to DO something on the system
_TOOL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(run|execute|eval)\s+(.+)", re.I),          "run_command"),
    (re.compile(r"\b(open|launch)\s+(.+)", re.I),               "open_app"),
    (re.compile(r"\b(search|find)\s+(.+)\s+in\s+files?\b", re.I), "file_search"),
    (re.compile(r"\bthink(\s+about)?\s+(.+)", re.I),            "think"),
]


# ── Public API ────────────────────────────────────────────────────────────

def plan(user_input: str) -> Plan:
    """
    Analyse *user_input* and return a Plan describing what Aios should do.

    Priority: system > tool > chat
    """
    text = user_input.strip()
    lower = text.lower()

    # 1. System commands
    for pattern, action in _SYSTEM_PATTERNS:
        if pattern.search(lower):
            return Plan(intent="system", action=action, confidence=0.95, payload=text)

    # 2. Tool execution
    for pattern, action in _TOOL_PATTERNS:
        m = pattern.search(text)
        if m:
            payload = m.group(m.lastindex) if m.lastindex else text
            return Plan(intent="tool", action=action, confidence=0.85, payload=payload.strip())

    # 3. Default: chat
    return Plan(intent="chat", action="llm_chat", confidence=1.0, payload=text)
