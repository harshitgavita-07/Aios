"""
Aios Core — Local AI Runtime
Modular agent system with memory, emotion, and tool execution.
"""

__version__ = "2.0.0"

from .agent import AgentController
from .memory import MemoryStore
from .soulsync import SoulSync
from .planner import Planner
from llm import LLMClient

__all__ = ["AgentController", "MemoryStore", "SoulSync", "Planner", "LLMClient"]
