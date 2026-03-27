"""
Aios brain — input processing and LLM orchestration.
"""

from llm import ask_llm


def brain(user_input: str) -> str:
    text = user_input.strip()
    if not text:
        return "Please type something."
    return ask_llm(text)