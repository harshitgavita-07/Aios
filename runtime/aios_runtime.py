"""
AIOS Runtime Layer — AI-First Operating Environment

The core runtime that transforms AIOS from an AI assistant into an AI-native operating system.
This layer provides the foundation for agent-based computing where AI agents are the fundamental
"applications" and workflows are the primary interaction paradigm.

Architecture Overview:
- Agent Mesh: Inter-agent communication and collaboration
- Workflow Engine: Complex task orchestration
- Context Engine: Environment awareness and adaptation
- Intent Engine: Natural language to action translation
- Resource Manager: Hardware/software resource orchestration
- Workspace Manager: AI-native desktop environment
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json

from core.agent import AgentController
from core.memory import MemoryStore
from core.planner import Planner, PlanStep
from hardware import detect as detect_hardware

log = logging.getLogger("aios.runtime")


class AgentState(Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class WorkflowState(Enum):
    """Workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(Enum):
    """Types of user intents."""
    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    WORKFLOW_CREATION = "workflow_creation"
    SYSTEM_CONTROL = "system_control"
    AGENT_MANAGEMENT = "agent_management"
    RESOURCE_REQUEST = "resource_request"
    ENVIRONMENT_QUERY = "environment_query"


@dataclass
class Agent:
    """An AI agent in the AIOS runtime."""
    agent_id: str
    name: str
    description: str
    capabilities: Set[str]
    state: AgentState = AgentState.INITIALIZING
    controller: Optional[AgentController] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None

    def is_capable(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def update_activity(self):
        """Update last active timestamp."""
        self.last_active = datetime.now()


@dataclass
class Workflow:
    """A workflow in the AIOS runtime."""
    workflow_id: str
    name: str
    description: str
    creator_agent: str
    steps: List[PlanStep]
    state: WorkflowState = WorkflowState.PENDING
    current_step: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def next_step(self) -> Optional[PlanStep]:
        """Get the next step to execute."""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def advance(self):
        """Move to the next step."""
        self.current_step += 1

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_step >= len(self.steps)


@dataclass
class Intent:
    """A user intent in the AIOS runtime."""
    intent_id: str
    intent_type: IntentType
    description: str
    parameters: Dict[str, Any]
    confidence: float
    source_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Context:
    """Runtime context information."""
    user_id: str
    session_id: str
    environment: Dict[str, Any]
    active_workflows: List[str]
    active_agents: List[str]
    resources: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class AgentMesh:
    """
    Inter-agent communication and collaboration system.

    Enables agents to discover, communicate, and collaborate with each other.
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.event_listeners: Dict[str, List[Callable]] = {}
        self._running = False

    def register_agent(self, agent: Agent):
        """Register an agent in the mesh."""
        self.agents[agent.agent_id] = agent
        log.info(f"Registered agent: {agent.name} ({agent.agent_id})")

    def unregister_agent(self, agent_id: str):
        """Remove an agent from the mesh."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            log.info(f"Unregistered agent: {agent_id}")

    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """Find agents with a specific capability."""
        return [agent for agent in self.agents.values()
                if agent.is_capable(capability) and agent.state == AgentState.READY]

    def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Send a message between agents."""
        message.update({
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat()
        })
        asyncio.create_task(self.message_queue.put(message))

    def broadcast(self, from_agent: str, message: Dict[str, Any], capability_filter: Optional[str] = None):
        """Broadcast a message to all agents (optionally filtered by capability)."""
        targets = self.agents.keys()
        if capability_filter:
            targets = [aid for aid, agent in self.agents.items()
                      if agent.is_capable(capability_filter)]

        for target in targets:
            if target != from_agent:
                self.send_message(from_agent, target, message.copy())

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to agent mesh events."""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)

    async def process_messages(self):
        """Process messages in the queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error(f"Error processing message: {e}")

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle an individual message."""
        to_agent = message.get("to_agent")
        if to_agent and to_agent in self.agents:
            agent = self.agents[to_agent]
            if agent.controller:
                # Log the message (handle_message dispatching happens via process_stream)
                log.debug(f"Message routed to agent {to_agent}: {message.get('type', 'unknown')}")

        # Notify event listeners
        event_type = message.get("type", "message")
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    await callback(message)
                except Exception as e:
                    log.error(f"Error in event callback: {e}")

    def start(self):
        """Start the agent mesh."""
        self._running = True
        asyncio.create_task(self.process_messages())
        log.info("Agent mesh started")

    def stop(self):
        """Stop the agent mesh."""
        self._running = False
        log.info("Agent mesh stopped")


