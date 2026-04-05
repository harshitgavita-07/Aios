"""
UI Worker — Background task runners for non-blocking UI.

Fixes in this file:
  Bug 1 — ToolWorker was defined TWICE (lines 58 and 78 in original).
           The second definition silently shadowed the first. Removed duplicate.

  Bug 6 — AgentWorker.sources_signal was Signal(int) but process_stream()
           yields {"type": "sources", "data": {"count": int, "sources": list}}.
           StreamWorker in chat_ui.py correctly uses Signal(dict). Fixed to match.
"""

from PySide6.QtCore import QThread, Signal


class AgentWorker(QThread):
    """
    Background worker for agent processing (used by app.py v2 entry point).

    Routes typed dicts from AgentController.process_stream() to the
    correct Qt signal.
    """

    token_signal    = Signal(str)
    thinking_signal = Signal(str)
    mode_signal     = Signal(str)
    sources_signal  = Signal(dict)   # Fix Bug 6: was Signal(int)
    complete_signal = Signal(str)
    error_signal    = Signal(str)

    def __init__(self, agent, user_input: str, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.user_input = user_input

    def run(self):
        try:
            for update in self.agent.process_stream(self.user_input):
                t = update.get("type", "")
                if t == "token":
                    self.token_signal.emit(update.get("content", ""))
                elif t == "thinking":
                    self.thinking_signal.emit(update.get("message", ""))
                elif t == "mode":
                    self.mode_signal.emit(update.get("mode", ""))
                elif t == "sources":
                    self.sources_signal.emit(
                        update.get("data", {"count": 0, "sources": []})
                    )
                elif t == "complete":
                    self.complete_signal.emit(update.get("confidence", ""))
                elif t == "error":
                    self.error_signal.emit(update.get("message", "Unknown error"))
        except Exception as e:
            self.error_signal.emit(str(e))


class ToolWorker(QThread):
    """
    Worker for one-shot tool execution (used by workspace / v3 UI).

    Fix Bug 1: was defined twice in the original file. Single canonical
    definition here.
    """

    result_ready   = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, executor, tool_name: str, payload, parent=None):
        super().__init__(parent)
        self.executor  = executor
        self.tool_name = tool_name
        self.payload   = payload

    def run(self):
        try:
            result = self.executor.execute(self.tool_name, self.payload)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
