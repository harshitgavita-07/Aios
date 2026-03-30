"""
UI Worker — Background task runner for non-blocking UI
"""

from PySide6.QtCore import QThread, Signal
from typing import Generator


class AgentWorker(QThread):
    """
    Background worker for agent processing.
    
    Change: Dedicated worker for agent processing
    Why:
    - Previous system used generic LLM worker
    - Agent processing has multiple stages
    Impact:
    - Cleaner separation of concerns
    - Better error handling per stage
    """
    
    token_received = Signal(str)
    response_complete = Signal(str)
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self, agent, user_input: str, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.user_input = user_input

    def run(self):
        try:
            # Stream tokens from the agent
            full_response = []
            for token in self.agent.process_stream(self.user_input):
                self.token_received.emit(token)
                full_response.append(token)
            
            complete = "".join(full_response)
            self.response_complete.emit(complete)
            
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
