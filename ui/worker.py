"""
UI Worker — Background task runner for non-blocking UI
"""

from PySide6.QtCore import QThread, Signal
from typing import Generator


class AgentWorker(QThread):
    """
    Background worker for agent processing.

    Fix: process_stream() yields typed dicts, not raw strings.
    Each dict has a "type" key: "thinking", "mode", "token",
    "sources", "complete", "error". The worker now routes each
    update to the correct signal instead of blindly treating
    every item as a string token.
    """

    # Emitted for each token of the assistant reply
    token_signal = Signal(str)
    # Emitted for thinking/status updates
    thinking_signal = Signal(str)
    # Emitted when mode is detected
    mode_signal = Signal(str)
    # Emitted with number of RAG sources found
    sources_signal = Signal(int)
    # Emitted with confidence string when generation is complete
    complete_signal = Signal(str)
    # Emitted on any unrecoverable error
    error_signal = Signal(str)

    def __init__(self, agent, user_input: str, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.user_input = user_input

    def run(self):
        try:
            for update in self.agent.process_stream(self.user_input):
                update_type = update.get("type", "")
                if update_type == "token":
                    self.token_signal.emit(update.get("content", ""))
                elif update_type == "thinking":
                    self.thinking_signal.emit(update.get("message", ""))
                elif update_type == "mode":
                    self.mode_signal.emit(update.get("mode", ""))
                elif update_type == "sources":
                    self.sources_signal.emit(update.get("count", 0))
                elif update_type == "complete":
                    self.complete_signal.emit(update.get("confidence", ""))
                elif update_type == "error":
                    self.error_signal.emit(update.get("message", "Unknown error"))
        except Exception as e:
            self.error_signal.emit(str(e))


class ToolWorker(QThread):
    """Worker for tool execution."""
    
    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, executor, tool_name: str, payload, parent=None):
        super().__init__(parent)
        self.executor = executor
        self.tool_name = tool_name
        self.payload = payload

    def run(self):
        try:
            result = self.executor.execute(self.tool_name, self.payload)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ToolWorker(QThread):
    """Worker for tool execution."""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, executor, tool_name: str, payload, parent=None):
        super().__init__(parent)
        self.executor = executor
        self.tool_name = tool_name
        self.payload = payload

    def run(self):
        try:
            result = self.executor.execute(self.tool_name, self.payload)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
