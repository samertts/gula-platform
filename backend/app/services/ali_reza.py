"""
ali_reza.py — thin compatibility shim.
All logic lives in ali_reza_engine.py (richer thresholds, more tests).
"""

from .ali_reza_engine import analyze  # noqa: F401  re-export for backward compat
