"""
Shared types and data structures for AIOS.

All core data models used across the Digital Coworker platform.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime


class IntentDomain(str, Enum):
    """Domains of user intents."""
    BROWSER = "browser"
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    GITHUB = "github"
    DOCKER = "docker"
    EMAIL = "email"
    CALENDAR = "calendar"
    SLACK = "slack"
    NOTION = "notion"
    LINEAR = "linear"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    GENERAL = "general"


class TaskStatus(str, Enum):
    """Status of a task step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Intent:
    """
    Represents a parsed user intent.
    
    Attributes:
        goal: The user's stated objective
        domain: The domain this intent belongs to
        confidence: Confidence score (0.0-1.0)
        requires_approval: Whether human approval is needed
        required_plugins: List of plugins needed for execution
        context_references: Related context from memory
        priority: Execution priority (1-10)
        estimated_complexity: Complexity estimate (1-10)
    """
    goal: str
    domain: IntentDomain = IntentDomain.GENERAL
    confidence: float = 0.0
    requires_approval: bool = False
    required_plugins: list[str] = field(default_factory=list)
    context_references: list[str] = field(default_factory=list)
    priority: int = 5
    estimated_complexity: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStep:
    """
    A single step in an execution plan.
    
    Attributes:
        id: Unique identifier for this step
        description: Human-readable description
        action: Action type (navigate, click, run, etc.)
        parameters: Action parameters
        dependencies: IDs of steps this depends on
        plugin: Target plugin for execution
        timeout: Maximum execution time in seconds
        retry_count: Number of retries on failure
        status: Current execution status
    """
    id: str
    description: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    plugin: str = "browser"
    timeout: int = 30
    retry_count: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ExecutionPlan:
    """
    Complete execution plan for an intent.
    
    Attributes:
        intent_id: Reference to the originating intent
        steps: Ordered list of task steps
        parallel_groups: Groups of steps that can run in parallel
        recovery_plan: Alternative steps if primary fails
        estimated_duration: Estimated total duration in seconds
        risk_level: Overall risk assessment
        checkpoints: Steps where state should be saved
    """
    intent_id: str
    steps: list[TaskStep] = field(default_factory=list)
    parallel_groups: list[list[str]] = field(default_factory=list)
    recovery_plan: list[TaskStep] = field(default_factory=list)
    estimated_duration: int = 60
    risk_level: RiskLevel = RiskLevel.LOW
    checkpoints: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """
    Result of verifying an executed action.
    
    Attributes:
        success: Whether verification passed
        confidence: Confidence in the verification (0.0-1.0)
        evidence: Supporting evidence for the result
        checks_performed: List of verification checks run
        failures: Details of any failed checks
        suggestions: Recovery suggestions if failed
    """
    success: bool
    confidence: float = 0.0
    evidence: dict[str, Any] = field(default_factory=dict)
    checks_performed: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=datetime.now)


@dataclass
class ActionResult:
    """
    Result of executing an action.
    
    Attributes:
        action_id: Reference to the executed step
        success: Whether execution succeeded
        data: Result data from the action
        error: Error message if failed
        duration_ms: Execution duration in milliseconds
        verification: Verification result
    """
    action_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    verification: Optional[VerificationResult] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowTemplate:
    """
    Reusable workflow template.
    
    Attributes:
        id: Unique template identifier
        name: Human-readable name
        description: Template description
        steps: Template steps with placeholders
        triggers: Events that can trigger this workflow
        variables: Required variables for execution
    """
    id: str
    name: str
    description: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    category: str = "general"
    version: str = "1.0.0"


@dataclass
class PluginManifest:
    """
    Plugin metadata and capabilities.
    
    Attributes:
        name: Plugin name
        version: Plugin version
        description: Plugin description
        capabilities: Actions this plugin can perform
        permissions: Required permissions
        dependencies: Other required plugins
    """
    name: str
    version: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    author: str = ""
    health: str = "healthy"
    enabled: bool = True


@dataclass
class Workspace:
    """
    Project workspace context.
    
    Attributes:
        id: Unique workspace identifier
        name: Workspace name
        root_path: Filesystem root path
        configuration: Workspace-specific settings
        active_tasks: Currently running tasks
    """
    id: str
    name: str
    root_path: str
    configuration: dict[str, Any] = field(default_factory=dict)
    active_tasks: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    """
    User session with context and history.
    
    Attributes:
        id: Unique session identifier
        workspace_id: Associated workspace
        tasks: Task history in this session
        memory_refs: References to relevant memories
        started_at: Session start time
    """
    id: str
    workspace_id: Optional[str] = None
    tasks: list[str] = field(default_factory=list)
    memory_refs: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class Event:
    """
    System event for observability.
    
    Attributes:
        type: Event type
        source: Component that emitted the event
        payload: Event data
        timestamp: When the event occurred
    """
    type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    severity: str = "info"
