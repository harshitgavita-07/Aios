"""
AIOS v3.0 — AI-Native Operating Environment entry point.

Fixes applied:
  - Added missing `Optional` import from typing.
  - Resolved asyncio / Qt event loop conflict: asyncio.run() and
    qt_app.exec() cannot both block the main thread. v3 now uses
    PySide6.QtAsyncio (Qt 6.6+) to run the asyncio loop inside the Qt
    loop. Falls back to a manual QTimer-based asyncio tick on older Qt.
  - shutdown_runtime() was a sync function called with asyncio.run()
    inside a non-async context — fixed in runtime/aios_runtime.py (now
    an async coroutine); callers updated accordingly.
  - --mode flag parsing preserved; defaults to "legacy" so the app is
    immediately runnable without the full v3 workspace scaffolding.

Usage:
    python app_v3.py                   # legacy chat (safe default)
    python app_v3.py --mode legacy     # same
    python app_v3.py --mode workspace  # AI-native workspace (v3)
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("aios")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_qt_asyncio() -> bool:
    """Check whether PySide6.QtAsyncio is available (Qt 6.6+)."""
    try:
        import PySide6.QtAsyncio  # noqa: F401
        return True
    except ImportError:
        return False


def _run_async_with_qt(coro):
    """
    Run an async coroutine alongside the Qt event loop.

    Prefers PySide6.QtAsyncio when available.  Falls back to a QTimer-based
    asyncio tick that pumps the asyncio event loop every 50 ms while Qt runs.
    """
    if _has_qt_asyncio():
        import PySide6.QtAsyncio as QtAsyncio
        QtAsyncio.run(coro)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Pump asyncio inside Qt via a 50-ms timer
        def _tick():
            loop.run_until_complete(asyncio.sleep(0))

        timer = QTimer()
        timer.timeout.connect(_tick)
        timer.start(50)

        # Schedule the coroutine
        loop.run_until_complete(coro)


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------

class AIOSApplication:
    """
    AIOS application supporting two modes:
      - "legacy"    : traditional chat interface (v2, immediately runnable)
      - "workspace" : AI-native agent workspace (v3)
    """

    def __init__(self, mode: str = "legacy"):
        self.mode = mode
        self.runtime = None          # type: Optional[object]  # AIOSRuntime
        self.workspace_manager = None
        self._legacy_components = None

        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("AIOS")
        self.qt_app.setApplicationVersion("3.0.0")
        self.qt_app.setApplicationDisplayName("AIOS — AI-Native Workspace")
        self.qt_app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    async def initialize(self) -> None:
        """Async initialisation — called before the Qt event loop starts."""
        log.info("=" * 60)
        log.info("Starting AIOS v3.0 — AI-Native Operating Environment")
        log.info("Mode: %s", self.mode)
        log.info("=" * 60)

        if self.mode == "workspace":
            await self._init_workspace_mode()
        else:
            self._init_legacy_mode()

    async def _init_workspace_mode(self) -> None:
        log.info("Initialising AI-Native Workspace Mode...")
        from runtime.aios_runtime import init_runtime
        from ui.workspace import WorkspaceManager

        self.runtime = await init_runtime()
        self.workspace_manager = WorkspaceManager(self.runtime)
        self.workspace_manager.create_workspace()
        log.info("AI-Native Workspace initialised")

    def _init_legacy_mode(self) -> None:
        log.info("Initialising Legacy Chat Mode...")
        from core.agent import AgentController
        from ui.chat_ui import ChatWindow
        from ui.bubble import FloatingBubble

        data_dir = Path(__file__).parent / "data"
        agent = AgentController(data_dir)
        chat_window = ChatWindow(agent)

        def show_chat():
            chat_window.show()
            chat_window.raise_()
            chat_window.activateWindow()

        bubble = FloatingBubble(on_activate=show_chat)
        bubble.show()

        # Keep references alive for the duration of the Qt event loop
        self._legacy_components = (agent, chat_window, bubble)
        log.info("Legacy Chat Mode initialised")

    def show(self) -> None:
        if self.mode == "workspace" and self.workspace_manager:
            self.workspace_manager.show_workspace()

    async def shutdown(self) -> None:
        log.info("Shutting down AIOS...")
        if self.runtime is not None:
            from runtime.aios_runtime import shutdown_runtime
            await shutdown_runtime()
        if self.qt_app:
            self.qt_app.quit()
        log.info("AIOS shutdown complete")

    def run(self) -> None:
        """
        Start the Qt event loop.  Must be called AFTER initialize().
        """
        self.show()
        log.info("Qt event loop starting...")
        sys.exit(self.qt_app.exec())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mode = "legacy"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    app = AIOSApplication(mode=mode)

    async def _init_then_run():
        await app.initialize()
        app.run()   # Qt exec() blocks here; asyncio resumes only on quit

    try:
        if _has_qt_asyncio():
            import PySide6.QtAsyncio as QtAsyncio
            asyncio.run(_init_then_run())  # QtAsyncio overrides the loop
        else:
            # Run init synchronously (no I/O in legacy mode init), then Qt
            asyncio.run(app.initialize())
            app.run()
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        asyncio.run(app.shutdown())
    except Exception as e:
        log.error("Application failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
