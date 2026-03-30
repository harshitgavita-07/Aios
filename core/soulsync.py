"""
SoulSync — Emotional Intelligence Layer
Detects user emotion, adapts tone, maintains user profile.
"""

import re
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

log = logging.getLogger("aios.soulsync")


@dataclass
class EmotionState:
    """Current emotional context of the user."""
    valence: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    arousal: float = 0.0  # 0.0 (calm) to 1.0 (excited)
    dominant: str = "neutral"
    confidence: float = 0.0


@dataclass
class UserProfile:
    """Persistent user preferences and patterns."""
    name: str = ""
    preferred_tone: str = "balanced"  # friendly, professional, concise, technical
    interests: List[str] = None
    conversation_style: str = "casual"  # casual, formal, technical
    common_tasks: List[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.common_tasks is None:
            self.common_tasks = []


class SoulSync:
    """
    Emotional intelligence and user personalization layer.
    
    Features:
    - Rule-based emotion detection from text
    - Tone adaptation based on user emotion and profile
    - User profile persistence and learning
    """

    # Emotion keyword patterns for detection
    EMOTION_PATTERNS = {
        "joy": [r"\b(happy|excited|awesome|great|love|wonderful|fantastic|amazing|yay)\b"],
        "anger": [r"\b(angry|mad|frustrated|annoyed|hate|terrible|awful|stupid)\b"],
        "sadness": [r"\b(sad|upset|disappointed|depressed|sorry|miss|lost)\b"],
        "fear": [r"\b(worried|scared|anxious|nervous|afraid|panic|stress)\b"],
        "surprise": [r"\b(wow|whoa|unexpected|surprised|shocked|omg|incredible)\b"],
        "confusion": [r"\b(confused|lost|don't understand|unclear|what\?|huh)\b"],
        "urgency": [r"\b(urgent|asap|emergency|quick|hurry|rush|deadline)\b"],
    }

    # Tone adaptation rules
    TONE_ADAPTATIONS = {
        "joy": {"tone": "enthusiastic", "style": "casual"},
        "anger": {"tone": "calm", "style": "concise"},
        "sadness": {"tone": "empathetic", "style": "supportive"},
        "fear": {"tone": "reassuring", "style": "clear"},
        "surprise": {"tone": "engaged", "style": "casual"},
        "confusion": {"tone": "patient", "style": "technical"},
        "urgency": {"tone": "direct", "style": "concise"},
        "neutral": {"tone": "balanced", "style": "natural"},
    }

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.profile_path = self.data_dir / "user_profile.json"
        
        self.profile = self._load_profile()
        self.current_emotion = EmotionState()
        self._emotion_history: List[EmotionState] = []
        log.info("SoulSync initialized")

    def detect_emotion(self, text: str) -> EmotionState:
        """
        Detect emotion from user text using rule-based patterns.
        
        Change: Added emotion detection via keyword patterns
        Why:
        - Previous system had no emotion awareness
        - Enables tone adaptation for better UX
        Impact:
        - AI responds with appropriate emotional tone
        - Improves user connection and satisfaction
        """
        text_lower = text.lower()
        scores = {}
        
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text_lower))
            if score > 0:
                scores[emotion] = score
        
        if not scores:
            emotion = EmotionState(dominant="neutral", confidence=0.5)
        else:
            dominant = max(scores, key=scores.get)
            confidence = min(scores[dominant] / 3, 1.0)
            
            # Calculate valence/arousal based on emotion
            valence_map = {
                "joy": 0.8, "surprise": 0.3, "neutral": 0.0,
                "confusion": -0.1, "sadness": -0.6, "anger": -0.8, "fear": -0.5
            }
            arousal_map = {
                "joy": 0.7, "surprise": 0.9, "anger": 0.9, "fear": 0.8,
                "urgency": 0.9, "confusion": 0.4, "sadness": 0.2, "neutral": 0.3
            }
            
            emotion = EmotionState(
                valence=valence_map.get(dominant, 0.0),
                arousal=arousal_map.get(dominant, 0.3),
                dominant=dominant,
                confidence=confidence
            )
        
        self.current_emotion = emotion
        self._emotion_history.append(emotion)
        
        # Keep only last 10 emotions
        if len(self._emotion_history) > 10:
            self._emotion_history = self._emotion_history[-10:]
        
        log.debug(f"Detected emotion: {emotion.dominant} (confidence: {emotion.confidence:.2f})")
        return emotion

    def get_tone_adaptation(self) -> Dict[str, str]:
        """
        Get tone and style adaptation based on current emotion.
        
        Change: Dynamic tone adaptation based on detected emotion
        Why:
        - Static responses feel robotic
        - Emotional mirroring improves rapport
        Impact:
        - More natural, human-like interactions
        - Better user experience
        """
        dominant = self.current_emotion.dominant
        adaptation = self.TONE_ADAPTATIONS.get(dominant, self.TONE_ADAPTATIONS["neutral"])
        
        # Blend with user preference
        if self.profile.preferred_tone != "balanced":
            adaptation["tone"] = self.profile.preferred_tone
        if self.profile.conversation_style != "casual":
            adaptation["style"] = self.profile.conversation_style
        
        return adaptation

    def get_system_prompt_modifier(self) -> str:
        """
        Generate system prompt modifier based on emotion and profile.
        
        Change: Dynamic system prompt augmentation
        Why:
        - Previous system used static prompt
        - Context-aware prompts improve relevance
        Impact:
        - More contextually appropriate responses
        - Better alignment with user state
        """
        adaptation = self.get_tone_adaptation()
        tone = adaptation["tone"]
        style = adaptation["style"]
        
        modifiers = {
            "enthusiastic": "Be upbeat and positive in your response.",
            "calm": "Be calm and soothing. Acknowledge frustration if present.",
            "empathetic": "Show empathy and understanding. Be supportive.",
            "reassuring": "Be reassuring and clear. Provide confidence.",
            "engaged": "Show genuine interest and engagement.",
            "patient": "Be patient and thorough. Explain step by step.",
            "direct": "Be direct and to the point. Prioritize clarity.",
            "balanced": "Be helpful and natural.",
        }
        
        style_modifiers = {
            "concise": "Keep your response brief and focused.",
            "technical": "Provide technical details where relevant.",
            "casual": "Use a conversational, friendly tone.",
            "formal": "Use professional, formal language.",
            "supportive": "Offer encouragement and practical help.",
            "clear": "Be extremely clear and structured.",
            "natural": "Respond naturally.",
        }
        
        modifier = modifiers.get(tone, modifiers["balanced"])
        style_mod = style_modifiers.get(style, style_modifiers["natural"])
        
        return f"\n[Tone guidance: {modifier} {style_mod}]"

    def update_profile(self, **kwargs):
        """Update user profile with new information."""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        
        self.profile.updated_at = datetime.now().isoformat()
        self._save_profile()

    def learn_from_interaction(self, user_input: str, task_type: Optional[str] = None):
        """
        Learn from user interaction to improve profile.
        
        Change: Simple learning from interactions
        Why:
        - Static profiles don't adapt
        - Learning improves personalization over time
        Impact:
        - Gradually improving user experience
        - Better anticipation of user needs
        """
        # Track common tasks
        if task_type and task_type not in self.profile.common_tasks:
            self.profile.common_tasks.append(task_type)
            if len(self.profile.common_tasks) > 10:
                self.profile.common_tasks = self.profile.common_tasks[-10:]
        
        # Extract potential interests (simple heuristic)
        interest_keywords = ["python", "coding", "ai", "ml", "data", "web", "app", 
                          "design", "writing", "music", "gaming", "reading"]
        for keyword in interest_keywords:
            if keyword in user_input.lower() and keyword not in self.profile.interests:
                self.profile.interests.append(keyword)
                if len(self.profile.interests) > 15:
                    self.profile.interests = self.profile.interests[-15:]
        
        self.profile.updated_at = datetime.now().isoformat()
        self._save_profile()

    def _load_profile(self) -> UserProfile:
        """Load user profile from disk."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r") as f:
                    data = json.load(f)
                return UserProfile(**data)
            except Exception as e:
                log.warning(f"Could not load profile: {e}")
        
        return UserProfile(
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def _save_profile(self):
        """Save user profile to disk."""
        try:
            with open(self.profile_path, "w") as f:
                json.dump(asdict(self.profile), f, indent=2)
        except Exception as e:
            log.warning(f"Could not save profile: {e}")

    def get_context(self) -> Dict:
        """Get full SoulSync context for the agent."""
        return {
            "emotion": asdict(self.current_emotion),
            "profile": asdict(self.profile),
            "tone_adaptation": self.get_tone_adaptation(),
        }
