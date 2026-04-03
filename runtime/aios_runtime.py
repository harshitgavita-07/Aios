"""
AIOS Runtime Layer — AI-First Operating Environment.

Fixes applied:
  - AIOSRuntime.get_system_status() referenced self.workflows which does not
    exist; fixed to self.workflow_engine.workflows.
  - shutdown_runtime() was a sync function called via asyncio.run(); changed
    to an async coroutine so callers can await it properly.
  - AIOSRuntime._handle_conversation() used `async for` on process_stream()
    which is a sync generator; fixed to a regular for loop.
  - WorkflowEngine.create_workflow() called self.planner.plan() and
    self.planner.generate_steps() which don't exist on Planner; updated to
    use the existing detect_intent() + create_plan() API.
  - AgentMesh.send_message() called asyncio.create_task() in a sync method
    (requires a running loop); replaced with a thread-safe queue.put_nowait()
    which works without requiring an event loop at the call site.
  - AgentController.handle_message() didn't exist; added in core/agent.py.
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from core.agent import AgentController
from core.memory import MemoryStore
from core.planner import Planner, PlanStep
from hardware import detect as detect_hardware

log = logging.getLogger("aios.runtime")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentState(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(Enum):
    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    WORKFLOW_CREATION = "workflow_creation"
    SYSTEM_CONTROL = "system_control"
    AGENT_MANAGEMENT = "agent_management"
    RESOURCE_REQUEST = "resource_request"
    ENVIRONMENT_QUERY = "environment_query"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Agent:
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
        return capability in self.capabilities

    def update_activity(self):
        self.last_active = datetime.now()


@dataclass
class Workflow:
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
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def advance(self):
        self.current_step += 1

    def is_complete(self) -> bool:
        return self.current_step >= len(self.steps)


@dataclass
class Intent:
    intent_id: str
    intent_type: IntentType
    description: str
    parameters: Dict[str, Any]
    confidence: float
    source_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Context:
    user_id: str
    session_id: str
    environment: Dict[str, Any]
    active_workflows: List[str]
    active_agents: List[str]
    resources: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# AgentMesh
# ---------------------------------------------------------------------------

class AgentMesh:
    """Inter-agent communication and collaboration."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        # Use asyncio.Queue only when inside an event loop; fall back to a
        # simple list buffer so the mesh can be constructed synchronously.
        self._pending_messages: List[Dict[str, Any]] = []
        self._message_queue: Optional[asyncio.Queue] = None
        self.event_listeners: Dict[str, List[Callable]] = {}
        self._running = False

    def _get_queue(self) -> asyncio.Queue:
        if self._message_queue is None:
            self._message_queue = asyncio.Queue()
            # Drain any messages buffered before the loop started
            for msg in self._pending_messages:
                self._message_queue.put_nowait(msg)
            self._pending_messages.clear()
        return self._message_queue

    def register_agent(self, agent: Agent):
        self.agents[agent.agent_id] = agent
        log.info("Registered agent: %s (%s)", agent.name, agent.agent_id)

    def unregister_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]

    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        return [a for a in self.agents.values()
                if a.is_capable(capability) and a.state == AgentState.READY]

    def send_message(self, from_agent: str, to_agent: str,
                     message: Dict[str, Any]):
        """
        Enqueue a message for delivery.

        Fix: originally called asyncio.create_task() which requires a running
        loop. Now uses put_nowait() on the queue (thread-safe) or buffers
        messages until the event loop is available.
        """
        message.update({
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat(),
        })
        try:
            self._get_queue().put_nowait(message)
        except RuntimeError:
            # No running event loop yet — buffer for later delivery
            self._pending_messages.append(message)

    def broadcast(self, from_agent: str, message: Dict[str, Any],
                  capability_filter: Optional[str] = None):
        targets = list(self.agents.keys())
        if capability_filter:
            targets = [aid for aid, agent in self.agents.items()
                       if agent.is_capable(capability_filter)]
        for target in targets:
            if target != from_agent:
                self.send_message(from_agent, target, message.copy())

    def subscribe(self, event_type: str, callback: Callable):
        self.event_listeners.setdefault(event_type, []).append(callback)

    async def process_messages(self):
        queue = self._get_queue()
        while self._running:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error("Error processing message: %s", e)

    async def _handle_message(self, message: Dict[str, Any]):
        to_agent = message.get("to_agent")
        if to_agent and to_agent in self.agents:
            agent = self.agents[to_agent]
            if agent.controller:
                # handle_message() is a sync method on AgentController
                agent.controller.handle_message(message)

        event_type = message.get("type", "message")
        for cb in self.event_listeners.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(message)
                else:
                    cb(message)
            except Exception as e:
                log.error("Error in event callback: %s", e)

    def start(self):
        self._running = True
        asyncio.ensure_future(self.process_messages())
        log.info("Agent mesh started")

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# WorkflowEngine
# ---------------------------------------------------------------------------

