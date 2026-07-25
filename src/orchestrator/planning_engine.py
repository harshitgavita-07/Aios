"""
Planning Engine for AIOS Digital Coworker.

Converts structured intents into executable plans with task steps,
dependencies, parallel execution groups, and recovery strategies.
"""

import uuid
from datetime import datetime
from typing import Optional
from ..shared.types import (
    Intent,
    IntentDomain,
    ExecutionPlan,
    TaskStep,
    TaskStatus,
    RiskLevel,
    WorkflowTemplate,
)


class PlanningEngine:
    """
    Generates execution plans from user intents.
    
    The Planning Engine breaks down high-level goals into concrete,
    executable steps with proper ordering, dependencies, and fallback strategies.
    
    Features:
    - Template-based planning for common workflows
    - Dependency resolution for step ordering
    - Parallel execution group identification
    - Automatic recovery plan generation
    - Risk assessment and checkpoint placement
    
    Example:
        >>> engine = PlanningEngine()
        >>> intent = Intent(goal="Open github.com", domain=IntentDomain.BROWSER)
        >>> plan = engine.create_plan(intent)
        >>> len(plan.steps)
        1
    """
    
    # Pre-defined workflow templates
    WORKFLOW_TEMPLATES: dict[str, WorkflowTemplate] = {
        "open_url": WorkflowTemplate(
            id="open_url",
            name="Open URL",
            description="Navigate to a specific URL in the browser",
            steps=[
                {
                    "id": "navigate",
                    "action": "navigate",
                    "plugin": "browser",
                    "parameters": {"url": "{{url}}"},
                }
            ],
            variables=["url"],
            category="browser",
        ),
        "git_clone": WorkflowTemplate(
            id="git_clone",
            name="Clone Repository",
            description="Clone a Git repository to local filesystem",
            steps=[
                {
                    "id": "clone",
                    "action": "clone",
                    "plugin": "git",
                    "parameters": {"repository": "{{repository}}", "path": "{{path}}"},
                },
                {
                    "id": "verify",
                    "action": "verify_exists",
                    "plugin": "filesystem",
                    "parameters": {"path": "{{path}}"},
                }
            ],
            variables=["repository", "path"],
            category="git",
        ),
        "publish_npm": WorkflowTemplate(
            id="publish_npm",
            name="Publish npm Package",
            description="Build and publish an npm package",
            steps=[
                {
                    "id": "check_status",
                    "action": "run",
                    "plugin": "terminal",
                    "parameters": {"command": "git status"},
                },
                {
                    "id": "install",
                    "action": "run",
                    "plugin": "terminal",
                    "parameters": {"command": "npm install"},
                },
                {
                    "id": "test",
                    "action": "run",
                    "plugin": "terminal",
                    "parameters": {"command": "npm test"},
                },
                {
                    "id": "build",
                    "action": "run",
                    "plugin": "terminal",
                    "parameters": {"command": "npm run build"},
                },
                {
                    "id": "publish",
                    "action": "run",
                    "plugin": "terminal",
                    "parameters": {"command": "npm publish"},
                },
                {
                    "id": "verify",
                    "action": "verify_published",
                    "plugin": "browser",
                    "parameters": {"package": "{{package_name}}"},
                }
            ],
            variables=["package_name"],
            category="deployment",
        ),
    }
    
    def __init__(self) -> None:
        """Initialize the Planning Engine."""
        self._templates = self.WORKFLOW_TEMPLATES.copy()
    
    def create_plan(
        self,
        intent: Intent,
        context: Optional[dict] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan from an intent.
        
        Args:
            intent: Parsed user intent
            context: Optional context with workspace info, history, etc.
            
        Returns:
            ExecutionPlan with ordered steps and recovery strategy
            
        Example:
            >>> engine = PlanningEngine()
            >>> intent = Intent(goal="Open https://example.com")
            >>> plan = engine.create_plan(intent)
            >>> plan.steps[0].action
            'navigate'
        """
        # Try to match a template
        template = self._match_template(intent)
        
        if template:
            plan = self._plan_from_template(intent, template, context)
        else:
            plan = self._plan_from_intent(intent, context)
        
        # Add risk assessment
        plan.risk_level = self._assess_risk(intent, plan)
        
        # Add checkpoints for high-risk operations
        plan.checkpoints = self._identify_checkpoints(plan)
        
        # Generate recovery plan
        plan.recovery_plan = self._generate_recovery_plan(plan)
        
        return plan
    
    def _match_template(self, intent: Intent) -> Optional[WorkflowTemplate]:
        """Match an intent to a workflow template."""
        goal_lower = intent.goal.lower()
        
        # URL navigation
        if any(word in goal_lower for word in ["open", "navigate", "go to"]):
            if "http" in goal_lower or ".com" in goal_lower or ".org" in goal_lower:
                return self._templates.get("open_url")
        
        # Git clone
        if "clone" in goal_lower and ("repo" in goal_lower or "github" in goal_lower):
            return self._templates.get("git_clone")
        
        # npm publish
        if any(word in goal_lower for word in ["publish", "release"]) and "npm" in goal_lower:
            return self._templates.get("publish_npm")
        
        return None
    
    def _plan_from_template(
        self,
        intent: Intent,
        template: WorkflowTemplate,
        context: Optional[dict]
    ) -> ExecutionPlan:
        """Create a plan from a workflow template."""
        steps = []
        variables = self._extract_variables(intent, template.variables, context)
        
        for step_template in template.steps:
            parameters = self._fill_parameters(
                step_template.get("parameters", {}),
                variables
            )
            
            step = TaskStep(
                id=step_template["id"],
                description=self._generate_description(step_template, variables),
                action=step_template["action"],
                parameters=parameters,
                plugin=step_template.get("plugin", "browser"),
                timeout=self._estimate_timeout(step_template),
            )
            steps.append(step)
        
        # Set up dependencies
        for i in range(1, len(steps)):
            steps[i].dependencies = [steps[i-1].id]
        
        return ExecutionPlan(
            intent_id=str(uuid.uuid4()),
            steps=steps,
            estimated_duration=sum(s.timeout for s in steps),
            metadata={
                "template_id": template.id,
                "template_name": template.name,
            }
        )
    
    def _plan_from_intent(
        self,
        intent: Intent,
        context: Optional[dict]
    ) -> ExecutionPlan:
        """Create a generic plan from an intent without template match."""
        steps = []
        
        # Default browser navigation for general intents
        if intent.domain.value in ["browser", "general"]:
            step = TaskStep(
                id=str(uuid.uuid4())[:8],
                description=f"Execute browser action for: {intent.goal}",
                action="execute",
                parameters={"goal": intent.goal},
                plugin="browser",
                timeout=30,
            )
            steps.append(step)
        elif intent.domain == IntentDomain.GIT:
            step = TaskStep(
                id=str(uuid.uuid4())[:8],
                description=f"Execute git operation: {intent.goal}",
                action="execute",
                parameters={"operation": intent.goal},
                plugin="git",
                timeout=60,
            )
            steps.append(step)
        elif intent.domain == IntentDomain.TERMINAL:
            step = TaskStep(
                id=str(uuid.uuid4())[:8],
                description=f"Execute terminal command: {intent.goal}",
                action="execute",
                parameters={"command": intent.goal},
                plugin="terminal",
                timeout=60,
            )
            steps.append(step)
        else:
            # Generic step for unknown domains
            step = TaskStep(
                id=str(uuid.uuid4())[:8],
                description=f"Execute: {intent.goal}",
                action="execute",
                parameters={"intent": intent.goal},
                plugin=intent.required_plugins[0] if intent.required_plugins else "browser",
                timeout=30,
            )
            steps.append(step)
        
        return ExecutionPlan(
            intent_id=str(uuid.uuid4()),
            steps=steps,
            estimated_duration=sum(s.timeout for s in steps),
            metadata={"plan_type": "generic"}
        )
    
    def _extract_variables(
        self,
        intent: Intent,
        variable_names: list[str],
        context: Optional[dict]
    ) -> dict[str, str]:
        """Extract variable values from intent and context."""
        variables = {}
        goal_lower = intent.goal.lower()
        
        # Extract URL
        if "url" in variable_names:
            import re
            url_match = re.search(r'(https?://[\w.-]+)', intent.goal)
            if url_match:
                variables["url"] = url_match.group(1)
            else:
                # Try to extract domain
                domain_match = re.search(r'([\w.-]+\.(com|org|io|net|dev))', intent.goal)
                if domain_match:
                    variables["url"] = f"https://{domain_match.group(1)}"
        
        # Extract repository
        if "repository" in variable_names:
            import re
            repo_match = re.search(r'(github\.com/[\w/-]+)', intent.goal)
            if repo_match:
                variables["repository"] = f"https://{repo_match.group(1)}.git"
        
        # Extract path
        if "path" in variable_names and context:
            if "workspace" in context:
                variables["path"] = context["workspace"]
        
        # Extract package name
        if "package_name" in variable_names:
            import re
            pkg_match = re.search(r'npm\s+(?:publish\s+)?(@?[\w/-]+)', intent.goal)
            if pkg_match:
                variables["package_name"] = pkg_match.group(1)
        
        return variables
    
    def _fill_parameters(
        self,
        parameters: dict,
        variables: dict[str, str]
    ) -> dict:
        """Fill template parameters with extracted variables."""
        filled = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    value = value.replace(f"{{{{{var_name}}}}}", var_value)
            filled[key] = value
        return filled
    
    def _generate_description(
        self,
        step_template: dict,
        variables: dict[str, str]
    ) -> str:
        """Generate human-readable step description."""
        action = step_template.get("action", "execute")
        plugin = step_template.get("plugin", "unknown")
        
        descriptions = {
            "navigate": f"Navigate to {variables.get('url', 'URL')}",
            "clone": f"Clone repository to {variables.get('path', 'target path')}",
            "verify_exists": "Verify directory exists",
            "run": f"Run command in {plugin}",
            "verify_published": f"Verify package {variables.get('package_name', '')} is published",
            "execute": f"Execute {action} in {plugin}",
        }
        
        return descriptions.get(action, f"{action.title()} in {plugin}")
    
    def _estimate_timeout(self, step_template: dict) -> int:
        """Estimate timeout for a step based on action type."""
        action = step_template.get("action", "execute")
        
        timeouts = {
            "navigate": 30,
            "clone": 120,
            "verify_exists": 5,
            "run": 60,
            "verify_published": 30,
            "execute": 30,
        }
        
        return timeouts.get(action, 30)
    
    def _assess_risk(self, intent: Intent, plan: ExecutionPlan) -> RiskLevel:
        """Assess overall risk level of a plan."""
        if intent.requires_approval:
            return RiskLevel.HIGH
        
        high_risk_actions = ["delete", "remove", "destroy", "publish", "deploy"]
        for step in plan.steps:
            if any(action in step.action.lower() for action in high_risk_actions):
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _identify_checkpoints(self, plan: ExecutionPlan) -> list[str]:
        """Identify steps where state should be saved."""
        checkpoints = []
        
        # Checkpoint before high-risk actions
        high_risk_actions = ["publish", "deploy", "merge", "delete"]
        for step in plan.steps:
            if any(action in step.action.lower() for action in high_risk_actions):
                checkpoints.append(step.id)
        
        # Checkpoint at the end
        if plan.steps:
            checkpoints.append(plan.steps[-1].id)
        
        return checkpoints
    
    def _generate_recovery_plan(self, plan: ExecutionPlan) -> list[TaskStep]:
        """Generate recovery steps for potential failures."""
        recovery_steps = []
        
        for step in plan.steps:
            if step.action in ["publish", "deploy"]:
                recovery = TaskStep(
                    id=f"recovery_{step.id}",
                    description=f"Rollback {step.description} if failed",
                    action="rollback",
                    parameters={"original_step": step.id},
                    plugin=step.plugin,
                    timeout=30,
                )
                recovery_steps.append(recovery)
        
        return recovery_steps
    
    def register_template(self, template: WorkflowTemplate) -> None:
        """Register a custom workflow template."""
        self._templates[template.id] = template
