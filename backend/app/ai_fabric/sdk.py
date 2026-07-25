from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AgentContext
from app.ai_fabric.agents.registry import AgentRegistry
from app.ai_fabric.clinical import (
    ClinicalDecisionSupport,
    ClinicalSummarizer,
    DrugInteractionDetector,
)
from app.ai_fabric.gateway import AIGateway
from app.ai_fabric.governance import (
    AIGovernance,
)
from app.ai_fabric.knowledge_graph import (
    KnowledgeGraphService,
)
from app.ai_fabric.laboratory_intelligence import (
    CriticalResultDetector,
    DeltaChecker,
    QCAnalyzer,
    WorkloadPredictor,
)
from app.ai_fabric.local_ai import EmbeddingService, LocalAIEngine, ModelRegistry, RerankingService
from app.ai_fabric.observability import AIObserver
from app.ai_fabric.public_health import (
    DiseaseSurveillance,
    OutbreakDetector,
    PopulationHealthAnalytics,
)
from app.ai_fabric.rag import RAGEngine, SemanticSearch, VectorStore
from app.ai_fabric.security import (
    AIFirewall,
)

logger = logging.getLogger("gula.ai_fabric.sdk")


class UnifiedAISDK:
    def __init__(self) -> None:
        self._gateway = AIGateway()
        self._local_ai = LocalAIEngine()
        self._model_registry = ModelRegistry()
        self._embedding = EmbeddingService(self._local_ai)
        self._reranking = RerankingService()
        self._vector_store = VectorStore()
        self._semantic_search = SemanticSearch(self._gateway, self._vector_store)
        self._rag = RAGEngine(
            gateway=self._gateway,
            vector_store=self._vector_store,
            semantic_search=self._semantic_search,
        )
        self._knowledge_graph = KnowledgeGraphService()
        self._clinical = ClinicalDecisionSupport(self._gateway)
        self._drug_interaction = DrugInteractionDetector(self._gateway)
        self._summarizer = ClinicalSummarizer(self._gateway)
        self._delta_checker = DeltaChecker()
        self._critical_detector = CriticalResultDetector()
        self._qc_analyzer = QCAnalyzer()
        self._workload_predictor = WorkloadPredictor()
        self._surveillance = DiseaseSurveillance()
        self._outbreak = OutbreakDetector()
        self._population = PopulationHealthAnalytics()
        self._governance = AIGovernance()
        self._observer = AIObserver()
        self._firewall = AIFirewall()
        self._agent_registry = AgentRegistry()

    @property
    def gateway(self) -> AIGateway:
        return self._gateway

    @property
    def rag(self) -> RAGEngine:
        return self._rag

    @property
    def knowledge_graph(self) -> KnowledgeGraphService:
        return self._knowledge_graph

    @property
    def clinical(self) -> ClinicalDecisionSupport:
        return self._clinical

    @property
    def drug_interaction(self) -> DrugInteractionDetector:
        return self._drug_interaction

    @property
    def summarizer(self) -> ClinicalSummarizer:
        return self._summarizer

    @property
    def delta_checker(self) -> DeltaChecker:
        return self._delta_checker

    @property
    def critical_detector(self) -> CriticalResultDetector:
        return self._critical_detector

    @property
    def qc_analyzer(self) -> QCAnalyzer:
        return self._qc_analyzer

    @property
    def workload_predictor(self) -> WorkloadPredictor:
        return self._workload_predictor

    @property
    def surveillance(self) -> DiseaseSurveillance:
        return self._surveillance

    @property
    def outbreak(self) -> OutbreakDetector:
        return self._outbreak

    @property
    def population(self) -> PopulationHealthAnalytics:
        return self._population

    @property
    def governance(self) -> AIGovernance:
        return self._governance

    @property
    def observer(self) -> AIObserver:
        return self._observer

    @property
    def firewall(self) -> AIFirewall:
        return self._firewall

    @property
    def agent_registry(self) -> AgentRegistry:
        return self._agent_registry

    @property
    def model_registry(self) -> ModelRegistry:
        return self._model_registry

    @property
    def embedding(self) -> EmbeddingService:
        return self._embedding

    @property
    def local_ai(self) -> LocalAIEngine:
        return self._local_ai

    async def chat(self, prompt: str, model: str = "gpt-4o-mini", **kwargs: Any) -> str:
        from app.ai_fabric.base import InferenceRequest

        request = InferenceRequest(prompt=prompt, model=model, **kwargs)
        response = self._gateway.chat(request)
        return response.text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedding.embed(texts)

    def get_health(self) -> dict[str, Any]:
        return {
            "gateway": {"providers": len(self._gateway.router.list_available())},
            "local_ai": self._local_ai.get_status(),
            "model_registry": self._model_registry.list_production(),
            "vector_store": self._vector_store.list_collections(),
            "knowledge_graph": {"available": True},
            "agents": self._agent_registry.get_statistics(),
            "observer": self._observer.get_statistics(1.0),
        }


class AgentSDK:
    def __init__(self, sdk: UnifiedAISDK | None = None) -> None:
        self._sdk = sdk or UnifiedAISDK()
        self._registry = self._sdk.agent_registry

    def create_context(self, user_id: str = "", lab_id: str = "", **kwargs: str) -> AgentContext:
        return AgentContext(
            user_id=user_id,
            lab_id=lab_id,
            **kwargs,
        )

    def run_agent(
        self, agent_name: str, context: AgentContext, input_data: dict[str, Any],
    ) -> dict[str, Any]:
        agent = self._registry.get_by_name(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        return agent.run(context, input_data)

    def find_and_run(
        self, task_type: str, context: AgentContext, input_data: dict[str, Any],
    ) -> dict[str, Any]:
        agent = self._registry.find_for_task(task_type)
        if not agent:
            return {"error": f"No agent found for task type: {task_type}"}
        return agent.run(context, input_data)

    def list_agents(self) -> list[dict[str, Any]]:
        return self._registry.list_agents()


class RAGSDK:
    def __init__(self, sdk: UnifiedAISDK | None = None) -> None:
        self._sdk = sdk or UnifiedAISDK()
        self._rag = self._sdk.rag

    async def query(
        self, question: str, collection: str = "default", top_k: int = 5,
    ) -> dict[str, Any]:
        return await self._rag.query(question, collection=collection, top_k=top_k)

    async def index(
        self, collection: str, texts: list[str], sources: list[str] | None = None,
    ) -> int:
        from app.ai_fabric.rag import Chunk

        chunks = []
        for i, text in enumerate(texts):
            chunk = Chunk(
                text=text,
                source=sources[i] if sources and i < len(sources) else "",
            )
            chunks.append(chunk)
        return await self._rag.index_documents(collection, chunks)
