"""
National AI & Intelligence Fabric (NAIF) — GULA Platform
=========================================================
Unified AI layer for the entire GULA ecosystem.

Reuses:
  - app.ai.guardrails       — guardrail enforcement, AIOperationType, AISuggestion
  - app.ai.approval         — human-in-the-loop approval workflow
  - app.ai.sandbox          — sandboxed AI execution
  - app.kernel.ai_runtime   — AIRuntime, ModelRegistry, InferenceContext
  - shared.ai.provider      — AIProvider base
  - shared.ai.client        — AIClient
  - app.knowledge_graph     — KnowledgeGraphEngine
  - ai.ai_service           — external AI gateway endpoints
"""

from __future__ import annotations
