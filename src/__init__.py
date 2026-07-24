"""
AIOS - AI Native Digital Coworker

A desktop-native digital coworker that understands intent, plans work,
delegates execution, verifies results, and collaborates naturally with humans.

Architecture:
- AIOS: Intent, Planning, Decision Making, Memory, Coordination
- SCR Runtime: Execution (Browser, Desktop, Filesystem, Terminal)
- Desktop Studio: Replay, Metrics, Timeline, Inspector, Developer Tools
"""

__version__ = "1.0.0-beta"
__author__ = "AIOS Contributors"
__license__ = "MIT"

from .shared.types import (
    Intent,
    TaskStep,
    ExecutionPlan,
    VerificationResult,
    ActionResult,
    WorkflowTemplate,
    PluginManifest,
    Workspace,
    Session,
    Event,
)

from .orchestrator.intent_engine import IntentEngine
from .orchestrator.planning_engine import PlanningEngine
from .orchestrator.verification_engine import VerificationEngine

__all__ = [
    "__version__",
    "Intent",
    "TaskStep",
    "ExecutionPlan",
    "VerificationResult",
    "ActionResult",
    "WorkflowTemplate",
    "PluginManifest",
    "Workspace",
    "Session",
    "Event",
    "IntentEngine",
    "PlanningEngine",
    "VerificationEngine",
]
