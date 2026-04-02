"""
Planner — Task decomposition and execution planning
Generates simple plans for complex user requests.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("aios.planner")


class StepType(Enum):
    """Types of planning steps."""
    THINK = "think"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    USER_CONFIRM = "user_confirm"
    OUTPUT = "output"


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    step_id: int
    step_type: StepType
    description: str
    parameters: Dict[str, Any]
    dependencies: List[int] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Planner:
    """
    Simple task planner for breaking down user requests.
    
    Features:
    - Intent-based plan generation
    - Tool dependency tracking
    - Execution ordering
    
    Change: Added planning layer
    Why:
    - Previous system had no execution planning
    - Complex tasks need decomposition
    Impact:
    - Enables multi-step task execution
    - Better handling of complex requests
    """

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry
        log.info("Planner initialized")

    def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from input.
        
        Change: Rule-based intent detection
        Why:
        - Need to route between chat and execution
        - Enables appropriate response strategy
        Impact:
        - Better task handling
        - Appropriate tool selection
        """
        text = user_input.lower()
        
        # Intent patterns
        intents = {
            "chat": [
                r"^(hi|hello|hey|how are you|what's up|good morning|good evening)",
                r"(explain|tell me about|what is|how does|why)",
                r"(write|create|generate|draft|help me with)",
            ],
            "execute": [
                r"(run|execute|calculate|compute|find|search|get)",
                r"(open|launch|start|close|kill)",
                r"(create file|write file|read file|delete file)",
            ],
            "system": [
                r"(system info|cpu|memory|disk|gpu|hardware)",
                r"(clear|reset|restart|status)",
            ],
        }
        
        import re
        scores = {}
        for intent, patterns in intents.items():
            score = sum(1 for p in patterns if re.search(p, text))
            if score > 0:
                scores[intent] = score
        
        if not scores:
            detected_intent = "chat"
            confidence = 0.5
        else:
            detected_intent = max(scores, key=scores.get)
            confidence = min(scores[detected_intent] / 2, 1.0)
        
        # Check for tool-specific keywords
        tool_keywords = {
            "think": ["think", "reason", "analyze", "consider"],
            "calculator": ["calculate", "compute", "math", "sum", "multiply"],
            "file": ["file", "read", "write", "create", "delete"],
            "shell": ["run", "execute", "command", "terminal"],
            "open_application": ["open", "launch", "start", "run", "application", "browser", "youtube"],
        }
        
        suggested_tools = []
        for tool, keywords in tool_keywords.items():
            if any(kw in text for kw in keywords):
                suggested_tools.append(tool)
        
        return {
            "primary": detected_intent,
            "confidence": confidence,
            "suggested_tools": suggested_tools,
            "requires_planning": detected_intent == "execute" or len(suggested_tools) > 0,
        }

    def create_plan(self, user_input: str, intent: Dict[str, Any]) -> Optional[List[PlanStep]]:
        """
        Create an execution plan based on intent.
        
        Change: Dynamic plan generation
        Why:
        - Complex tasks need structured execution
        - Enables tool orchestration
        Impact:
        - Systematic task completion
        - Error handling at step level
        """
        if not intent.get("requires_planning", False):
            # Simple chat - no plan needed
            return None
        
        steps = []
        step_id = 1
        
        # Add thinking step for complex requests
        if intent["primary"] == "execute":
            steps.append(PlanStep(
                step_id=step_id,
                step_type=StepType.THINK,
                description="Analyze the request and determine approach",
                parameters={"input": user_input, "intent": intent}
            ))
            step_id += 1
        
        # Add tool execution steps
        for tool_name in intent.get("suggested_tools", []):
            steps.append(PlanStep(
                step_id=step_id,
                step_type=StepType.TOOL_CALL,
                description=f"Execute {tool_name} tool",
                parameters={"tool": tool_name, "input": user_input},
                dependencies=[s.step_id for s in steps]
            ))
            step_id += 1
        
        # Add LLM synthesis step if tools were called
        if steps:
            steps.append(PlanStep(
                step_id=step_id,
                step_type=StepType.LLM_CALL,
                description="Synthesize results into final response",
                parameters={"context": "tool_results"},
                dependencies=[s.step_id for s in steps]
            ))
        
        log.info(f"Created plan with {len(steps)} steps for intent: {intent['primary']}")
        return steps

    def execute_plan(self, plan: List[PlanStep], 
                     tool_executor=None,
                     llm_client=None) -> Dict[str, Any]:
        """
        Execute a generated plan.
        
        Change: Plan execution engine
        Why:
        - Plans need to be executed step by step
        - Dependencies must be respected
        Impact:
        - Reliable multi-step execution
        - Observable progress
        """
        results = {}
        
        for step in plan:
            log.debug(f"Executing step {step.step_id}: {step.step_type.value}")
            
            try:
                if step.step_type == StepType.THINK:
                    result = self._execute_think(step)
                elif step.step_type == StepType.TOOL_CALL:
                    result = self._execute_tool(step, tool_executor)
                elif step.step_type == StepType.LLM_CALL:
                    result = self._execute_llm(step, llm_client, results)
                elif step.step_type == StepType.OUTPUT:
                    result = step.parameters.get("content", "")
                else:
                    result = {"error": f"Unknown step type: {step.step_type}"}
                
                results[step.step_id] = {
                    "success": True,
                    "result": result,
                    "step": step
                }
                
            except Exception as e:
                log.error(f"Step {step.step_id} failed: {e}")
                results[step.step_id] = {
                    "success": False,
                    "error": str(e),
                    "step": step
                }
                # Continue with remaining steps
        
        return {
            "completed": all(r.get("success", False) for r in results.values()),
            "results": results,
            "step_count": len(plan)
        }

    def _execute_think(self, step: PlanStep) -> Dict:
        """Execute a thinking step."""
        return {
            "analysis": f"Analyzed: {step.parameters.get('input', '')}",
            "approach": "Using suggested tools and LLM synthesis"
        }

    def _execute_tool(self, step: PlanStep, tool_executor) -> Dict:
        """Execute a tool call step."""
        if not tool_executor:
            return {"error": "No tool executor available"}
        
        tool_name = step.parameters.get("tool")
        tool_input = step.parameters.get("input", "")
        
        # Parse tool input based on tool type
        payload = self._parse_tool_payload(tool_name, tool_input)
        
        try:
            result = tool_executor.execute(tool_name, payload)
            return {"tool": tool_name, "result": result}
        except Exception as e:
            return {"tool": tool_name, "error": str(e)}

    def _parse_tool_payload(self, tool_name: str, user_input: str) -> Any:
        """Parse user input into appropriate payload for the tool."""
        text = user_input.lower()
        
        if tool_name == "open_application":
            # Extract what to open from user input
            # Look for common targets
            targets = {
                "youtube": ["youtube", "yt"],
                "browser": ["browser", "chrome", "firefox", "edge"],
                "notepad": ["notepad", "editor", "text"],
                "calculator": ["calculator", "calc"],
                "explorer": ["explorer", "file explorer", "files"],
            }
            
            for target, keywords in targets.items():
                if any(kw in text for kw in keywords):
                    return {"target": target}
            
            # If no specific target found, try to extract from text
            # Look for URLs or application names
            import re
            url_match = re.search(r'(https?://[^\s]+)', user_input)
            if url_match:
                return {"target": url_match.group(1)}
            
            # Default to trying the whole input as target
            return {"target": user_input.strip()}
            
        elif tool_name == "run_command":
            # Extract command from user input
            command = user_input.replace("run command", "").replace("execute", "").strip()
            return {"command": command}
            
        elif tool_name == "take_screenshot":
            # Optional filename
            filename = None
            if "as" in text or "named" in text:
                # Try to extract filename
                pass
            return {"filename": filename}
            
        elif tool_name == "file_read":
            # Extract file path
            path = user_input.replace("read file", "").replace("open file", "").strip()
            return {"path": path}
            
        elif tool_name == "file_write":
            # This is more complex - would need content extraction
            return {"error": "File writing requires specific path and content"}
            
        elif tool_name == "calculator":
            # Extract expression
            expression = user_input.replace("calculate", "").replace("compute", "").strip()
            return {"expression": expression}
            
        else:
            # For unknown tools, pass the input as-is
            return user_input

    def _execute_llm(self, step: PlanStep, llm_client, previous_results: Dict) -> str:
        """Execute an LLM synthesis step."""
        if not llm_client:
            return "LLM synthesis not available"
        
        # Build context from previous results
        context = json.dumps(previous_results, indent=2)
        prompt = f"""Synthesize the following execution results into a helpful response:

{context}

Provide a clear, concise answer based on these results."""
        
        return llm_client.generate(prompt)

    def format_plan(self, plan: List[PlanStep]) -> str:
        """Format plan for display."""
        lines = ["📋 Execution Plan:"]
        for step in plan:
            deps = f" (depends on: {step.dependencies})" if step.dependencies else ""
            lines.append(f"  {step.step_id}. [{step.step_type.value}] {step.description}{deps}")
        return "\n".join(lines)
