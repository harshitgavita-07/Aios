"""
Aios LLM worker — runs agent processing in a QThread so the UI never blocks.

v2: routes through the agent controller (memory + soulsync + planner + LLM)
instead of calling the LLM directly.
"""

from PySide6.QtCore import QThread, Signal

from core.agent import process as agent_process


class LLMWorker(QThread):
    """Background thread that streams agent tokens back to the UI."""

    token_received = Signal(str)
    generation_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        try:
            for token in agent_process(self.prompt):
                self.token_received.emit(token)
            self.generation_finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
