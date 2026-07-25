"""
Adapters connecting AIOS orchestration to external execution runtimes.

AIOS coordinates (intent, planning, verification); it never executes
browser, filesystem, terminal, or desktop actions directly. Adapters in
this package are the only bridge to that execution -- currently SCR
Runtime, via scr_adapter.ScrRuntimeAdapter.
"""

from .scr_adapter import ScrRuntimeAdapter, ScrRuntimeError

__all__ = [
    "ScrRuntimeAdapter",
    "ScrRuntimeError",
]
