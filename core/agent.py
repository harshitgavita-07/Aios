"""
AIOS Agent Controller — unified v2/v3 orchestrator.

Fixes applied:
  - Removed duplicate module-level v1 agent code that was concatenated
    at the end of the file (caused SyntaxError: `self` in non-method scope).
  - Removed duplicate process_stream() definition (second one shadowed first).
  - Removed dangling references to `self.gstack` and bare `user_input` variable
    inside the old module-level _handle_system() function.
  - Fixed `from llm import LLMClient` -> `from core.llm import LLMClient`
    so the class-based LLM client in core/ is used, not the old module.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from .memory import MemoryStore
from .soulsync import SoulSync
from .planner import Planner, PlanStep
from .llm import LLMClient
from .context_manager import ContextManager
from .mode_controller import ModeController, AgentMode
from .confidence import ConfidenceScorer
from rag.pipeline import RAGPipeline

log = logging.getLogger("aios.agent")


class AgentController:
    """
    Central controller for the AIOS agent system.

    Pipeline:
        user input
            → SoulSync  (emotion + tone)
            → ModeController (chat / tool / web)
            → RAG / tool execution (optional)
            → ContextManager (build optimised prompt)
            → LLMClient  (generate / stream)
            → ConfidenceScorer
            → MemoryStore (save)
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)

        log.info("=" * 50)
        log.info("Initializing AIOS AgentController")
        log.info("=" * 50)

        self.memory = MemoryStore(self.data_dir)
        self.soulsync = SoulSync(self.data_dir)
        self.llm = LLMClient(self.data_dir)
        self.planner = Planner()
        self.context_manager = ContextManager(max_tokens=4096)
        self.mode_controller = ModeController()
        self.confidence_scorer = ConfidenceScorer()
        self.rag = RAGPipeline(self.data_dir)
        self.tool_executor = None

        # Optional gstack integration
        try:
            from gstack.aios_gstack import GStackRunner
            self.gstack = GStackRunner()
            log.info("gstack integration initialised")
        except ImportError:
            self.gstack = None

        log.info("AgentController initialisation complete")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_tool_executor(self, executor) -> None:
        self.tool_executor = executor
        self.planner.tool_registry = executor

    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle an inter-agent message (used by the v3 AgentMesh).
        Processes messages routed from the runtime layer.
        """
        msg_type = message.get("type", "")
        if msg_type == "llm_generation":
            prompt = message.get("prompt", "")
            if prompt:
                self.llm.generate(prompt)
        elif msg_type == "tool_execution":
            tool = message.get("tool", "")
            params = message.get("parameters", {})
            if tool and self.tool_executor:
                try:
                    self.tool_executor.execute(tool, params)
                except Exception as e:
                    log.error("Tool execution in handle_message failed: %s", e)
        else:
            log.debug("Unhandled message type in handle_message: %s", msg_type)

    def process(self, user_input: str, show_thinking: bool = True) -> Dict[str, Any]:
        """Synchronous full-pipeline processing. Returns result dict."""
        thinking_steps: List[Dict] = []

        def add_step(msg: str):
            thinking_steps.append({"step": len(thinking_steps) + 1, "message": msg})
            log.info("[Thinking] %s", msg)

        try:
            # Short-circuit for very short inputs
            text = user_input.strip()
            if len(text) < 3:
                response = random.choice([
                    "Hello! How can I help you today?",
                    "Hi there! What would you like to chat about?",
                    "Hey! I'm here to help. What's on your mind?",
                ])
                self.memory.add_message("assistant", response,
                                        metadata={"emotion": "neutral"})
                return {
                    "response": response,
                    "thinking_steps": [],
                    "confidence": None,
                    "mode": "chat",
                    "sources": [],
                    "emotion": "neutral",
                }

            self.memory.add_message("user", text)
            add_step("Received user input")

            emotion = self.soulsync.detect_emotion(text)
            add_step(f"Detected emotion: {emotion.dominant}")

            mode_decision = self.mode_controller.detect_mode(text)
            add_step(f"Mode: {mode_decision.mode.value} ({mode_decision.reasoning})")

            rag_results: List[Dict] = []
            web_results: List[Dict] = []
            tool_results: Dict = {}

            if mode_decision.requires_web:
                add_step("Researching web...")
                rag_results = self.rag.research(text)
                add_step(f"Found {len(rag_results)} relevant sources")
                web_results = [
                    {"content": r["content"], "source": r.get("url", "")}
                    for r in rag_results[:3]
                ]

            memory_rag = self.rag.query(text, use_web=False)
            if memory_rag:
                add_step(f"Retrieved {len(memory_rag)} items from knowledge base")
                rag_results.extend(memory_rag)

            if mode_decision.requires_tools and self.tool_executor:
                add_step("Executing tools...")
                intent = self.planner.detect_intent(text)
                plan = self.planner.create_plan(text, intent)
                if plan:
                    tool_results = self.planner.execute_plan(
                        plan,
                        tool_executor=self.tool_executor,
                        llm_client=self.llm,
                    )
                    add_step("Tool execution complete")

            add_step("Building context...")
            memory_context = self.memory.get_formatted_history(limit=10)
            tone_modifier = self.soulsync.get_system_prompt_modifier()
            system_prompt = self._build_system_prompt(tone_modifier)

            context = self.context_manager.build_context(
                user_query=text,
                memory_messages=memory_context,
                rag_results=rag_results,
                web_results=web_results,
                tool_results=tool_results,
                system_prompt=system_prompt,
            )

            add_step("Generating response...")
            response = self.llm.generate(text, system_prompt, context)

            sources = [r.get("source", "memory") for r in rag_results]
            confidence = self.confidence_scorer.score_response(
                response, sources, mode_decision.mode.value,
                has_rag=bool(rag_results), has_web=bool(web_results),
            )

            if confidence.should_fallback:
                response = self.confidence_scorer.get_fallback_response(
                    text, confidence)
                add_step(f"Low confidence ({confidence.level.value}), using fallback")
            else:
                add_step(f"Confidence: {confidence.level.value}")

            self.memory.add_message("assistant", response, metadata={
                "emotion": emotion.dominant,
                "mode": mode_decision.mode.value,
                "confidence": confidence.overall,
                "sources": sources[:3],
            })
            self.soulsync.learn_from_interaction(text, mode_decision.mode.value)

            return {
                "response": response,
                "thinking_steps": thinking_steps if show_thinking else [],
                "confidence": confidence,
                "mode": mode_decision.mode.value,
                "sources": sources[:3],
                "emotion": emotion.dominant,
            }

        except Exception as e:
            log.error("Error processing input: %s", e)
            return {
                "response": f"I encountered an error: {e}. Please try again.",
                "thinking_steps": thinking_steps,
                "confidence": None,
                "mode": "error",
                "sources": [],
                "emotion": "neutral",
            }

    def process_stream(self, user_input: str) -> Generator[Dict[str, Any], None, None]:
        """
        Stream processing: yields typed dicts consumed by StreamWorker in chat_ui.py.

        Yielded dict shapes:
          {"type": "thinking", "message": str}
          {"type": "mode",     "mode": str}
          {"type": "sources",  "data": {"count": int, "sources": list}}
          {"type": "token",    "content": str}
          {"type": "complete", "confidence": str}
          {"type": "error",    "message": str}
        """
        try:
            text = user_input.strip()
            if not text:
                return

            if len(text) < 3:
                response = random.choice([
                    "Hello! How can I help you today?",
                    "Hi there! What would you like to chat about?",
                    "Hey! I'm here to help. What's on your mind?",
                ])
                self.memory.add_message("assistant", response,
                                        metadata={"emotion": "neutral"})
                yield {"type": "token", "content": response}
                yield {"type": "complete", "confidence": "HIGH"}
                return

            yield {"type": "thinking", "message": "Analysing request..."}

            self.memory.add_message("user", text)
            emotion = self.soulsync.detect_emotion(text)
            mode_decision = self.mode_controller.detect_mode(text)

            yield {"type": "mode", "mode": mode_decision.mode.value}

            rag_results: List[Dict] = []
            web_results: List[Dict] = []

            if mode_decision.requires_web:
                yield {"type": "thinking", "message": "Searching web..."}
                rag_results = self.rag.research(text)
                yield {"type": "sources",
                       "data": {"count": len(rag_results),
                                "sources": rag_results[:5]}}
                web_results = [
                    {"content": r["content"],
                     "source": r.get("url", ""),
                     "title": r.get("title", "")}
                    for r in rag_results[:3]
                ]

            yield {"type": "thinking", "message": "Generating response..."}

            memory_context = self.memory.get_formatted_history(limit=10)
            tone_modifier = self.soulsync.get_system_prompt_modifier()
            system_prompt = self._build_system_prompt(tone_modifier)

            context = self.context_manager.build_context(
                user_query=text,
                memory_messages=memory_context,
                rag_results=rag_results,
                web_results=web_results,
                system_prompt=system_prompt,
            )

            full_response: List[str] = []
            for token in self.llm.generate_stream(text, system_prompt, context):
                full_response.append(token)
                yield {"type": "token", "content": token}

            complete_response = "".join(full_response)

            sources = [r.get("source", "memory") for r in rag_results]
            confidence = self.confidence_scorer.score_response(
                complete_response, sources, mode_decision.mode.value,
                has_rag=bool(rag_results), has_web=bool(web_results),
            )

            self.memory.add_message("assistant", complete_response, metadata={
                "emotion": emotion.dominant,
                "mode": mode_decision.mode.value,
                "confidence": confidence.overall,
                "sources": sources[:3],
            })

            yield {"type": "complete", "confidence": confidence.level.value}

        except Exception as e:
            log.error("Error in process_stream: %s", e)
            yield {"type": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, tone_modifier: str) -> str:
        base = (
            "You are AIOS, an advanced local AI assistant running on the user's machine. "
            "All processing is on-device — no data leaves this device. "
            "Be direct, honest, concise, and technically accurate. "
            "Use warm, constructive communication without excessive praise. "
            "If you don't know something, say so clearly."
        )
        return base + "\n\n" + tone_modifier

    def get_status(self) -> Dict[str, Any]:
        return {
            "model": self.llm.get_model(),
            "hardware": self.llm.get_hardware_info(),
            "memory_stats": self.memory.get_stats(),
            "rag_stats": self.rag.get_stats(),
            "emotion": self.soulsync.current_emotion.dominant,
            "profile": self.soulsync.profile.name or "not set",
        }

    def clear_conversation(self) -> None:
        self.memory.clear_thread()

    def set_user_name(self, name: str) -> None:
        self.soulsync.update_profile(name=name)