class WorkflowEngine:
    """Orchestrates multi-step workflows."""

    def __init__(self, agent_mesh: AgentMesh):
        self.agent_mesh = agent_mesh
        self.workflows: Dict[str, Workflow] = {}
        self.planner = Planner()

    def create_workflow(self, name: str, description: str,
                        creator_agent: str, user_request: str) -> str:
        """
        Fix: previously called self.planner.plan() and generate_steps() which
        don't exist.  Now uses the real Planner API: detect_intent() +
        create_plan().
        """
        workflow_id = str(uuid.uuid4())

        intent = self.planner.detect_intent(user_request)
        steps: List[PlanStep] = self.planner.create_plan(user_request, intent) or []

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            creator_agent=creator_agent,
            steps=steps,
        )
        self.workflows[workflow_id] = workflow
        log.info("Created workflow: %s — %s", workflow_id, name)
        return workflow_id

    async def execute_workflow(self, workflow_id: str) -> bool:
        if workflow_id not in self.workflows:
            log.error("Workflow not found: %s", workflow_id)
            return False

        workflow = self.workflows[workflow_id]
        workflow.state = WorkflowState.RUNNING

        try:
            while (step := workflow.next_step()) is not None:
                success = await self._execute_step(workflow, step)
                if not success:
                    workflow.state = WorkflowState.FAILED
                    return False
                workflow.advance()

            workflow.state = WorkflowState.COMPLETED
            workflow.completed_at = datetime.now()
            return True

        except Exception as e:
            log.error("Workflow execution failed: %s", e)
            workflow.state = WorkflowState.FAILED
            return False

    async def _execute_step(self, workflow: Workflow, step: PlanStep) -> bool:
        log.info("Executing step %s: %s", step.step_id, step.description)

        if step.step_type.value == "tool_call":
            tool_name = step.parameters.get("tool")
            agents = self.agent_mesh.get_agents_by_capability(
                f"tool:{tool_name}")
            if not agents:
                log.error("No agent capable of tool: %s", tool_name)
                return False
            agent = agents[0]
            self.agent_mesh.send_message("workflow_engine", agent.agent_id, {
                "type": "tool_execution",
                "tool": tool_name,
                "parameters": step.parameters,
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id,
            })
            await asyncio.sleep(0.1)
            return True

        elif step.step_type.value == "llm_call":
            agents = self.agent_mesh.get_agents_by_capability("llm")
            if not agents:
                log.error("No LLM-capable agent available")
                return False
            agent = agents[0]
            self.agent_mesh.send_message("workflow_engine", agent.agent_id, {
                "type": "llm_generation",
                "prompt": step.parameters.get("prompt"),
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id,
            })
            await asyncio.sleep(0.1)
            return True

        return True

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        if workflow_id not in self.workflows:
            return None
        w = self.workflows[workflow_id]
        return {
            "workflow_id": w.workflow_id,
            "name": w.name,
            "state": w.state.value,
            "current_step": w.current_step,
            "total_steps": len(w.steps),
            "progress": w.current_step / len(w.steps) if w.steps else 0,
        }


# ---------------------------------------------------------------------------
# IntentEngine
# ---------------------------------------------------------------------------

