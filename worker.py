"""
Aios LLM worker — runs inference in a QThread so the UI never blocks.
"""

from PySide6.QtCore import QThread, Signal

from llm import ask_llm_stream


class LLMWorker(QThread):
    """Background thread that streams LLM tokens back to the UI."""

    token_received = Signal(str)
    generation_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        try:
            for token in ask_llm_stream(self.prompt):
                self.token_received.emit(token)
            self.generation_finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
