"""
Agent Controller — Main orchestrator for AIOS
Coordinates memory, emotion, planning, tools, RAG, and LLM.
"""

import logging
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path

from .memory import MemoryStore
from .soulsync import SoulSync
from .planner import Planner, PlanStep
from .llm import LLMClient
from .context_manager import ContextManager
from .mode_controller import ModeController, AgentMode
from .confidence import ConfidenceScorer

# Import RAG
from rag.pipeline import RAGPipeline

log = logging.getLogger("aios.agent")


class AgentController:
    """
    Central controller for the AIOS agent system v2.
    
    Flow:
    User Input → Agent Controller → Mode Detection → [Memory-RAG | Web-RAG | Tools]
              → SoulSync → Context Manager → LLM → Confidence Check → Response
    
    Change: Enhanced agent with RAG, Context Manager, and Confidence
    Why:
    - Previous system lacked knowledge retrieval
    - Context window needed intelligent management
    - Response quality needed verification
    Impact:
    - Research capability
    - Optimal context usage
    - Quality guarantees
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        log.info("=" * 50)
        log.info("Initializing AIOS Agent Controller v2")
        log.info("=" * 50)
        
        # Initialize core components
        self.memory = MemoryStore(self.data_dir)
        self.soulsync = SoulSync(self.data_dir)
        self.llm = LLMClient(self.data_dir)
        self.planner = Planner()
        self.context_manager = ContextManager(max_tokens=4096)
        self.mode_controller = ModeController()
        self.confidence_scorer = ConfidenceScorer()
        
        # Initialize RAG pipeline
        self.rag = RAGPipeline(self.data_dir)
        
        # Tool executor (set later)
        self.tool_executor = None
        
        log.info("AgentController initialization complete")

    def set_tool_executor(self, executor):
        """Set the tool executor for the agent."""
        self.tool_executor = executor
        self.planner.tool_registry = executor

    def process(self, user_input: str, 
                show_thinking: bool = True) -> Dict[str, Any]:
        """
        Process user input with full pipeline.
        
        Change: Enhanced processing with thinking steps
        Why:
        - Users want transparency on processing
        - Shows what's happening behind the scenes
        - Better for debugging
        Impact:
        - Transparent processing
        - Better user understanding
        """
        thinking_steps = []
        
        def add_step(step: str):
            thinking_steps.append({"step": len(thinking_steps) + 1, "message": step})
            log.info(f"[Thinking] {step}")
        
        try:
            # Step 1: Save user message
            self.memory.add_message("user", user_input)
            add_step("Received user input")
            
            # Step 2: Detect emotion
            emotion = self.soulsync.detect_emotion(user_input)
            add_step(f"Detected emotion: {emotion.dominant}")
            
            # Step 3: Detect mode
            mode_decision = self.mode_controller.detect_mode(user_input)
            add_step(f"Mode: {mode_decision.mode.value} ({mode_decision.reasoning})")
            
            # Step 4: Gather knowledge based on mode
            rag_results = []
            web_results = []
            tool_results = []
            
            if mode_decision.requires_web:
                add_step("🔍 Researching web...")
                rag_results = self.rag.research(user_input)
                add_step(f"Found {len(rag_results)} relevant sources")
                web_results = [{"content": r["content"], "source": r.get("url", "")} 
                              for r in rag_results[:3]]
            
            # Retrieve from local memory/knowledge
            memory_rag = self.rag.query(user_input, use_web=False)
            if memory_rag:
                add_step(f"📚 Retrieved {len(memory_rag)} items from knowledge base")
                rag_results.extend(memory_rag)
            
            if mode_decision.requires_tools and self.tool_executor:
                add_step("🔧 Executing tools...")
                intent = self.planner.detect_intent(user_input)
                plan = self.planner.create_plan(user_input, intent)
                if plan:
                    plan_result = self.planner.execute_plan(
                        plan, 
                        tool_executor=self.tool_executor,
                        llm_client=self.llm
                    )
                    tool_results = plan_result
                    add_step("Tool execution complete")
            
            # Step 5: Build optimized context
            add_step("🧠 Building context...")
            memory_context = self.memory.get_formatted_history(limit=10)
            
            tone_modifier = self.soulsync.get_system_prompt_modifier()
            system_prompt = self._build_system_prompt(tone_modifier)
            
            context = self.context_manager.build_context(
                user_query=user_input,
                memory_messages=memory_context,
                rag_results=rag_results,
                web_results=web_results,
                system_prompt=system_prompt
            )
            
            # Step 6: Generate response
            add_step("✍️ Generating response...")
            response = self.llm.generate(user_input, system_prompt, context)
            
            # Step 7: Score confidence
            sources = [r.get("source", "memory") for r in rag_results]
            confidence = self.confidence_scorer.score_response(
                response, 
                sources, 
                mode_decision.mode.value,
                has_rag=bool(rag_results),
                has_web=bool(web_results)
            )
            
            if confidence.should_fallback:
                response = self.confidence_scorer.get_fallback_response(user_input, confidence)
                add_step(f"⚠️ Low confidence ({confidence.level.value}), using fallback")
            else:
                add_step(f"✓ Confidence: {confidence.level.value}")
            
            # Step 8: Save response
            self.memory.add_message("assistant", response, metadata={
                "emotion": emotion.dominant,
                "mode": mode_decision.mode.value,
                "confidence": confidence.overall,
                "sources": sources[:3]
            })
            
            # Learn from interaction
            self.soulsync.learn_from_interaction(user_input, mode_decision.mode.value)
            
            return {
                "response": response,
                "thinking_steps": thinking_steps if show_thinking else [],
                "confidence": confidence,
                "mode": mode_decision.mode.value,
                "sources": sources[:3],
                "emotion": emotion.dominant
            }
            
        except Exception as e:
            log.error(f"Error processing input: {e}")
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "thinking_steps": thinking_steps,
                "confidence": None,
                "mode": "error",
                "sources": [],
                "emotion": "neutral"
            }

    def process_stream(self, user_input: str) -> Generator[Dict[str, Any], None, None]:
        """
        Process user input and yield streaming updates.
        
        Change: Streaming with thinking steps
        Why:
        - Users want real-time progress
        - Shows what's happening
        - Better for long operations
        Impact:
        - Real-time transparency
        - Better perceived performance
        """
        try:
            yield {"type": "thinking", "message": "Analyzing request..."}
            
            # Save and detect
            self.memory.add_message("user", user_input)
            emotion = self.soulsync.detect_emotion(user_input)
            mode_decision = self.mode_controller.detect_mode(user_input)
            
            yield {"type": "mode", "mode": mode_decision.mode.value}
            
            # Gather knowledge
            rag_results = []
            web_results = []
            
            if mode_decision.requires_web:
                yield {"type": "thinking", "message": "🔍 Searching web..."}
                rag_results = self.rag.research(user_input)
                yield {"type": "sources", "count": len(rag_results)}
                web_results = [{"content": r["content"], "source": r.get("url", "")} 
                              for r in rag_results[:3]]
            
            # Build context and generate
            yield {"type": "thinking", "message": "🧠 Generating response..."}
            
            memory_context = self.memory.get_formatted_history(limit=10)
            tone_modifier = self.soulsync.get_system_prompt_modifier()
            system_prompt = self._build_system_prompt(tone_modifier)
            
            context = self.context_manager.build_context(
                user_query=user_input,
                memory_messages=memory_context,
                rag_results=rag_results,
                web_results=web_results,
                system_prompt=system_prompt
            )
            
            # Stream tokens
            full_response = []
            for token in self.llm.generate_stream(user_input, system_prompt, context):
                full_response.append(token)
                yield {"type": "token", "content": token}
            
            complete_response = "".join(full_response)
            
            # Score and save
            sources = [r.get("source", "memory") for r in rag_results]
            confidence = self.confidence_scorer.score_response(
                complete_response, sources, mode_decision.mode.value,
                has_rag=bool(rag_results), has_web=bool(web_results)
            )
            
            self.memory.add_message("assistant", complete_response, metadata={
                "emotion": emotion.dominant,
                "mode": mode_decision.mode.value,
                "confidence": confidence.overall,
                "sources": sources[:3]
            })
            
            yield {"type": "complete", "confidence": confidence.level.value}
            
        except Exception as e:
            log.error(f"Error in streaming: {e}")
            yield {"type": "error", "message": str(e)}

    def _build_system_prompt(self, tone_modifier: str) -> str:
        """Build system prompt with SoulSync guidance."""
        base_prompt = (
            "You are Aios, a helpful local AI assistant with memory, reasoning, and research capabilities. "
            "Be concise, accurate, and friendly. When using web sources, cite them clearly. "
            "If you don't know something, say so rather than making up information. "
            "All processing happens on your machine — no data leaves this device."
        )
        return base_prompt + tone_modifier

    def get_status(self) -> Dict[str, Any]:
        """Get agent status summary."""
        return {
            "model": self.llm.get_model(),
            "hardware": self.llm.get_hardware_info(),
            "memory_stats": self.memory.get_stats(),
            "rag_stats": self.rag.get_stats(),
            "emotion": self.soulsync.current_emotion.dominant,
            "profile": self.soulsync.profile.name or "not set",
        }

    def clear_conversation(self):
        """Clear current conversation thread."""
        self.memory.clear_thread()

    def set_user_name(self, name: str):
        """Set user's name in profile."""
        self.soulsync.update_profile(name=name)

    def set_research_mode(self, enabled: bool):
        """Toggle research mode."""
        # This can be used to force web search
        pass
