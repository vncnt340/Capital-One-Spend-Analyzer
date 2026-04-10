from __future__ import annotations

import sys
import traceback
from functools import wraps


def safe_slot(fn):
    """Decorator that wraps a PyQt slot body in try/except.

    PyQt6 6.7+ calls abort() when any Python exception escapes a slot
    without being caught in Python first. This decorator ensures exceptions
    are always caught at the Python level, preventing the fatal abort.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            print(f"[SpendAnalyzer] Unhandled exception in slot {fn.__qualname__}:",
                  file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
    return wrapper