class WorkflowEngine:
    """
    Orchestrates complex multi-step workflows across agents.
    """

    def __init__(self, agent_mesh: AgentMesh):
        self.agent_mesh = agent_mesh
        self.workflows: Dict[str, Workflow] = {}
        self.planner = Planner()

    def create_workflow(self, name: str, description: str, creator_agent: str,
                       user_request: str) -> str:
        """Create a new workflow from a user request."""
        workflow_id = str(uuid.uuid4())

        # Generate execution plan
        intent = self.planner.detect_intent(user_request)
        steps = self.planner.create_plan(user_request, intent) or []

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            creator_agent=creator_agent,
            steps=steps
        )

        self.workflows[workflow_id] = workflow
        log.info(f"Created workflow: {workflow_id} - {name}")

        return workflow_id

    async def execute_workflow(self, workflow_id: str) -> bool:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            log.error(f"Workflow not found: {workflow_id}")
            return False

        workflow = self.workflows[workflow_id]
        workflow.state = WorkflowState.RUNNING

        try:
            while step := workflow.next_step():
                success = await self._execute_step(workflow, step)
                if not success:
                    workflow.state = WorkflowState.FAILED
                    return False

                workflow.advance()

            workflow.state = WorkflowState.COMPLETED
            workflow.completed_at = datetime.now()
            return True

        except Exception as e:
            log.error(f"Workflow execution failed: {e}")
            workflow.state = WorkflowState.FAILED
            return False

    async def _execute_step(self, workflow: Workflow, step: PlanStep) -> bool:
        """Execute a single workflow step."""
        log.info(f"Executing step {step.step_id}: {step.description}")

        if step.step_type == "tool_call":
            # Find agent capable of this tool
            tool_name = step.parameters.get("tool")
            agents = self.agent_mesh.get_agents_by_capability(f"tool:{tool_name}")

            if not agents:
                log.error(f"No agent capable of tool: {tool_name}")
                return False

            # Send tool execution request
            agent = agents[0]  # Use first available
            message = {
                "type": "tool_execution",
                "tool": tool_name,
                "parameters": step.parameters,
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id
            }

            self.agent_mesh.send_message("workflow_engine", agent.agent_id, message)

            # Wait for completion (simplified - in real impl would use promises/futures)
            await asyncio.sleep(1)
            return True

        elif step.step_type == "llm_call":
            # Find LLM-capable agent
            agents = self.agent_mesh.get_agents_by_capability("llm")

            if not agents:
                log.error("No LLM-capable agent available")
                return False

            agent = agents[0]
            message = {
                "type": "llm_generation",
                "prompt": step.parameters.get("prompt"),
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id
            }

            self.agent_mesh.send_message("workflow_engine", agent.agent_id, message)
            await asyncio.sleep(1)
            return True

        return True

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "state": workflow.state.value,
            "current_step": workflow.current_step,
            "total_steps": len(workflow.steps),
            "progress": workflow.current_step / len(workflow.steps) if workflow.steps else 0
        }