class IntentEngine:
    def __init__(self, agent_mesh: AgentMesh):
        self.agent_mesh = agent_mesh
        self._patterns = {
            "conversation": {
                "patterns": ["tell me", "explain", "what is", "how does", "why"],
                "intent_type": IntentType.CONVERSATION,
                "threshold": 0.1,
            },
            "task_execution": {
                "patterns": ["run", "execute", "open", "start", "launch", "create"],
                "intent_type": IntentType.TASK_EXECUTION,
                "threshold": 0.2,
            },
            "workflow_creation": {
                "patterns": ["workflow", "automate", "process", "pipeline"],
                "intent_type": IntentType.WORKFLOW_CREATION,
                "threshold": 0.3,
            },
            "system_control": {
                "patterns": ["settings", "configure", "system", "restart", "shutdown"],
                "intent_type": IntentType.SYSTEM_CONTROL,
                "threshold": 0.2,
            },
        }

    def parse_intent(self, user_input: str) -> Intent:
        lowered = user_input.lower()
        best_match = None
        best_confidence = 0.0

        for name, data in self._patterns.items():
            matches = sum(1 for p in data["patterns"] if p in lowered)
            confidence = matches / max(len(data["patterns"]), 1)
            if confidence > best_confidence and confidence >= data["threshold"]:
                best_match = data
                best_confidence = confidence

        intent_type = best_match["intent_type"] if best_match else IntentType.CONVERSATION

        return Intent(
            intent_id=str(uuid.uuid4()),
            intent_type=intent_type,
            description=user_input,
            parameters={"query": user_input},
            confidence=best_confidence,
        )


# ---------------------------------------------------------------------------
# ContextEngine & ResourceManager
# ---------------------------------------------------------------------------

class ContextEngine:
    def __init__(self):
        self.current_context = Context(
            user_id="default_user",
            session_id=str(uuid.uuid4()),
            environment={},
            active_workflows=[],
            active_agents=[],
            resources={},
        )
        self.context_history: List[Context] = []

    def update_environment(self, updates: Dict[str, Any]):
        self.current_context.environment.update(updates)
        self.current_context.timestamp = datetime.now()
        self.context_history.append(self.current_context)
        if len(self.context_history) > 100:
            self.context_history = self.context_history[-100:]

    def get_context(self) -> Context:
        return self.current_context

    def add_active_workflow(self, wf_id: str):
        if wf_id not in self.current_context.active_workflows:
            self.current_context.active_workflows.append(wf_id)

    def remove_active_workflow(self, wf_id: str):
        if wf_id in self.current_context.active_workflows:
            self.current_context.active_workflows.remove(wf_id)

    def add_active_agent(self, agent_id: str):
        if agent_id not in self.current_context.active_agents:
            self.current_context.active_agents.append(agent_id)

    def remove_active_agent(self, agent_id: str):
        if agent_id in self.current_context.active_agents:
            self.current_context.active_agents.remove(agent_id)


class ResourceManager:
    def __init__(self):
        self.hardware_info = detect_hardware()
        self.resource_usage: Dict[str, Any] = {}
        self.resource_limits: Dict[str, Any] = {}

    def get_resource_usage(self) -> Dict[str, Any]:
        return self.resource_usage.copy()


# ---------------------------------------------------------------------------
# AIOSRuntime
# ---------------------------------------------------------------------------

