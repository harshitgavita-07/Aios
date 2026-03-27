"""
Aios agent — routes user input to the brain.
"""

from brain import brain


def agent_router(user_input: str) -> str:
    """Route user input to the appropriate handler.

    Currently a pass-through to brain(); future plugins
    (web search, calendar, system commands) plug in here.
    """
    return brain(user_input)