class IntentEngine:
    """
    Translates natural language into structured intents and actions.
    """

    def __init__(self, agent_mesh: AgentMesh):
        self.agent_mesh = agent_mesh
        self.intent_patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load intent recognition patterns."""
        return {
            "conversation": {
                "patterns": ["tell me", "explain", "what is", "how does", "why"],
                "intent_type": IntentType.CONVERSATION,
                "confidence_threshold": 0.7
            },
            "task_execution": {
                "patterns": ["run", "execute", "open", "start", "launch", "create"],
                "intent_type": IntentType.TASK_EXECUTION,
                "confidence_threshold": 0.8
            },
            "workflow_creation": {
                "patterns": ["workflow", "automate", "process", "pipeline"],
                "intent_type": IntentType.WORKFLOW_CREATION,
                "confidence_threshold": 0.9
            },
            "system_control": {
                "patterns": ["settings", "configure", "system", "restart", "shutdown"],
                "intent_type": IntentType.SYSTEM_CONTROL,
                "confidence_threshold": 0.8
            },
            "agent_management": {
                "patterns": ["agent", "create agent", "manage", "deploy"],
                "intent_type": IntentType.AGENT_MANAGEMENT,
                "confidence_threshold": 0.8
            }
        }

    def parse_intent(self, user_input: str) -> Intent:
        """Parse user input into a structured intent."""
        user_input_lower = user_input.lower()

        best_match = None
        best_confidence = 0.0

        for pattern_name, pattern_data in self.intent_patterns.items():
            confidence = self._calculate_confidence(user_input_lower, pattern_data["patterns"])

            if confidence > best_confidence and confidence >= pattern_data["confidence_threshold"]:
                best_match = pattern_data
                best_confidence = confidence

        if best_match:
            intent_type = best_match["intent_type"]
        else:
            intent_type = IntentType.CONVERSATION  # Default fallback

        return Intent(
            intent_id=str(uuid.uuid4()),
            intent_type=intent_type,
            description=user_input,
            parameters=self._extract_parameters(user_input, intent_type),
            confidence=best_confidence
        )

    def _calculate_confidence(self, text: str, patterns: List[str]) -> float:
        """Calculate confidence score for intent matching."""
        matches = sum(1 for pattern in patterns if pattern in text)
        return min(matches / len(patterns), 1.0) if patterns else 0.0

    def _extract_parameters(self, text: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extract parameters from user input based on intent type."""
        # Simplified parameter extraction - would be more sophisticated in real implementation
        if intent_type == IntentType.TASK_EXECUTION:
            # Extract command-like parameters
            return {"command": text}
        elif intent_type == IntentType.WORKFLOW_CREATION:
            return {"description": text}
        else:
            return {"query": text}


class ContextEngine:
    """
    Maintains awareness of the runtime environment and user context.
    """

    def __init__(self):
        self.current_context = Context(
            user_id="default_user",
            session_id=str(uuid.uuid4()),
            environment={},
            active_workflows=[],
            active_agents=[],
            resources={}
        )
        self.context_history: List[Context] = []

    def update_environment(self, updates: Dict[str, Any]):
        """Update environment information."""
        self.current_context.environment.update(updates)
        self.current_context.timestamp = datetime.now()
        self._save_context_snapshot()

    def get_context(self) -> Context:
        """Get current context."""
        return self.current_context

    def add_active_workflow(self, workflow_id: str):
        """Add an active workflow."""
        if workflow_id not in self.current_context.active_workflows:
            self.current_context.active_workflows.append(workflow_id)

    def remove_active_workflow(self, workflow_id: str):
        """Remove a completed workflow."""
        if workflow_id in self.current_context.active_workflows:
            self.current_context.active_workflows.remove(workflow_id)

    def add_active_agent(self, agent_id: str):
        """Add an active agent."""
        if agent_id not in self.current_context.active_agents:
            self.current_context.active_agents.append(agent_id)

    def remove_active_agent(self, agent_id: str):
        """Remove an inactive agent."""
        if agent_id in self.current_context.active_agents:
            self.current_context.active_agents.remove(agent_id)

    def _save_context_snapshot(self):
        """Save a snapshot of the current context."""
        self.context_history.append(self.current_context)
        # Keep only last 100 snapshots
        if len(self.context_history) > 100:
            self.context_history = self.context_history[-100:]


