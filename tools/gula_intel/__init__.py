"""GULA Intelligent Platform Core — deterministic, AI-free platform self-knowledge.

The core answers questions about the platform from repository content and
recorded execution results only.  No AI provider is imported, required, or
consulted; an optional adapter boundary is defined in ``ai_boundary`` for a
future explanation layer that may consume these outputs but may never become a
source of truth.
"""
from __future__ import annotations

__all__ = ["detectors", "impact", "inventory", "model", "registry"]
