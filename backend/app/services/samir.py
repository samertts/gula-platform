"""
samir.py — thin compatibility shim.
All logic lives in samir_engine.py (richer tips, more pages, type checking).
"""
from .samir_engine import samir, samir_help  # noqa: F401  re-export for backward compat
