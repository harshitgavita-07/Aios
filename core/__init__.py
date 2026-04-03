"""
AIOS Core — Local AI Runtime
Modular agent system with memory, emotion, and tool execution.

Fix: changed `from llm import LLMClient` to `from .llm import LLMClient`
     so the class-based LLMClient in core/llm.py is used, not the old
     module-level llm.py at the repo root.
"""

__version__ = "2.0.0"

from .agent import AgentController
from .memory import MemoryStore
from .soulsync import SoulSync
from .planner import Planner
from .llm import LLMClient

__all__ = ["AgentController", "MemoryStore", "SoulSync", "Planner", "LLMClient"]