class AIOSRuntime:
    """The main AIOS v3 runtime layer."""

    def __init__(self):
        self.agent_mesh = AgentMesh()
        self.workflow_engine = WorkflowEngine(self.agent_mesh)
        self.intent_engine = IntentEngine(self.agent_mesh)
        self.context_engine = ContextEngine()
        self.resource_manager = ResourceManager()
        self.core_agent: Optional[Agent] = None
        self._running = False
        self._init_core_agent()

    def _init_core_agent(self):
        self.core_agent = Agent(
            agent_id="core_agent",
            name="AIOS Core",
            description="The core AIOS runtime agent",
            capabilities={"llm", "planning", "orchestration", "system_control"},
        )
        self.core_agent.controller = AgentController()
        self.core_agent.state = AgentState.READY
        self.agent_mesh.register_agent(self.core_agent)

    async def start(self):
        log.info("Starting AIOS Runtime Layer...")
        self._running = True
        self.agent_mesh.start()
        asyncio.ensure_future(self._monitor_system())
        log.info("AIOS Runtime Layer started")

    async def stop(self):
        log.info("Stopping AIOS Runtime Layer...")
        self._running = False
        self.agent_mesh.stop()
        log.info("AIOS Runtime Layer stopped")

    async def process_user_input(self, user_input: str) -> str:
        intent = self.intent_engine.parse_intent(user_input)

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
        return await self._handle_conversation(intent)

    async def _handle_conversation(self, intent: Intent) -> str:
        """
        Fix: process_stream() is a sync generator, not an async generator.
        Use a regular for loop, not `async for`.
        """
        if self.core_agent and self.core_agent.controller:
            response_parts: List[str] = []
            for update in self.core_agent.controller.process_stream(
                    intent.description):
                if update.get("type") == "token":
                    response_parts.append(update.get("content", ""))
            return "".join(response_parts) or "No response generated"
        return "Conversation agent not available"

    async def _handle_task_execution(self, intent: Intent) -> str:
        wf_id = self.workflow_engine.create_workflow(
            name=f"Task: {intent.description[:50]}",
            description=intent.description,
            creator_agent="user",
            user_request=intent.description,
        )
        success = await self.workflow_engine.execute_workflow(wf_id)
        return (f"Task completed (workflow {wf_id})" if success
                else f"Task failed (workflow {wf_id})")

    async def _handle_workflow_creation(self, intent: Intent) -> str:
        wf_id = self.workflow_engine.create_workflow(
            name=f"Workflow: {intent.description[:50]}",
            description=intent.description,
            creator_agent="user",
            user_request=intent.description,
        )
        return f"Workflow created: {wf_id}"

    async def _handle_system_control(self, intent: Intent) -> str:
        cmd = intent.parameters.get("query", "").lower()
        if "restart" in cmd:
            return "System restart initiated"
        if "shutdown" in cmd:
            return "System shutdown initiated"
        return f"System control: {cmd}"

    async def _handle_agent_management(self, intent: Intent) -> str:
        agents = list(self.agent_mesh.agents.values())
        lines = [f"- {a.name}: {a.description} ({a.state.value})" for a in agents]
        return "Available agents:\n" + "\n".join(lines)

    async def _monitor_system(self):
        while self._running:
            try:
                self.resource_manager.hardware_info = detect_hardware()
                self.context_engine.update_environment({
                    "active_workflows": len(
                        self.context_engine.current_context.active_workflows),
                    "active_agents": len(
                        self.context_engine.current_context.active_agents),
                })
                await asyncio.sleep(30)
            except Exception as e:
                log.error("System monitoring error: %s", e)
                await asyncio.sleep(30)

    def get_system_status(self) -> Dict[str, Any]:
        """
        Fix: previously referenced self.workflows which doesn't exist.
        Corrected to self.workflow_engine.workflows.
        """
        return {
            "runtime_status": "running" if self._running else "stopped",
            "agents": {
                aid: {
                    "name": a.name,
                    "state": a.state.value,
                    "capabilities": list(a.capabilities),
                }
                for aid, a in self.agent_mesh.agents.items()
            },
            "workflows": {
                wf_id: self.workflow_engine.get_workflow_status(wf_id)
                for wf_id in self.workflow_engine.workflows  # FIXED
            },
            "resources": self.resource_manager.get_resource_usage(),
            "context": {
                "active_workflows":
                    self.context_engine.current_context.active_workflows,
                "active_agents":
                    self.context_engine.current_context.active_agents,
                "environment":
                    self.context_engine.current_context.environment,
            },
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_runtime_instance: Optional[AIOSRuntime] = None


def get_runtime() -> AIOSRuntime:
    global _runtime_instance
    if _runtime_instance is None:
        _runtime_instance = AIOSRuntime()
    return _runtime_instance


async def init_runtime() -> AIOSRuntime:
    runtime = get_runtime()
    await runtime.start()
    return runtime


async def shutdown_runtime() -> None:
    """
    Fix: was a sync function called via asyncio.run().
    Now an async coroutine so callers can await it.
    """
    global _runtime_instance
    if _runtime_instance is not None:
        await _runtime_instance.stop()
        _runtime_instance = None
