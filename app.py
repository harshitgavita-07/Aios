"""
Aios v2.0 — Local AI Runtime
Entry point for the next-generation AIOS.
"""

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

# Import core components
from core.agent import AgentController
from ui.chat_ui import ChatWindow
from ui.bubble import FloatingBubble
from tools.executor import ToolExecutor
from tools.system_tools import SystemTools


def setup_tools(agent: AgentController):
    """
    Register system tools with the agent.
    
    Change: Tool setup moved to dedicated function
    Why:
    - Clearer initialization flow
    - Easy to add/remove tools
    Impact:
    - Modular tool configuration
    """
    executor = ToolExecutor()
    system_tools = SystemTools()
    
    # Register whitelisted tools
    tools = system_tools.get_tools_dict()
    for name, handler in tools.items():
        executor.register_tool(name, handler, whitelisted=True)
    
    agent.set_tool_executor(executor)
    log.info(f"Registered {len(tools)} whitelisted tools")


def main():
    """
    Main entry point.
    
    Change: Enhanced initialization sequence
    Why:
    - Proper component initialization order
    - Better error handling on startup
    Impact:
    - Reliable startup
    - Clear error messages
    """
    log.info("=" * 50)
    log.info("Starting AIOS v2.0")
    log.info("=" * 50)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AIOS")
    app.setApplicationVersion("2.0.0")
    
    # Enable high DPI scaling
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Initialize agent controller
    try:
        data_dir = Path(__file__).parent / "data"
        agent = AgentController(data_dir)
        log.info("AgentController initialized")
    except Exception as e:
        log.error(f"Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Setup tools
    setup_tools(agent)
    
    # Create UI components
    chat_window = ChatWindow(agent)
    
    def show_chat():
        chat_window.show()
        chat_window.raise_()
        chat_window.activateWindow()
    
    bubble = FloatingBubble(on_activate=show_chat)
    bubble.show()
    
    log.info("AIOS ready")
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