class ResourceManager:
    """
    Manages hardware and software resources in the AIOS runtime.
    """

    def __init__(self):
        self.hardware_info = detect_hardware()
        self.resource_usage: Dict[str, Any] = {}
        self.resource_limits: Dict[str, Any] = {}

    def allocate_resource(self, resource_type: str, amount: Any) -> bool:
        """Allocate a system resource."""
        # Simplified resource allocation - would check limits in real implementation
        current = self.resource_usage.get(resource_type, 0)
        self.resource_usage[resource_type] = current + amount
        return True

    def release_resource(self, resource_type: str, amount: Any):
        """Release a system resource."""
        current = self.resource_usage.get(resource_type, 0)
        self.resource_usage[resource_type] = max(0, current - amount)

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        return self.resource_usage.copy()

    def check_resource_availability(self, resource_type: str, amount: Any) -> bool:
        """Check if a resource is available."""
        limit = self.resource_limits.get(resource_type)
        if limit is None:
            return True  # No limit set

        current = self.resource_usage.get(resource_type, 0)
        return current + amount <= limit


class AIOSRuntime:
    """
    The main AIOS runtime layer - the AI-native operating environment.
    """

    def __init__(self):
        self.agent_mesh = AgentMesh()
        self.workflow_engine = WorkflowEngine(self.agent_mesh)
        self.intent_engine = IntentEngine(self.agent_mesh)
        self.context_engine = ContextEngine()
        self.resource_manager = ResourceManager()

        self.core_agent: Optional[Agent] = None
        self._running = False

        # Initialize core components
        self._init_core_agent()

    def _init_core_agent(self):
        """Initialize the core AIOS agent."""
        self.core_agent = Agent(
            agent_id="core_agent",
            name="AIOS Core",
            description="The core AIOS runtime agent",
            capabilities={"llm", "planning", "orchestration", "system_control"}
        )

        # Create agent controller
        self.core_agent.controller = AgentController()

        # Register with mesh
        self.agent_mesh.register_agent(self.core_agent)

    async def start(self):
        """Start the AIOS runtime."""
        log.info("Starting AIOS Runtime Layer...")

        self._running = True
        self.agent_mesh.start()

        # Start background tasks
        asyncio.create_task(self._monitor_system())
        asyncio.create_task(self._process_intents())

        log.info("AIOS Runtime Layer started successfully")

    async def stop(self):
        """Stop the AIOS runtime."""
        log.info("Stopping AIOS Runtime Layer...")

        self._running = False
        self.agent_mesh.stop()

        log.info("AIOS Runtime Layer stopped")

    async def process_user_input(self, user_input: str) -> str:
        """Process user input through the AIOS runtime."""
        # Parse intent
        intent = self.intent_engine.parse_intent(user_input)

        # Route based on intent type
        if intent.intent_type == IntentType.CONVERSATION:
            return await self._handle_conversation(intent)
        elif intent.intent_type == IntentType.TASK_EXECUTION:
            return await self._handle_task_execution(intent)
        elif intent.intent_type == IntentType.WORKFLOW_CREATION:
            return await self._handle_workflow_creation(intent)
        elif intent.intent_type == IntentType.SYSTEM_CONTROL:
            return await self._handle_system_control(intent)
        elif intent.intent_type == IntentType.AGENT_MANAGEMENT:
            return await self._handle_agent_management(intent)
        else:
            return await self._handle_conversation(intent)  # Default fallback

    async def _handle_conversation(self, intent: Intent) -> str:
        """Handle conversational intents."""
        if self.core_agent and self.core_agent.controller:
            # Use core agent for conversation
            response = ""
            async for token in self.core_agent.controller.process_stream(intent.description):
                if token["type"] == "token":
                    response += token["content"]
            return response
        return "Conversation agent not available"

    async def _handle_task_execution(self, intent: Intent) -> str:
        """Handle task execution intents."""
        # Create a simple workflow for the task
        workflow_id = self.workflow_engine.create_workflow(
            name=f"Task: {intent.description[:50]}",
            description=intent.description,
            creator_agent="user",
            user_request=intent.description
        )

        # Execute the workflow
        success = await self.workflow_engine.execute_workflow(workflow_id)

        if success:
            return f"Task completed successfully (Workflow: {workflow_id})"
        else:
            return f"Task execution failed (Workflow: {workflow_id})"

    async def _handle_workflow_creation(self, intent: Intent) -> str:
        """Handle workflow creation intents."""
        workflow_id = self.workflow_engine.create_workflow(
            name=f"Custom Workflow: {intent.description[:50]}",
            description=intent.description,
            creator_agent="user",
            user_request=intent.description
        )

        return f"Workflow created: {workflow_id}. Use workflow commands to manage it."

    async def _handle_system_control(self, intent: Intent) -> str:
        """Handle system control intents."""
        # Simplified system control - would be more sophisticated
        command = intent.parameters.get("command", "").lower()

        if "restart" in command:
            return "System restart initiated"
        elif "shutdown" in command:
            return "System shutdown initiated"
        elif "settings" in command:
            return "Opening system settings..."
        else:
            return f"System control: {command}"

    async def _handle_agent_management(self, intent: Intent) -> str:
        """Handle agent management intents."""
        # List available agents
        agents = list(self.agent_mesh.agents.values())
        agent_info = "\n".join([f"- {agent.name}: {agent.description} ({agent.state.value})"
                               for agent in agents])

        return f"Available agents:\n{agent_info}"

    async def _monitor_system(self):
        """Monitor system resources and health."""
        while self._running:
            try:
                # Update hardware info
                self.resource_manager.hardware_info = detect_hardware()

                # Update context
                self.context_engine.update_environment({
                    "cpu_usage": "unknown",  # Would implement actual monitoring
                    "memory_usage": "unknown",
                    "active_workflows": len(self.context_engine.current_context.active_workflows),
                    "active_agents": len(self.context_engine.current_context.active_agents)
                })

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                log.error(f"System monitoring error: {e}")
                await asyncio.sleep(30)

    async def _process_intents(self):
        """Process queued intents."""
        # This would handle background intent processing
        # For now, it's a placeholder
        pass

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "runtime_status": "running" if self._running else "stopped",
            "agents": {
                agent_id: {
                    "name": agent.name,
                    "state": agent.state.value,
                    "capabilities": list(agent.capabilities)
                }
                for agent_id, agent in self.agent_mesh.agents.items()
            },
            "workflows": {
                wf_id: self.workflow_engine.get_workflow_status(wf_id)
                for wf_id in self.workflow_engine.workflows.keys()
            },
            "resources": self.resource_manager.get_resource_usage(),
            "context": {
                "active_workflows": self.context_engine.current_context.active_workflows,
                "active_agents": self.context_engine.current_context.active_agents,
                "environment": self.context_engine.current_context.environment
            }
        }


# Global runtime instance
_runtime_instance: Optional[AIOSRuntime] = None


def get_runtime() -> AIOSRuntime:
    """Get the global AIOS runtime instance."""
    global _runtime_instance
    if _runtime_instance is None:
        _runtime_instance = AIOSRuntime()
    return _runtime_instance


async def init_runtime():
    """Initialize and start the AIOS runtime."""
    runtime = get_runtime()
    await runtime.start()
    return runtime


async def shutdown_runtime():
    """Shutdown the AIOS runtime."""
    global _runtime_instance
    if _runtime_instance:
        await _runtime_instance.stop()
        _runtime_instance = None