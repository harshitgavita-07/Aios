"""
bubble.py — Legacy v1 compatibility shim.

The floating bubble was moved to ui/bubble.py in v2 and renamed
FloatingBubble. This file keeps the old Bubble class name working
so any scripts that still import it don't break.

app.py and app_v3.py both import from ui.bubble (correct).
This file is for backward compatibility only.
"""
from ui.bubble import FloatingBubble

# Alias for v1 code that used `from bubble import Bubble`
Bubble = FloatingBubble

__all__ = ["Bubble", "FloatingBubble"]
