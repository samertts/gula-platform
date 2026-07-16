"""
AI Fabric Agents — Specialized AI agents for the GULA platform.

Each agent wraps a domain-specific capability set:
  - ClinicalAgent        — Clinical decision support
  - LaboratoryAgent      — Laboratory intelligence
  - SecurityAgent        — Cybersecurity monitoring
  - EngineeringAgent     — Architecture/engineering guardian
  - CitizenAgent         — Citizen health assistant
"""

from __future__ import annotations

from app.ai_fabric.agents.base import AgentContext, AgentMemory, AgentTool, AIAgent
from app.ai_fabric.agents.citizen_agent import CitizenAgent
from app.ai_fabric.agents.clinical_agent import ClinicalAgent
from app.ai_fabric.agents.engineering_agent import EngineeringAgent
from app.ai_fabric.agents.laboratory_agent import LaboratoryAgent
from app.ai_fabric.agents.registry import AgentRegistry
from app.ai_fabric.agents.security_agent import SecurityAgent

__all__ = [
    "AIAgent",
    "AgentContext",
    "AgentMemory",
    "AgentRegistry",
    "AgentTool",
    "CitizenAgent",
    "ClinicalAgent",
    "EngineeringAgent",
    "LaboratoryAgent",
    "SecurityAgent",
]
