"""
Mode Controller — Smart mode detection and switching
Automatically detects when research mode is needed.
"""

import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("aios.mode")


class AgentMode(Enum):
    """Operating modes for the agent."""
    CHAT = "chat"           # Standard conversation
    RESEARCH = "research"   # Web search + RAG needed
    EXECUTE = "execute"     # Tool execution
    REASON = "reason"       # Complex reasoning required


@dataclass
class ModeDecision:
    """Decision about which mode to use."""
    mode: AgentMode
    confidence: float
    reasoning: str
    requires_web: bool
    requires_tools: bool


class ModeController:
    """
    Detects the appropriate mode for handling user queries.
    
    Change: Multi-mode intelligence
    Why:
    - Previous system had limited routing
    - Different queries need different strategies
    - Research vs chat vs execution are distinct
    Impact:
    - Appropriate handling of each query type
    - Better resource utilization
    """

    # Keywords indicating need for fresh information
    RESEARCH_KEYWORDS = [
        r"\b(latest|recent|current|today|news|update|new)\b",
        r"\b(weather|forecast|stock|price)\b",
        r"\b(who won|what happened|when did)\b",
        r"\b(how much does|where can i buy)\b",
    ]
    
    # Keywords indicating tool execution
    EXECUTE_KEYWORDS = [
        r"\b(run|execute|calculate|compute|find|search)\b",
        r"\b(create file|write file|read file|delete)\b",
        r"\b(system info|cpu|memory|disk)\b",
        r"\b(open|launch|close)\b",
    ]
    
    # Keywords indicating complex reasoning
    REASON_KEYWORDS = [
        r"\b(why|explain|analyze|compare|contrast)\b",
        r"\b(step by step|walk me through|how would)\b",
        r"\b(pros and cons|advantages|disadvantages)\b",
        r"\b(if.*then|what if|scenario)\b",
    ]

    def __init__(self):
        self.mode_history: list = []
        self.max_history = 10
        log.info("ModeController initialized")

    def detect_mode(self, user_input: str, context: Optional[Dict] = None) -> ModeDecision:
        """
        Detect appropriate mode for the query.
        
        Change: Multi-factor mode detection
        Why:
        - Single regex patterns are brittle
        - Need confidence scoring
        - Context matters for mode selection
        Impact:
        - Correct mode selection
        - Appropriate resource allocation
        """
        text = user_input.lower()
        scores = {mode: 0.0 for mode in AgentMode}
        
        # Score each mode
        for pattern in self.RESEARCH_KEYWORDS:
            if re.search(pattern, text):
                scores[AgentMode.RESEARCH] += 0.3
        
        for pattern in self.EXECUTE_KEYWORDS:
            if re.search(pattern, text):
                scores[AgentMode.EXECUTE] += 0.3
        
        for pattern in self.REASON_KEYWORDS:
            if re.search(pattern, text):
                scores[AgentMode.REASON] += 0.25
        
        # Default to CHAT if no strong signals
        if all(s < 0.3 for s in scores.values()):
            scores[AgentMode.CHAT] = 0.8
        
        # Boost CHAT for short, simple queries
        word_count = len(text.split())
        if word_count < 5 and scores[AgentMode.EXECUTE] < 0.5:
            scores[AgentMode.CHAT] += 0.3
        
        # Determine winning mode
        winning_mode = max(scores, key=scores.get)
        confidence = scores[winning_mode]
        
        # Determine requirements
        requires_web = winning_mode == AgentMode.RESEARCH or scores[AgentMode.RESEARCH] > 0.3
        requires_tools = winning_mode == AgentMode.EXECUTE or scores[AgentMode.EXECUTE] > 0.3
        
        # Build reasoning
        reasoning_parts = []
        if winning_mode == AgentMode.RESEARCH:
            reasoning_parts.append("Query asks for recent/factual information")
        elif winning_mode == AgentMode.EXECUTE:
            reasoning_parts.append("Query involves system operations or calculations")
        elif winning_mode == AgentMode.REASON:
            reasoning_parts.append("Query requires complex analysis")
        else:
            reasoning_parts.append("Standard conversation mode")
        
        decision = ModeDecision(
            mode=winning_mode,
            confidence=min(confidence, 1.0),
            reasoning="; ".join(reasoning_parts),
            requires_web=requires_web,
            requires_tools=requires_tools
        )
        
        # Track history
        self.mode_history.append(decision)
        if len(self.mode_history) > self.max_history:
            self.mode_history = self.mode_history[-self.max_history:]
        
        log.info(f"Mode detected: {winning_mode.value} (confidence: {confidence:.2f})")
        return decision

    def get_preferred_mode(self, last_n: int = 3) -> Optional[AgentMode]:
        """Get most common recent mode."""
        if not self.mode_history:
            return None
        
        recent = self.mode_history[-last_n:]
        mode_counts = {}
        for d in recent:
            mode_counts[d.mode] = mode_counts.get(d.mode, 0) + 1
        
        return max(mode_counts, key=mode_counts.get)

    def should_refresh_knowledge(self, query: str, last_web_search: Optional[str] = None) -> bool:
        """Determine if we need fresh web data."""
        decision = self.detect_mode(query)
        return decision.requires_web
