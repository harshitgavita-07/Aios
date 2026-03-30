"""
Aios agent — central controller for the v2 runtime.

Pipeline:
    user input
        → Planner  (intent detection)
        → SoulSync (emotion + tone)
        → Memory   (conversation context)
        → LLM / Tool Executor
        → Memory   (save response)
        → yield tokens to UI
"""

from __future__ import annotations

import logging
import uuid
from typing import Generator

from core import memory, soulsync, planner as planner_mod
from tools.registry import ToolRegistry

log = logging.getLogger("aios.agent")

# Module-level tool registry (initialised once)
_registry = ToolRegistry()

# Active session ID — resets on app start, cleared on "new chat"
_session_id: str = str(uuid.uuid4())


# ── Public API ────────────────────────────────────────────────────────────

def session_id() -> str:
    return _session_id


def new_session() -> str:
    global _session_id
    _session_id = str(uuid.uuid4())
    return _session_id


def process(user_input: str) -> Generator[str, None, None]:
    """
    Main entry point called by the UI worker.

    Yields string tokens (or full strings for tool/system responses).
    """
    text = user_input.strip()
    if not text:
        return

    # 1. Plan
    plan = planner_mod.plan(text)
    log.debug("plan=%s action=%s", plan.intent, plan.action)

    # 2. Emotion analysis
    soul = soulsync.analyse(text)
    log.debug("emotion=%s conf=%.2f", soul.emotion, soul.confidence)

    # 3. Save user message
    memory.save(_session_id, "user", text, emotion=soul.emotion)

    # 4. Route
    if plan.intent == "system":
        response = _handle_system(plan)
        memory.save(_session_id, "assistant", response)
        yield response
        return

    if plan.intent == "tool":
        response = _handle_tool(plan)
        memory.save(_session_id, "assistant", response)
        yield response
        return

    # 5. Chat — stream through LLM with memory context
    history = memory.history(_session_id)
    full_response: list[str] = []

    from llm import stream_with_history
    for token in stream_with_history(
        system_prompt=soul.system_prompt,
        history=history,
        user_input=text,
    ):
        full_response.append(token)
        yield token

    # 6. Save assistant response
    memory.save(_session_id, "assistant", "".join(full_response))


# ── System command handlers ───────────────────────────────────────────────

def _handle_system(plan: planner_mod.Plan) -> str:
    action = plan.action

    if action == "clear_memory":
        memory.clear_session(_session_id)
        new_session()
        return "Memory cleared. Starting a fresh session. 🧹"

    if action == "list_models":
        from llm import list_models
        models = list_models()
        if not models:
            return "No models installed. Run: ollama pull llama3.2"
        return "Installed models:\n" + "\n".join(f"  • {m}" for m in models)

    if action == "current_model":
        from llm import get_model
        return f"Current model: {get_model()}"

    if action == "show_hardware":
        from llm import get_hw_info
        hw = get_hw_info()
        lines = [
            f"GPU: {hw.get('gpu_name', 'none')}",
            f"VRAM: {hw.get('vram_gb', 0)} GB",
            f"RAM: {hw.get('ram_gb', 0)} GB",
            f"CPU cores: {hw.get('cpu_cores', 0)}",
            f"Backend: {hw.get('backend', 'cpu')}",
        ]
        return "\n".join(lines)

    if action == "help":
        return (
            "Aios v2 — what I can do:\n"
            "  • Answer questions and have conversations\n"
            "  • Remember what we've discussed this session\n"
            "  • 'clear chat' — start a fresh session\n"
            "  • 'list models' — show installed models\n"
            "  • 'show hardware' — display GPU/CPU info\n"
            "  • 'think about X' — structured reasoning step\n"
        )

    return f"[system: {action}]"


# ── Tool handlers ─────────────────────────────────────────────────────────

def _handle_tool(plan: planner_mod.Plan) -> str:
    action = plan.action

    if action == "think":
        import json
        result = _registry.run("think_tool", json.dumps({"thought": plan.payload}))
        try:
            import json as _j
            data = _j.loads(result)
            thought = data.get("thought", plan.payload)
            return f"💭 Thought: {thought}"
        except Exception:
            return result

    # For other tools, check whitelist
    tool_name = action
    if not _registry.has(tool_name):
        return (
            f"Tool '{tool_name}' is not available. "
            "Only whitelisted tools can be executed."
        )

    try:
        return _registry.run(tool_name, plan.payload)
    except Exception as e:
        log.error("tool %s error: %s", tool_name, e)
        return f"Tool error: {e}"
