"""
core/memory.py

JSON-based task memory system.
Stores inputs, outputs, skill used, and timestamps.
Lives at ~/.aios-gstack/memory.json
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Optional

_MEMORY_DIR = Path.home() / ".aios-gstack"
_MEMORY_FILE = _MEMORY_DIR / "memory.json"


def _load() -> dict:
    if not _MEMORY_FILE.exists():
        return {"tasks": [], "config": {}}
    try:
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"tasks": [], "config": {}}


def _save(data: dict) -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    _MEMORY_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_task(
    skill: str,
    user_input: str,
    output: str,
    model: str = "llama3",
    metadata: Optional[dict] = None,
) -> str:
    """Persist a completed task. Returns the task ID."""
    data = _load()
    task_id = str(uuid.uuid4())[:8]
    data["tasks"].append({
        "id":         task_id,
        "skill":      skill,
        "input":      user_input,
        "output":     output,
        "model":      model,
        "metadata":   metadata or {},
        "timestamp":  time.time(),
        "ts_human":   time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save(data)
    return task_id


def get_task(task_id: str) -> Optional[dict]:
    data = _load()
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def recent_tasks(n: int = 10) -> list[dict]:
    """Return the N most recent tasks, newest first."""
    data = _load()
    tasks = data.get("tasks", [])
    return list(reversed(tasks[-n:]))


def get_context(n: int = 3) -> str:
    """
    Return a brief context string of the last N tasks
    for inclusion in prompts when follow-up context matters.
    """
    tasks = recent_tasks(n)
    if not tasks:
        return ""
    lines = ["## Recent context"]
    for t in reversed(tasks):
        lines.append(f"[{t['ts_human']}] /{t['skill']}: {t['input'][:80]}...")
    return "\n".join(lines)


def config_set(key: str, value: str) -> None:
    data = _load()
    data.setdefault("config", {})[key] = value
    _save(data)


def config_get(key: str, default: Optional[str] = None) -> Optional[str]:
    data = _load()
    return data.get("config", {}).get(key, default)


def clear_all() -> None:
    """Wipe all stored tasks (keeps config)."""
    data = _load()
    data["tasks"] = []
    _save(data)
