"""
Confidence System — Response quality assessment
Provides confidence scores and fallback handling.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("aios.confidence")


class ConfidenceLevel(Enum):
    """Confidence levels for responses."""
    HIGH = "high"       # >= 0.8
    MEDIUM = "medium"   # >= 0.5, < 0.8
    LOW = "low"         # < 0.5


@dataclass
class ConfidenceScore:
    """Confidence information for a response."""
    overall: float
    level: ConfidenceLevel
    factors: Dict[str, float]
    explanation: str
    should_fallback: bool
    retry_recommended: bool


class ConfidenceScorer:
    """
    Scores response confidence based on multiple factors.
    
    Change: Multi-factor confidence scoring
    Why:
    - Previous system had no quality assessment
    - Users need to know when to trust responses
    - Enables automatic retry for low confidence
    Impact:
    - Transparent quality indicators
    - Better user trust
    - Automatic fallback handling
    """

    def __init__(self):
        self.threshold_high = 0.8
        self.threshold_medium = 0.5
        log.info("ConfidenceScorer initialized")

    def score_response(self,
                      response: str,
                      context_sources: List[str],
                      mode: str,
                      has_rag: bool = False,
                      has_web: bool = False) -> ConfidenceScore:
        """
        Calculate confidence score for a response.
        
        Change: Comprehensive confidence calculation
        Why:
        - Single metric is insufficient
        - Multiple factors contribute to confidence
        - Need explanation for transparency
        Impact:
    - User-visible quality indicators
    - Informed decision making
    """
        factors = {}
        
        # Factor 1: Source diversity (more sources = higher confidence)
        source_count = len(set(context_sources))
        factors["source_diversity"] = min(source_count / 3, 1.0)
        
        # Factor 2: Has external knowledge (RAG/Web)
        if has_rag or has_web:
            factors["external_knowledge"] = 1.0
        else:
            factors["external_knowledge"] = 0.6  # Base confidence for memory-only
        
        # Factor 3: Response length adequacy
        word_count = len(response.split())
        if word_count < 10:
            factors["response_adequacy"] = 0.3  # Too short
        elif word_count > 500:
            factors["response_adequacy"] = 0.7  # Might be verbose
        else:
            factors["response_adequacy"] = 1.0
        
        # Factor 4: Uncertainty markers
        uncertainty_markers = ["i don't know", "not sure", "unclear", "cannot", "unable"]
        has_uncertainty = any(marker in response.lower() for marker in uncertainty_markers)
        factors["certainty"] = 0.4 if has_uncertainty else 1.0
        
        # Factor 5: Mode-specific confidence
        mode_multipliers = {
            "research": 0.9 if has_web else 0.6,
            "execute": 0.95,
            "chat": 0.85,
            "reason": 0.8,
        }
        factors["mode_match"] = mode_multipliers.get(mode, 0.7)
        
        # Calculate weighted overall score
        weights = {
            "source_diversity": 0.2,
            "external_knowledge": 0.25,
            "response_adequacy": 0.15,
            "certainty": 0.25,
            "mode_match": 0.15,
        }
        
        overall = sum(factors[k] * weights[k] for k in weights)
        
        # Determine level
        if overall >= self.threshold_high:
            level = ConfidenceLevel.HIGH
        elif overall >= self.threshold_medium:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        # Build explanation
        explanation_parts = []
        if level == ConfidenceLevel.HIGH:
            explanation_parts.append("High confidence based on multiple reliable sources")
        elif level == ConfidenceLevel.MEDIUM:
            explanation_parts.append("Moderate confidence; response may need verification")
        else:
            explanation_parts.append("Low confidence; recommend additional verification")
        
        if has_uncertainty:
            explanation_parts.append("Response contains uncertainty markers")
        
        should_fallback = level == ConfidenceLevel.LOW
        retry_recommended = level == ConfidenceLevel.LOW and not has_web
        
        return ConfidenceScore(
            overall=overall,
            level=level,
            factors=factors,
            explanation=" ".join(explanation_parts),
            should_fallback=should_fallback,
            retry_recommended=retry_recommended
        )

    def get_fallback_response(self, original_query: str, score: ConfidenceScore) -> str:
        """Generate fallback response for low confidence."""
        if score.retry_recommended:
            return (
                f"I'm not confident in my response to '{original_query}'. "
                "Let me search for more information..."
            )
        
        return (
            "I don't have enough reliable information to answer that question confidently. "
            "Could you provide more context or clarify what you're looking for?"
        )

    def format_for_display(self, score: ConfidenceScore) -> str:
        """Format confidence for UI display."""
        emoji = {
            ConfidenceLevel.HIGH: "🟢",
            ConfidenceLevel.MEDIUM: "🟡",
            ConfidenceLevel.LOW: "🔴",
        }
        
        return f"{emoji[score.level]} Confidence: {score.level.value.upper()} ({score.overall:.0%})"
