from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.ai_fabric.agents.citizen_agent import CitizenAgent
from app.ai_fabric.agents.clinical_agent import ClinicalAgent
from app.ai_fabric.agents.engineering_agent import EngineeringAgent
from app.ai_fabric.agents.laboratory_agent import LaboratoryAgent
from app.ai_fabric.agents.registry import AgentRegistry
from app.ai_fabric.agents.security_agent import SecurityAgent
from app.ai_fabric.gateway import AIGateway
from app.ai_fabric.rag import RAGEngine, SemanticSearch, VectorStore
from app.ai_fabric.routes import router as ai_fabric_router
from app.ai_fabric.sdk import UnifiedAISDK

logger = logging.getLogger("gula.ai_fabric.integration")


_sdk: UnifiedAISDK | None = None
_gateway: AIGateway | None = None
_rag: RAGEngine | None = None
_agent_registry: AgentRegistry | None = None
_initalized: bool = False


def get_sdk() -> UnifiedAISDK:
    global _sdk
    if _sdk is None:
        _sdk = UnifiedAISDK()
    return _sdk


def get_gateway() -> AIGateway:
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway


def get_rag() -> RAGEngine:
    global _rag
    if _rag is None:
        gateway = get_gateway()
        vector_store = VectorStore()
        semantic_search = SemanticSearch(gateway, vector_store)
        _rag = RAGEngine(gateway=gateway, vector_store=vector_store, semantic_search=semantic_search)
    return _rag


def get_agent_registry() -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def _register_default_agents(registry: AgentRegistry) -> None:
    registry.register(ClinicalAgent())
    registry.register(LaboratoryAgent())
    registry.register(SecurityAgent())
    registry.register(EngineeringAgent())
    registry.register(CitizenAgent())
    logger.info("Default AI agents registered")


def initialize_ai_fabric(app: FastAPI | None = None) -> dict[str, Any]:
    global _initalized
    if _initalized:
        return {"status": "already_initialized"}

    gateway = get_gateway()
    registry = get_agent_registry()
    _register_default_agents(registry)
    registry.initialize_all()

    {
        "gateway": gateway,
        "rag": get_rag(),
        "agent_registry": registry,
        "sdk": get_sdk(),
    }

    if app is not None:
        app.include_router(ai_fabric_router)

    _initalized = True
    logger.info("AI Fabric initialized with %d agents and %d providers",
                registry.count, len(gateway.router.list_available()))

    return {
        "status": "initialized",
        "agents_registered": registry.count,
        "providers_available": len(gateway.router.list_available()),
    }


def shutdown_ai_fabric(app: FastAPI | None = None) -> dict[str, Any]:
    global _initalized
    registry = get_agent_registry()
    count = registry.shutdown_all()
    _initalized = False
    logger.info("AI Fabric shut down: %d agents stopped", count)
    return {"status": "shutdown", "agents_stopped": count}


async def get_ai_fabric_health() -> dict[str, Any]:
    registry = get_agent_registry()
    gateway = get_gateway()
    return {
        "initialized": _initalized,
        "agents": registry.get_statistics(),
        "providers": len(gateway.router.list_available()),
        "rag_available": _rag is not None,
    }
