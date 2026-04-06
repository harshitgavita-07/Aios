"""
AIOS — Unified Entry Point
AI-Native Operating Environment

Covers all versions and all modes in one file:
  - legacy  : v2 chat interface with floating bubble + full tool setup
  - workspace: v3 AI-native workspace with agent mesh, workflow engine,
               intent engine, and multi-agent orchestration

Usage
-----
    python app.py                    # workspace mode (default — v3)
    python app.py --mode legacy      # classic chat interface (v2)
    python app.py --mode workspace   # explicit workspace mode
    python app.py --help

Architecture this file connects
--------------------------------
    app.py
      ├── core/           agent, memory, soulsync, planner, llm,
      │                   mode_controller, confidence, context_manager
      ├── rag/            embedder, vector_store, retriever, pipeline,
      │                   web_search, processor
      ├── tools/          executor, registry, system_tools, think_tool
      ├── gstack/         aios_core, aios_gstack, core/*  (skills, router)
      ├── runtime/        aios_runtime  (AgentMesh, WorkflowEngine, etc.)
      └── ui/             chat_ui, workspace, bubble, worker
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# ── Logging ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("aios")


# ── Helpers ───────────────────────────────────────────────────────────────

def _has_qt_asyncio() -> bool:
    """PySide6.QtAsyncio is available from Qt 6.6+."""
    try:
        import PySide6.QtAsyncio  # noqa: F401
        return True
    except ImportError:
        return False


def _setup_tools(agent) -> None:
    """
    Register all whitelisted system tools with the agent's ToolExecutor.

    Connected modules: tools/executor.py, tools/system_tools.py
    Why needed: The tool whitelist in tools/registry.py gates execution;
                tools must be registered under the exact whitelisted key.
    """
    from tools.executor import ToolExecutor
    from tools.system_tools import SystemTools

    executor = ToolExecutor()
    system_tools = SystemTools()

    registered = 0
    for name, handler in system_tools.get_tools_dict().items():
        executor.register_tool(name, handler, whitelisted=True)
        registered += 1

    agent.set_tool_executor(executor)
    log.info("Registered %d whitelisted tools", registered)


# ── Legacy mode (v2 chat interface) ──────────────────────────────────────

def _run_legacy(qt_app: QApplication) -> None:
    """
    Initialize and show the v2 chat interface.

    Connected modules:
        core/agent.py     → AgentController (memory + soulsync + llm + rag)
        ui/chat_ui.py     → ChatWindow (streaming UI with thinking steps)
        ui/bubble.py      → FloatingBubble (always-on-top quick access)
        tools/*           → ToolExecutor + SystemTools (all system tools)
        rag/*             → RAGPipeline (web search + FAISS vector store)
    """
    log.info("=" * 60)
    log.info("AIOS v2/v3 — Legacy Chat Mode")
    log.info("=" * 60)

    from core.agent import AgentController
    from ui.chat_ui import ChatWindow
    from ui.bubble import FloatingBubble

    data_dir = Path(__file__).parent / "data"

    try:
        agent = AgentController(data_dir)
    except Exception as exc:
        log.error("AgentController init failed: %s", exc)
        sys.exit(1)

    _setup_tools(agent)

    chat_window = ChatWindow(agent)

    def _show_chat() -> None:
        chat_window.show()
        chat_window.raise_()
        chat_window.activateWindow()

    bubble = FloatingBubble(on_activate=_show_chat)
    bubble.show()

    log.info("AIOS legacy mode ready — Qt event loop starting")
    sys.exit(qt_app.exec())


# ── Workspace mode (v3 AI-native OS) ─────────────────────────────────────

async def _init_workspace(qt_app: QApplication) -> None:
    """
    Initialize the v3 AI-native workspace.

    Connected modules:
        runtime/aios_runtime.py → AIOSRuntime (AgentMesh, WorkflowEngine,
                                   IntentEngine, ContextEngine, ResourceManager)
        ui/workspace.py         → WorkspaceManager + AIOSWorkspace
        core/agent.py           → AgentController (registered as core agent)
        tools/*                 → via AgentController
    """
    log.info("=" * 60)
    log.info("AIOS v3 — AI-Native Workspace Mode")
    log.info("=" * 60)

    from runtime.aios_runtime import init_runtime, shutdown_runtime
    from ui.workspace import WorkspaceManager

    try:
        runtime = await init_runtime()
    except Exception as exc:
        log.error("Runtime init failed: %s — falling back to legacy mode", exc)
        _run_legacy(qt_app)
        return

    # Also set up tools on the core agent so workspace agents can use them
    if runtime.core_agent and runtime.core_agent.controller:
        try:
            _setup_tools(runtime.core_agent.controller)
        except Exception as exc:
            log.warning("Tool setup on core agent failed: %s", exc)

    workspace_manager = WorkspaceManager(runtime)
    workspace_manager.create_workspace()
    workspace_manager.show_workspace()

    log.info("AIOS workspace ready — Qt event loop starting")

    try:
        sys.exit(qt_app.exec())
    finally:
        await shutdown_runtime()


# ── Application bootstrap ─────────────────────────────────────────────────

def _build_qt_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("AIOS")
    app.setApplicationVersion("3.0.0")
    app.setApplicationDisplayName("AIOS — AI-Native Operating Environment")
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    return app


def main() -> None:
    """
    Unified AIOS entry point.

    Parses --mode flag and boots the appropriate runtime:
      - workspace (default): v3 AI-native OS with agent mesh
      - legacy             : v2 chat interface with tool execution
    """
    mode = "workspace"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    elif "--legacy" in sys.argv or "-l" in sys.argv:
        mode = "legacy"

    if mode not in ("workspace", "legacy"):
        print(f"Unknown mode '{mode}'. Use: workspace | legacy", file=sys.stderr)
        sys.exit(1)

    qt_app = _build_qt_app()

    if mode == "legacy":
        _run_legacy(qt_app)
        return  # sys.exit called inside

    # Workspace mode — needs asyncio
    if _has_qt_asyncio():
        # Qt 6.6+: QtAsyncio manages the event loop natively
        import PySide6.QtAsyncio as QtAsyncio

        async def _boot():
            await _init_workspace(qt_app)

        try:
            asyncio.run(_boot())
        except KeyboardInterrupt:
            log.info("Interrupted")
    else:
        # Older Qt: init async, then hand off to Qt event loop
        try:
            asyncio.run(_init_workspace(qt_app))
        except KeyboardInterrupt:
            log.info("Interrupted")
        except Exception as exc:
            log.error("Startup error: %s", exc, exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
