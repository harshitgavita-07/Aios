"""
AIOS v3.0 — AI-Native Operating Environment

The next evolution of AIOS: from AI assistant to AI-native operating system.
This version transforms AIOS into a runtime layer where agents, workflows,
and on-device intelligence are the core UI paradigm.
"""

import asyncio
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("aios")

# Import AIOS runtime components
from runtime.aios_runtime import AIOSRuntime, init_runtime, shutdown_runtime
from ui.workspace import WorkspaceManager

# Legacy imports for backward compatibility
from core.agent import AgentController
from ui.chat_ui import ChatWindow
from ui.bubble import FloatingBubble


class AIOSApplication:
    """
    The main AIOS application that can run in different modes:
    - workspace: AI-native desktop environment (default)
    - legacy: Traditional chat interface (backward compatibility)
    """

    def __init__(self, mode: str = "workspace"):
        self.mode = mode
        self.runtime: Optional[AIOSRuntime] = None
        self.workspace_manager: Optional[WorkspaceManager] = None
        self.legacy_app = None

        # Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("AIOS")
        self.qt_app.setApplicationVersion("3.0.0")
        self.qt_app.setApplicationDisplayName("AIOS — AI-Native Workspace")

        # Enable high DPI scaling
        self.qt_app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    async def initialize(self):
        """Initialize the AIOS application."""
        log.info("=" * 60)
        log.info("Starting AIOS v3.0 — AI-Native Operating Environment")
        log.info("=" * 60)

        if self.mode == "workspace":
            await self._init_workspace_mode()
        elif self.mode == "legacy":
            self._init_legacy_mode()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    async def _init_workspace_mode(self):
        """Initialize AI-native workspace mode."""
        log.info("Initializing AI-Native Workspace Mode...")

        # Initialize AIOS runtime
        self.runtime = await init_runtime()

        # Create workspace manager
        self.workspace_manager = WorkspaceManager(self.runtime)

        # Create and show workspace
        workspace = self.workspace_manager.create_workspace()

        # Register initial agents
        await self._register_core_agents()

        log.info("AI-Native Workspace initialized successfully")

    def _init_legacy_mode(self):
        """Initialize legacy chat interface mode."""
        log.info("Initializing Legacy Chat Mode...")

        # Initialize legacy components
        data_dir = Path(__file__).parent / "data"
        agent = AgentController(data_dir)

        # Create UI components
        chat_window = ChatWindow(agent)

        def show_chat():
            chat_window.show()
            chat_window.raise_()
            chat_window.activateWindow()

        bubble = FloatingBubble(on_activate=show_chat)
        bubble.show()

        self.legacy_app = (agent, chat_window, bubble)
        log.info("Legacy Chat Mode initialized")

    async def _register_core_agents(self):
        """Register core AIOS agents."""
        if not self.runtime:
            return

        # Core system agent (already registered in runtime init)
        log.info("Core agents registered")

        # Could register additional agents here:
        # - File management agent
        # - Network agent
        # - Development agent
        # - Productivity agent
        # etc.

    def show_workspace(self):
        """Show the AI-native workspace."""
        if self.workspace_manager:
            self.workspace_manager.show_workspace()

    async def process_user_input(self, user_input: str) -> str:
        """Process user input through the runtime."""
        if self.runtime:
            return await self.runtime.process_user_input(user_input)
        return "Runtime not available"

    def run(self):
        """Run the AIOS application."""
        try:
            if self.mode == "workspace":
                # Show workspace
                self.show_workspace()

                # Start Qt event loop
                log.info("Starting Qt event loop...")
                sys.exit(self.qt_app.exec())

            elif self.mode == "legacy":
                # Legacy mode already has UI components shown
                log.info("Starting legacy Qt event loop...")
                sys.exit(self.qt_app.exec())

        except KeyboardInterrupt:
            log.info("Received interrupt signal")
        except Exception as e:
            log.error(f"Application error: {e}")
        finally:
            # Cleanup
            if self.runtime:
                asyncio.run(shutdown_runtime())
            log.info("AIOS shutdown complete")

    async def shutdown(self):
        """Shutdown the application gracefully."""
        log.info("Shutting down AIOS...")

        if self.runtime:
            await shutdown_runtime()

        if self.qt_app:
            self.qt_app.quit()

        log.info("AIOS shutdown complete")


def main():
    """
    Main entry point for AIOS v3.0.

    Usage:
        python app.py                    # AI-native workspace (default)
        python app.py --mode legacy      # Legacy chat interface
        python app.py --mode workspace   # Explicit workspace mode
    """

    # Parse command line arguments
    mode = "workspace"  # Default to AI-native workspace

    if len(sys.argv) > 1:
        if "--mode" in sys.argv:
            mode_idx = sys.argv.index("--mode")
            if mode_idx + 1 < len(sys.argv):
                mode = sys.argv[mode_idx + 1]

    # Create and run application
    app = AIOSApplication(mode=mode)

    # Initialize asyncio components
    async def init_and_run():
        await app.initialize()
        app.run()

    # Run with asyncio
    try:
        asyncio.run(init_and_run())
    except KeyboardInterrupt:
        log.info("Application interrupted by user")
        asyncio.run(app.shutdown())
    except Exception as e:
        log.error(f"Application failed: {e}")
        asyncio.run(app.shutdown())
        sys.exit(1)


if __name__ == "__main__":
    main()