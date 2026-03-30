"""
Agent Controller — Main orchestrator for AIOS
Coordinates memory, emotion, planning, tools, and LLM.
"""

import logging
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path

from .memory import MemoryStore
from .soulsync import SoulSync
from .planner import Planner, PlanStep
from .llm import LLMClient

log = logging.getLogger("aios.agent")


class AgentController:
    """
    Central controller for the AIOS agent system.
    
    Flow:
    User Input → Agent Controller → SoulSync (emotion + profile)
              → Memory (context) → Planner (intent + plan)
              → Tool Executor (if needed) → LLM → Response
    
    Change: Modular agent architecture
    Why:
    - Previous system was linear with no separation of concerns
    - Needed extensible architecture for new capabilities
    Impact:
    - Clean separation of responsibilities
    - Easy to extend with new features
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize core components
        log.info("Initializing AgentController...")
        
        # Memory system
        self.memory = MemoryStore(self.data_dir)
        log.info("MemoryStore initialized")
        
        # SoulSync (emotional intelligence)
        self.soulsync = SoulSync(self.data_dir)
        log.info("SoulSync initialized")
        
        # LLM client
        self.llm = LLMClient(self.data_dir)
        log.info("LLMClient initialized")
        
        # Planner
        self.planner = Planner()
        log.info("Planner initialized")
        
        # Tool executor (set later)
        self.tool_executor = None
        
        log.info("AgentController initialization complete")

    def set_tool_executor(self, executor):
        """Set the tool executor for the agent."""
        self.tool_executor = executor
        self.planner.tool_registry = executor

    def process(self, user_input: str) -> str:
        """
        Process user input and return response.
        
        Change: Unified processing pipeline
        Why:
        - Previous system had no orchestration layer
        - Needed single entry point for all requests
        Impact:
        - Consistent processing flow
        - Better error handling
        """
        try:
            # 1. Save user message to memory
            self.memory.add_message("user", user_input)
            
            # 2. Detect emotion
            emotion = self.soulsync.detect_emotion(user_input)
            log.debug(f"Detected emotion: {emotion.dominant}")
            
            # 3. Detect intent and create plan
            intent = self.planner.detect_intent(user_input)
            log.debug(f"Detected intent: {intent['primary']}")
            
            # 4. Get plan if needed
            plan = self.planner.create_plan(user_input, intent)
            
            # 5. Execute plan or direct response
            if plan:
                log.info(f"Executing plan with {len(plan)} steps")
                plan_result = self.planner.execute_plan(
                    plan, 
                    tool_executor=self.tool_executor,
                    llm_client=self.llm
                )
                
                # Build response from plan execution
                if plan_result.get("completed"):
                    response = self._synthesize_plan_result(plan_result, user_input)
                else:
                    response = self._handle_plan_failure(plan_result)
            else:
                # Direct chat response
                response = self._generate_chat_response(user_input)
            
            # 6. Save assistant response to memory
            self.memory.add_message("assistant", response, metadata={
                "emotion": emotion.dominant,
                "intent": intent["primary"]
            })
            
            # 7. Learn from interaction
            self.soulsync.learn_from_interaction(user_input, intent["primary"])
            
            return response
            
        except Exception as e:
            log.error(f"Error processing input: {e}")
            return f"I encountered an error: {str(e)}. Please try again."

    def process_stream(self, user_input: str) -> Generator[str, None, None]:
        """
        Process user input and yield streaming response.
        
        Change: Streaming support for real-time UI
        Why:
        - Previous system blocked UI during generation
        - Streaming improves perceived responsiveness
        Impact:
        - Real-time token display
        - Better user experience
        """
        try:
            # 1. Save user message
            self.memory.add_message("user", user_input)
            
            # 2. Detect emotion and intent
            emotion = self.soulsync.detect_emotion(user_input)
            intent = self.planner.detect_intent(user_input)
            
            # 3. Get context from memory
            context = self.memory.get_formatted_history(limit=10)
            
            # 4. Build system prompt with SoulSync guidance
            tone_modifier = self.soulsync.get_system_prompt_modifier()
            system_prompt = self._build_system_prompt(tone_modifier)
            
            # 5. Stream response
            full_response = []
            for token in self.llm.generate_stream(user_input, system_prompt, context):
                full_response.append(token)
                yield token
            
            # 6. Save complete response to memory
            complete_response = "".join(full_response)
            self.memory.add_message("assistant", complete_response, metadata={
                "emotion": emotion.dominant,
                "intent": intent["primary"],
                "streamed": True
            })
            
            # 7. Learn from interaction
            self.soulsync.learn_from_interaction(user_input, intent["primary"])
            
        except Exception as e:
            log.error(f"Error in streaming: {e}")
            yield f"\n[Error: {str(e)}]"

    def _generate_chat_response(self, user_input: str) -> str:
        """Generate a direct chat response."""
        # Get context from memory
        context = self.memory.get_formatted_history(limit=10)
        
        # Build system prompt
        tone_modifier = self.soulsync.get_system_prompt_modifier()
        system_prompt = self._build_system_prompt(tone_modifier)
        
        # Generate response
        return self.llm.generate(user_input, system_prompt, context)

    def _build_system_prompt(self, tone_modifier: str) -> str:
        """Build system prompt with SoulSync guidance."""
        base_prompt = (
            "You are Aios, a helpful local AI desktop assistant. "
            "Be concise, accurate, and friendly. All processing happens "
            "on the user's machine — no data leaves this device. "
            "You can execute tools and remember context from previous messages."
        )
        return base_prompt + tone_modifier

    def _synthesize_plan_result(self, plan_result: Dict, original_input: str) -> str:
        """Synthesize plan execution results into a response."""
        results = plan_result.get("results", {})
        
        # Check if we have tool results to synthesize
        tool_results = []
        for step_id, result_data in results.items():
            if result_data.get("success"):
                result = result_data.get("result", {})
                if isinstance(result, dict) and "tool" in result:
                    tool_results.append(result)
        
        if tool_results:
            # Synthesize tool results
            synthesis_prompt = f"""The user asked: "{original_input}"

I executed the following tools:
{self._format_tool_results(tool_results)}

Provide a clear, helpful response based on these results."""
            
            return self.llm.generate(synthesis_prompt)
        
        return "I've completed the requested task."

    def _handle_plan_failure(self, plan_result: Dict) -> str:
        """Handle plan execution failure."""
        results = plan_result.get("results", {})
        
        # Find first failure
        for step_id, result_data in results.items():
            if not result_data.get("success", False):
                error = result_data.get("error", "Unknown error")
                return f"I couldn't complete that task. Error: {error}"
        
        return "I encountered an issue while processing your request."

    def _format_tool_results(self, tool_results: List[Dict]) -> str:
        """Format tool results for synthesis."""
        lines = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", "")
            lines.append(f"- {tool_name}: {tool_result}")
        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status summary."""
        return {
            "model": self.llm.get_model(),
            "hardware": self.llm.get_hardware_info(),
            "memory_stats": self.memory.get_stats(),
            "emotion": self.soulsync.current_emotion.dominant,
            "profile": self.soulsync.profile.name or "not set",
        }

    def get_memory_context(self, limit: int = 5) -> List[Dict]:
        """Get recent memory context."""
        return self.memory.get_formatted_history(limit=limit)

    def clear_conversation(self):
        """Clear current conversation thread."""
        self.memory.clear_thread()

    def set_user_name(self, name: str):
        """Set user's name in profile."""
        self.soulsync.update_profile(name=name)

    def set_preferred_tone(self, tone: str):
        """Set preferred tone in profile."""
        self.soulsync.update_profile(preferred_tone=tone)
