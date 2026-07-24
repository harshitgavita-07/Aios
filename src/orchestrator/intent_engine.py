"""
Intent Engine for AIOS Digital Coworker.

Parses natural language user input into structured intents with domain classification,
confidence scoring, and plugin requirements detection.
"""

import re
from typing import Optional
from ..shared.types import Intent, IntentDomain


class IntentEngine:
    """
    Converts natural language goals into structured intents.
    
    The Intent Engine analyzes user input to determine:
    - The goal domain (browser, filesystem, git, etc.)
    - Required plugins for execution
    - Confidence level in the interpretation
    - Whether human approval is required
    - Related context from memory
    
    Example:
        >>> engine = IntentEngine()
        >>> intent = engine.parse("Open github.com")
        >>> intent.domain
        <IntentDomain.BROWSER: 'browser'>
        >>> intent.required_plugins
        ['browser']
    """
    
    # Domain keywords for classification
    DOMAIN_KEYWORDS: dict[IntentDomain, list[str]] = {
        IntentDomain.BROWSER: [
            "open", "navigate", "go to", "visit", "website", "url",
            "search", "google", "chrome", "firefox", "safari"
        ],
        IntentDomain.FILESYSTEM: [
            "file", "folder", "directory", "create", "delete", "move",
            "copy", "rename", "find", "search files", "read", "write"
        ],
        IntentDomain.TERMINAL: [
            "terminal", "command", "shell", "bash", "zsh", "powershell",
            "run command", "execute", "cli"
        ],
        IntentDomain.GIT: [
            "git", "commit", "push", "pull", "branch", "merge", "clone",
            "checkout", "rebase", "stash", "diff", "log"
        ],
        IntentDomain.GITHUB: [
            "github", "pull request", "pr", "issue", "release", "repository",
            "repo", "fork", "star", "watch"
        ],
        IntentDomain.DOCKER: [
            "docker", "container", "image", "build", "run", "stop",
            "start", "compose", "kubernetes", "k8s"
        ],
        IntentDomain.EMAIL: [
            "email", "mail", "send email", "inbox", "gmail", "outlook"
        ],
        IntentDomain.CALENDAR: [
            "calendar", "meeting", "schedule", "appointment", "event",
            "zoom", "teams", "google meet"
        ],
        IntentDomain.SLACK: [
            "slack", "message", "channel", "dm", "thread"
        ],
        IntentDomain.NOTION: [
            "notion", "page", "database", "wiki", "document"
        ],
        IntentDomain.LINEAR: [
            "linear", "ticket", "issue", "task", "project"
        ],
        IntentDomain.RESEARCH: [
            "research", "find information", "look up", "investigate"
        ],
        IntentDomain.DOCUMENTATION: [
            "documentation", "docs", "readme", "api docs", "generate docs"
        ],
        IntentDomain.DEPLOYMENT: [
            "deploy", "publish", "release", "build", "ci", "cd",
            "pipeline", "production", "staging"
        ],
    }
    
    # High-risk actions requiring approval
    HIGH_RISK_PATTERNS: list[str] = [
        r"delete",
        r"remove",
        r"drop",
        r"destroy",
        r"publish",
        r"deploy.*production",
        r"merge.*main",
        r"merge.*master",
        r"force.*push",
        r"rm.*-rf",
        r"sudo.*rm",
    ]
    
    def __init__(self) -> None:
        """Initialize the Intent Engine."""
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self.risk_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HIGH_RISK_PATTERNS
        ]
    
    def parse(self, user_input: str, context: Optional[dict] = None) -> Intent:
        """
        Parse user input into a structured intent.
        
        Args:
            user_input: Natural language goal from the user
            context: Optional context dictionary with workspace info, history, etc.
            
        Returns:
            Intent object with classified domain and metadata
            
        Example:
            >>> engine = IntentEngine()
            >>> intent = engine.parse("Publish the new version to npm")
            >>> intent.goal
            'Publish the new version to npm'
            >>> intent.domain
            <IntentDomain.DEPLOYMENT: 'deployment'>
        """
        input_lower = user_input.lower()
        
        # Classify domain
        domain = self._classify_domain(input_lower)
        
        # Determine required plugins
        required_plugins = self._determine_plugins(domain)
        
        # Calculate confidence
        confidence = self._calculate_confidence(user_input, domain)
        
        # Check if approval is required
        requires_approval = self._requires_approval(user_input)
        
        # Estimate complexity
        complexity = self._estimate_complexity(user_input, domain)
        
        return Intent(
            goal=user_input,
            domain=domain,
            confidence=confidence,
            requires_approval=requires_approval,
            required_plugins=required_plugins,
            context_references=self._extract_context_refs(user_input, context),
            priority=self._determine_priority(user_input),
            estimated_complexity=complexity,
            metadata={
                "input_length": len(user_input),
                "word_count": len(user_input.split()),
            }
        )
    
    def _classify_domain(self, input_lower: str) -> IntentDomain:
        """Classify the input into a domain based on keywords."""
        scores: dict[IntentDomain, int] = {}
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in input_lower)
            if score > 0:
                scores[domain] = score
        
        if not scores:
            return IntentDomain.GENERAL
        
        return max(scores.keys(), key=lambda d: scores[d])
    
    def _determine_plugins(self, domain: IntentDomain) -> list[str]:
        """Determine which plugins are required for a domain."""
        plugin_map: dict[IntentDomain, list[str]] = {
            IntentDomain.BROWSER: ["browser"],
            IntentDomain.FILESYSTEM: ["filesystem"],
            IntentDomain.TERMINAL: ["terminal"],
            IntentDomain.GIT: ["git"],
            IntentDomain.GITHUB: ["github"],
            IntentDomain.DOCKER: ["docker"],
            IntentDomain.EMAIL: ["email"],
            IntentDomain.CALENDAR: ["calendar"],
            IntentDomain.SLACK: ["slack"],
            IntentDomain.NOTION: ["notion"],
            IntentDomain.LINEAR: ["linear"],
            IntentDomain.RESEARCH: ["browser", "research"],
            IntentDomain.DOCUMENTATION: ["filesystem", "browser"],
            IntentDomain.DEPLOYMENT: ["terminal", "docker", "github"],
            IntentDomain.GENERAL: ["browser"],
        }
        
        return plugin_map.get(domain, ["browser"])
    
    def _calculate_confidence(self, user_input: str, domain: IntentDomain) -> float:
        """Calculate confidence score based on clarity and specificity."""
        base_confidence = 0.5
        
        # Increase confidence for clear action verbs
        action_verbs = [
            "open", "create", "delete", "run", "build", "test",
            "publish", "deploy", "search", "find"
        ]
        if any(verb in user_input.lower() for verb in action_verbs):
            base_confidence += 0.2
        
        # Increase confidence for specific targets (URLs, file paths, etc.)
        if re.search(r'(https?://|\.com|\.org|\.io|/[\w.-]+)', user_input):
            base_confidence += 0.2
        
        # Decrease confidence for vague requests
        vague_words = ["something", "stuff", "things", "maybe", "probably"]
        if any(word in user_input.lower() for word in vague_words):
            base_confidence -= 0.2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _requires_approval(self, user_input: str) -> bool:
        """Check if the action requires human approval."""
        return any(pattern.search(user_input) for pattern in self.risk_patterns)
    
    def _estimate_complexity(self, user_input: str, domain: IntentDomain) -> int:
        """Estimate task complexity on a scale of 1-10."""
        complexity = 3  # Base complexity
        
        # Multi-step indicators
        multi_step_words = ["then", "after", "before", "while", "and", "also"]
        complexity += sum(1 for word in multi_step_words if word in user_input.lower())
        
        # Conditional logic indicators
        conditional_words = ["if", "unless", "when", "otherwise"]
        complexity += sum(2 for word in conditional_words if word in user_input.lower())
        
        # Domain-specific complexity
        high_complexity_domains = [
            IntentDomain.DEPLOYMENT,
            IntentDomain.DOCKER,
            IntentDomain.GITHUB,
        ]
        if domain in high_complexity_domains:
            complexity += 2
        
        return min(complexity, 10)
    
    def _extract_context_refs(
        self,
        user_input: str,
        context: Optional[dict]
    ) -> list[str]:
        """Extract references to context items from the input."""
        refs = []
        
        if not context:
            return refs
        
        # Look for project/workspace references
        if "workspace" in context:
            if context["workspace"].lower() in user_input.lower():
                refs.append("workspace")
        
        # Look for file references
        if "recent_files" in context:
            for file_path in context["recent_files"]:
                if file_path in user_input:
                    refs.append(f"file:{file_path}")
        
        return refs
    
    def _determine_priority(self, user_input: str) -> int:
        """Determine task priority on a scale of 1-10."""
        priority = 5  # Default priority
        
        # Urgency indicators
        urgent_words = ["urgent", "asap", "immediately", "now", "quick"]
        if any(word in user_input.lower() for word in urgent_words):
            priority = 8
        
        # Time-sensitive indicators
        time_words = ["today", "tomorrow", "deadline", "soon"]
        if any(word in user_input.lower() for word in time_words):
            priority = max(priority, 7)
        
        return min(priority, 10)
