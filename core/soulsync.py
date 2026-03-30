"""
Aios SoulSync — emotion detection and tone adaptation layer.

Detects the user's emotional state from their input text using
lightweight keyword matching (no ML model, no extra deps, < 1ms).
Adapts the system prompt tone accordingly and maintains a simple
user profile derived from conversation history.

Emotions: neutral, curious, frustrated, happy, anxious, excited
"""

from __future__ import annotations

import re
from typing import NamedTuple

# ── Emotion lexicon ───────────────────────────────────────────────────────

_LEXICON: dict[str, list[str]] = {
    "frustrated": [
        "not working", "broken", "wrong", "error", "fail", "crash",
        "still doesn't", "why isn't", "ugh", "damn", "annoying",
        "useless", "terrible", "awful", "hate", "keeps failing",
        "fix this", "nothing works",
    ],
    "anxious": [
        "worried", "nervous", "scared", "afraid", "panic", "stress",
        "urgent", "asap", "deadline", "help me", "please hurry",
        "what if", "might break", "could go wrong", "risky",
    ],
    "happy": [
        "thanks", "thank you", "great", "awesome", "love it",
        "perfect", "excellent", "amazing", "nice", "cool", "works",
        "finally", "yay", "👍", "🎉", "wonderful",
    ],
    "excited": [
        "wow", "incredible", "insane", "mind-blowing", "can't believe",
        "this is huge", "so fast", "way better", "next level", "🔥", "🚀",
        "excited", "pumped", "stoked",
    ],
    "curious": [
        "how does", "why does", "what is", "explain", "can you tell",
        "i wonder", "interesting", "how would", "what if", "could you",
        "i want to understand", "teach me", "show me", "?",
    ],
}

# ── Tone templates ────────────────────────────────────────────────────────

_BASE_PROMPT = (
    "You are Aios, a local AI desktop assistant. "
    "You are concise, accurate, and helpful. "
    "All processing happens on the user's machine — no data leaves this device."
)

_TONE_SUFFIX: dict[str, str] = {
    "neutral":    " Respond clearly and directly.",
    "curious":    " The user is exploring. Be thorough and explain your reasoning step by step.",
    "frustrated": " The user is frustrated. Be calm, empathetic, and get straight to the solution. Avoid filler.",
    "anxious":    " The user seems anxious or under pressure. Be reassuring, clear, and prioritize the most important action first.",
    "happy":      " The user is in a good mood. Match their energy — be warm and slightly upbeat.",
    "excited":    " The user is excited. Share the enthusiasm while staying accurate and grounded.",
}


# ── Public API ────────────────────────────────────────────────────────────

class SoulState(NamedTuple):
    emotion: str          # detected emotion label
    confidence: float     # 0.0 – 1.0
    system_prompt: str    # adapted system prompt for the LLM


def analyse(text: str) -> SoulState:
    """
    Detect emotion in *text* and return an adapted system prompt.

    Returns SoulState(emotion, confidence, system_prompt).
    """
    emotion, confidence = _detect_emotion(text.lower())
    prompt = _BASE_PROMPT + _TONE_SUFFIX.get(emotion, _TONE_SUFFIX["neutral"])
    return SoulState(emotion=emotion, confidence=confidence, system_prompt=prompt)


def emotion_label(text: str) -> str:
    """Convenience: return just the emotion string."""
    emotion, _ = _detect_emotion(text.lower())
    return emotion


# ── Internal ──────────────────────────────────────────────────────────────

def _detect_emotion(text: str) -> tuple[str, float]:
    """
    Score each emotion bucket by keyword hits.
    Returns (emotion, confidence) where confidence = hits / total_keywords.
    """
    scores: dict[str, int] = {}

    for emotion, keywords in _LEXICON.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits:
            scores[emotion] = hits

    if not scores:
        return "neutral", 1.0

    top_emotion = max(scores, key=lambda e: scores[e])
    top_hits = scores[top_emotion]
    total_keywords = len(_LEXICON[top_emotion])
    confidence = min(top_hits / max(total_keywords * 0.2, 1), 1.0)

    return top_emotion, round(confidence, 2)
