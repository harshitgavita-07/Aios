"""
SoulSync — Advanced emotion detection and personality adaptation
Uses pattern matching and context to detect user emotions and adapt responses.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("aios.soulsync")


@dataclass
class EmotionState:
    """Current emotional state of the user."""
    dominant: str
    intensity: float
    confidence: float
    context: Dict[str, any]
    
    def __init__(self, dominant: str = "neutral", intensity: float = 0.5, confidence: float = 0.5):
        self.dominant = dominant
        self.intensity = intensity
        self.confidence = confidence
        self.context = {}


class SoulSync:
    """
    Advanced emotion detection and response adaptation system.
    
    Features:
    - Multi-pattern emotion detection
    - Context-aware analysis
    - Personality adaptation
    - Emotional memory
    
    Change: Advanced emotion processing
    Why:
    - Simple keyword matching was too basic
    - Users have complex emotional states
    Impact:
    - Better user experience
    - More empathetic responses
    """

    def __init__(self, data_dir=None):
        self.data_dir = data_dir
        self.emotion_lexicon = self._build_lexicon()
        self.personality_profiles = self._load_personality_profiles()
        self.emotional_memory = []
        self.current_emotion = None
        log.info("SoulSync initialized")

    def _build_lexicon(self) -> Dict[str, List[str]]:
        """Build comprehensive emotion lexicon."""
        return {
            "frustrated": [
                "not working", "broken", "wrong", "error", "fail", "crash",
                "still doesn't", "why isn't", "ugh", "damn", "annoying",
                "useless", "terrible", "awful", "hate", "keeps failing",
                "fix this", "nothing works", "stuck", "blocked", "can't",
            ],
            "anxious": [
                "worried", "nervous", "scared", "afraid", "panic", "stress",
                "urgent", "asap", "deadline", "help me", "please hurry",
                "what if", "might break", "could go wrong", "risky",
                "concerned", "uneasy", "apprehensive",
            ],
            "happy": [
                "thanks", "thank you", "great", "awesome", "love it",
                "perfect", "excellent", "amazing", "nice", "cool", "works",
                "finally", "yay", "wonderful", "pleased", "satisfied",
                "grateful", "appreciative",
            ],
            "excited": [
                "wow", "incredible", "insane", "mind-blowing", "can't believe",
                "this is huge", "so fast", "way better", "next level",
                "excited", "pumped", "stoked", "thrilled", "enthusiastic",
            ],
            "curious": [
                "how does", "why does", "what is", "explain", "can you tell",
                "i wonder", "interesting", "how would", "what if", "could you",
                "i want to understand", "teach me", "show me", "tell me more",
                "fascinating", "intrigued",
            ],
            "confused": [
                "confused", "lost", "don't understand", "unclear", "puzzled",
                "bewildered", "mystified", "baffled", "perplexed",
            ],
            "angry": [
                "angry", "mad", "furious", "outraged", "infuriated",
                "irritated", "annoyed", "pissed off", "enraged",
            ],
            "sad": [
                "sad", "unhappy", "depressed", "disappointed", "sorry",
                "regretful", "down", "blue", "melancholy",
            ],
        }

    def _load_personality_profiles(self) -> Dict[str, Dict]:
        """Load personality adaptation profiles."""
        return {
            "frustrated": {
                "tone": "supportive",
                "style": "step_by_step",
                "empathy": "high",
                "prompt_modifier": "I understand this is frustrating. Let's work through this together step by step."
            },
            "anxious": {
                "tone": "calming",
                "style": "reassuring",
                "empathy": "high",
                "prompt_modifier": "I can help you with this. Take a deep breath - we'll figure it out together."
            },
            "happy": {
                "tone": "enthusiastic",
                "style": "celebratory",
                "empathy": "medium",
                "prompt_modifier": "That's great! I'm excited to help you make the most of this."
            },
            "excited": {
                "tone": "energetic",
                "style": "collaborative",
                "empathy": "medium",
                "prompt_modifier": "This is exciting! Let's dive in and explore the possibilities."
            },
            "curious": {
                "tone": "educational",
                "style": "explanatory",
                "empathy": "medium",
                "prompt_modifier": "That's a great question. Let me explain this clearly."
            },
            "confused": {
                "tone": "patient",
                "style": "clarifying",
                "empathy": "high",
                "prompt_modifier": "I can see this might be confusing. Let me break it down for you."
            },
            "angry": {
                "tone": "calm",
                "style": "de-escalating",
                "empathy": "high",
                "prompt_modifier": "I hear your frustration. Let's focus on solving this issue."
            },
            "sad": {
                "tone": "compassionate",
                "style": "supportive",
                "empathy": "high",
                "prompt_modifier": "I'm sorry you're feeling this way. I'm here to help however I can."
            },
            "neutral": {
                "tone": "balanced",
                "style": "direct",
                "empathy": "medium",
                "prompt_modifier": ""
            },
        }

    def detect_emotion(self, text: str, context: Optional[Dict] = None) -> EmotionState:
        """
        Detect user's emotional state from text and context.
        
        Change: Multi-factor emotion detection
        Why:
        - Single keyword matching misses nuance
        - Context improves accuracy
        Impact:
        - More accurate emotion detection
        - Better response adaptation
        """
        text_lower = text.lower()
        
        # Score emotions based on lexicon matches
        scores = {}
        for emotion, keywords in self.emotion_lexicon.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[emotion] = score
        
        # Consider context from recent messages
        if context and "recent_emotions" in context:
            for emotion in context["recent_emotions"]:
                if emotion in scores:
                    scores[emotion] += 0.5  # Boost continuity
                else:
                    scores[emotion] = 0.5
        
        # Pattern-based intensity detection
        intensity = self._calculate_intensity(text_lower)
        
        if not scores:
            primary_emotion = "neutral"
            confidence = 0.5
        else:
            primary_emotion = max(scores, key=scores.get)
            confidence = min(scores[primary_emotion] / 3, 1.0)  # Normalize confidence
        
        # Adjust for intensity
        if intensity > 0.7:
            confidence = min(confidence + 0.2, 1.0)
        
        state = EmotionState(dominant=primary_emotion, intensity=intensity, confidence=confidence)
        
        # Store current emotion
        self.current_emotion = state
        
        # Store in emotional memory
        self.emotional_memory.append({
            "text": text,
            "emotion": primary_emotion,
            "intensity": intensity,
            "timestamp": __import__("time").time()
        })
        
        # Keep memory limited
        if len(self.emotional_memory) > 10:
            self.emotional_memory.pop(0)
        
        log.debug(f"Detected emotion: {primary_emotion} (intensity: {intensity:.2f}, confidence: {confidence:.2f})")
        return state

    def _calculate_intensity(self, text: str) -> float:
        """Calculate emotional intensity from text patterns."""
        intensity_indicators = {
            "high": [
                "!!!", "???", "so much", "extremely", "absolutely", "totally",
                "completely", "utterly", "incredibly", "unbelievably",
                "really really", "very very", "super", "ultra",
            ],
            "medium": [
                "quite", "pretty", "fairly", "rather", "somewhat",
                "kind of", "sort of", "a bit", "a little",
            ],
            "low": [
                "slightly", "barely", "hardly", "scarcely",
            ],
        }
        
        score = 0.5  # Base neutral
        
        for level, patterns in intensity_indicators.items():
            if any(p in text for p in patterns):
                if level == "high":
                    score = min(score + 0.3, 1.0)
                elif level == "medium":
                    score = min(score + 0.1, 0.8)
                elif level == "low":
                    score = max(score - 0.1, 0.2)
        
        # Punctuation intensity
        exclamation_count = text.count("!")
        question_count = text.count("?")
        
        if exclamation_count > 2:
            score = min(score + 0.2, 1.0)
        if question_count > 2:
            score = min(score + 0.1, 0.9)
        
        return score

    def adapt_response(self, emotion_state: EmotionState, base_response: str) -> str:
        """
        Adapt response based on detected emotion.
        
        Change: Emotion-aware response adaptation
        Why:
        - Generic responses don't account for user state
        - Emotional intelligence improves UX
        Impact:
        - More appropriate responses
        - Better user satisfaction
        """
        if emotion_state.primary_emotion == "neutral" or emotion_state.confidence < 0.6:
            return base_response
        
        profile = self.personality_profiles.get(emotion_state.primary_emotion, self.personality_profiles["neutral"])
        
        # Add emotional prefix
        prefix = profile["prompt_modifier"]
        if prefix:
            adapted = f"{prefix}\n\n{base_response}"
        else:
            adapted = base_response
        
        # Adjust style based on emotion
        if profile["style"] == "step_by_step" and len(base_response.split(".")) > 3:
            # Break into steps for frustrated users
            sentences = [s.strip() for s in base_response.split(".") if s.strip()]
            if len(sentences) > 1:
                adapted = f"{prefix}\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
        
        return adapted

    def get_emotional_context(self) -> Dict:
        """Get current emotional context for LLM."""
        if not self.emotional_memory:
            return {"emotional_state": "neutral", "recent_emotions": []}
        
        recent_emotions = [m["emotion"] for m in self.emotional_memory[-3:]]
        dominant_emotion = max(set(recent_emotions), key=recent_emotions.count) if recent_emotions else "neutral"
        
        return {
            "emotional_state": dominant_emotion,
            "recent_emotions": recent_emotions,
            "emotional_trend": self._analyze_trend()
        }

    def get_context(self) -> Dict:
        """Get current emotional context for UI."""
        if self.current_emotion:
            return {"emotion": {"dominant": self.current_emotion.dominant}}
        else:
            return {"emotion": {"dominant": "neutral"}}

    def get_system_prompt_modifier(self) -> str:
        """Get system prompt modifier based on current emotion."""
        if self.current_emotion:
            profile = self.personality_profiles.get(self.current_emotion.dominant, self.personality_profiles["neutral"])
            return profile["prompt_modifier"]
        else:
            return ""

    def learn_from_interaction(self, user_input: str, mode: str):
        """Learn from user interaction to improve emotion detection."""
        # For now, just log it. Could be extended to update profiles or lexicons.
        log.debug(f"Learned from interaction: mode={mode}, input_length={len(user_input)}")

    def _analyze_trend(self) -> str:
        """Analyze emotional trend from memory."""
        if len(self.emotional_memory) < 3:
            return "stable"
        
        recent = [m["emotion"] for m in self.emotional_memory[-3:]]
        
        if len(set(recent)) == 1:
            return "consistent"
        elif recent[-1] != recent[0]:
            return "changing"
        else:
            return "stable"
