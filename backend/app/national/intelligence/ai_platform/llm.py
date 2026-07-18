from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.national.intelligence.ai_platform")

_MODEL_CAPABILITIES: dict[str, list[str]] = {
    "gpt-4": ["text_generation", "reasoning", "code", "analysis", "multilingual"],
    "gpt-3.5-turbo": ["text_generation", "code", "analysis"],
    "claude-3-opus": ["text_generation", "reasoning", "analysis", "multilingual"],
    "claude-3-sonnet": ["text_generation", "analysis", "multilingual"],
    "llama-3-70b": ["text_generation", "reasoning", "code", "multilingual"],
    "llama-3-8b": ["text_generation", "multilingual"],
    "gemini-pro": ["text_generation", "reasoning", "code", "multilingual"],
    "mistral-large": ["text_generation", "reasoning", "code"],
    "mixtral-8x7b": ["text_generation", "multilingual"],
}


@dataclass
class ModelInfo:
    id: str = ""
    name: str = ""
    version: str = ""
    endpoint: str = ""
    capabilities: list[str] = field(default_factory=list)
    status: str = "active"
    latency_p50_ms: float = 0.0
    cost_per_token: float = 0.0


@dataclass
class PromptTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    template: str = ""
    version: str = "1.0.0"
    variables: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class EmbeddingRecord:
    entity_id: str = ""
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeEntity:
    id: str = ""
    type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditRecord:
    id: str = ""
    model: str = ""
    input_preview: str = ""
    output_preview: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    duration_ms: float = 0.0


class LLMGateway:
    def __init__(self) -> None:
        self._providers: dict[str, Callable[..., Any]] = {}
        self._response_cache: dict[str, tuple[Any, float]] = {}
        self._cache_ttl = 300

    def register_provider(self, name: str, handler: Callable[..., Any]) -> None:
        self._providers[name] = handler

    async def query_llm(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cache_key = hashlib.md5(f"{model}:{prompt}".encode(), usedforsecurity=False).hexdigest()
        cached = self._response_cache.get(cache_key)
        if cached and time.time() < cached[1]:
            return cached[0]
        params = parameters or {}
        provider = self._providers.get(model)
        if provider is None:
            return {
                "model": model,
                "response": f"Simulated response from {model}",
                "usage": {"prompt_tokens": len(prompt.split()), "completion_tokens": 50, "total_tokens": len(prompt.split()) + 50},
                "latency_ms": 0.0,
            }
        start = time.monotonic()
        try:
            if asyncio.iscoroutinefunction(provider):
                response = await provider(prompt, **params)
            else:
                response = provider(prompt, **params)
            duration_ms = (time.monotonic() - start) * 1000
            result = {
                "model": model,
                "response": response,
                "usage": {"prompt_tokens": len(prompt.split()), "completion_tokens": len(str(response).split()), "total_tokens": len(prompt.split()) + len(str(response).split())},
                "latency_ms": round(duration_ms, 1),
            }
            self._response_cache[cache_key] = (result, time.time() + self._cache_ttl)
            return result
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            return {
                "model": model,
                "error": str(exc),
                "latency_ms": round(duration_ms, 1),
            }

    def get_available_models(self) -> list[str]:
        return list(self._providers.keys()) or list(_MODEL_CAPABILITIES.keys())

    def get_model_capabilities(self, model: str) -> list[str]:
        return _MODEL_CAPABILITIES.get(model, ["text_generation"])


import asyncio


class PromptRegistry:
    def __init__(self) -> None:
        self._prompts: dict[str, PromptTemplate] = {}
        self._versions: dict[str, list[str]] = {}

    def register_prompt(self, name: str, template: str, version: str = "1.0.0") -> PromptTemplate:
        prompt = PromptTemplate(name=name, template=template, version=version)
        self._prompts[f"{name}:{version}"] = prompt
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append(version)
        logger.info("[PromptRegistry] registered prompt=%s version=%s", name, version)
        return prompt

    def get_prompt(self, name: str, version: str | None = None) -> PromptTemplate | None:
        if version:
            return self._prompts.get(f"{name}:{version}")
        versions = self._versions.get(name, [])
        if not versions:
            return None
        latest = sorted(versions, key=lambda v: [int(x) for x in v.split(".")])[-1]
        return self._prompts.get(f"{name}:{latest}")

    def render_prompt(self, prompt_name: str, variables: dict[str, Any]) -> str:
        prompt = self.get_prompt(prompt_name)
        if prompt is None:
            raise ValueError(f"Prompt {prompt_name!r} not found")
        result = prompt.template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._model_versions: dict[str, list[str]] = {}

    def register_model(self, name: str, version: str, endpoint: str, capabilities: list[str] | None = None) -> ModelInfo:
        model = ModelInfo(
            id=f"{name}:{version}",
            name=name,
            version=version,
            endpoint=endpoint,
            capabilities=capabilities or _MODEL_CAPABILITIES.get(name, ["text_generation"]),
        )
        self._models[model.id] = model
        if name not in self._model_versions:
            self._model_versions[name] = []
        self._model_versions[name].append(version)
        logger.info("[ModelRegistry] registered model=%s version=%s", name, version)
        return model

    def get_model(self, name: str, version: str | None = None) -> ModelInfo | None:
        if version:
            return self._models.get(f"{name}:{version}")
        versions = self._model_versions.get(name, [])
        if not versions:
            return None
        latest = sorted(versions, key=lambda v: [int(x) for x in v.split(".")])[-1]
        return self._models.get(f"{name}:{latest}")

    def list_models(self, capability: str | None = None) -> list[ModelInfo]:
        models = list(self._models.values())
        if capability:
            models = [m for m in models if capability in m.capabilities]
        return models


class ModelRouter:
    def __init__(self) -> None:
        self._models: list[ModelInfo] = []
        self._selection_strategies: dict[str, Callable[..., Any]] = {}

    def register_model(self, model: ModelInfo) -> None:
        self._models.append(model)

    def register_strategy(self, name: str, strategy: Callable[..., Any]) -> None:
        self._selection_strategies[name] = strategy

    def route_request(self, request: dict[str, Any], models: list[ModelInfo] | None = None, criteria: dict[str, Any] | None = None) -> ModelInfo:
        available = models or self._models
        if not available:
            raise ValueError("No models available for routing")
        strategy_name = (criteria or {}).get("strategy", "capability_match")
        strategy = self._selection_strategies.get(strategy_name)
        if strategy:
            return strategy(request, available)
        return self.select_best_model(request, available)

    def select_best_model(self, request: dict[str, Any], available_models: list[ModelInfo]) -> ModelInfo:
        required_capability = request.get("capability", "text_generation")
        matching = [m for m in available_models if required_capability in m.capabilities and m.status == "active"]
        if not matching:
            matching = [m for m in available_models if m.status == "active"]
        if not matching:
            return available_models[0]
        return min(matching, key=lambda m: m.latency_p50_ms)

    def fallback_strategy(self, primary: ModelInfo, fallbacks: list[ModelInfo]) -> ModelInfo:
        if primary.status == "active":
            return primary
        for fallback in fallbacks:
            if fallback.status == "active":
                return fallback
        return fallbacks[0] if fallbacks else primary


class InferenceEngine:
    def __init__(self) -> None:
        self._models: dict[str, Callable[..., Any]] = {}
        self._stats: dict[str, dict[str, float]] = {}

    def register_model_fn(self, model_id: str, fn: Callable[..., Any]) -> None:
        self._models[model_id] = fn

    async def run_inference(self, model: str, input_data: Any) -> dict[str, Any]:
        fn = self._models.get(model)
        start = time.monotonic()
        if fn is None:
            result = {"model": model, "output": f"Simulated inference for {model}", "status": "simulated"}
        else:
            try:
                if asyncio.iscoroutinefunction(fn):
                    output = await fn(input_data)
                else:
                    output = fn(input_data)
                result = {"model": model, "output": output, "status": "success"}
            except Exception as exc:
                result = {"model": model, "error": str(exc), "status": "failed"}
        duration = (time.monotonic() - start) * 1000
        if model not in self._stats:
            self._stats[model] = {"count": 0, "total_latency_ms": 0.0, "errors": 0}
        self._stats[model]["count"] += 1
        self._stats[model]["total_latency_ms"] += duration
        if result["status"] == "failed":
            self._stats[model]["errors"] += 1
        result["latency_ms"] = round(duration, 1)
        return result

    async def batch_inference(self, model: str, inputs: list[Any]) -> list[dict[str, Any]]:
        results = []
        for inp in inputs:
            result = await self.run_inference(model, inp)
            results.append(result)
        return results

    async def stream_inference(self, model: str, input_stream: AsyncIterator[Any]) -> AsyncIterator[dict[str, Any]]:
        async for chunk in input_stream:
            result = await self.run_inference(model, chunk)
            yield result


class VectorStore:
    def __init__(self) -> None:
        self._store: dict[str, EmbeddingRecord] = {}
        self._index: dict[str, list[float]] = {}

    def store_embedding(self, entity_id: str, embedding: list[float], metadata: dict[str, Any] | None = None) -> None:
        record = EmbeddingRecord(
            entity_id=entity_id,
            embedding=embedding,
            metadata=metadata or {},
        )
        self._store[entity_id] = record
        self._index[entity_id] = embedding
        logger.info("[VectorStore] stored embedding entity=%s dim=%d", entity_id, len(embedding))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search_similar(self, query_embedding: list[float], k: int = 10) -> list[dict[str, Any]]:
        if not self._index:
            return []
        similarities: list[tuple[str, float]] = []
        for entity_id, embedding in self._index.items():
            sim = self._cosine_similarity(query_embedding, embedding)
            similarities.append((entity_id, sim))
        similarities.sort(key=lambda x: -x[1])
        top_k = similarities[:k]
        results = []
        for entity_id, score in top_k:
            record = self._store.get(entity_id)
            if record:
                results.append({
                    "entity_id": entity_id,
                    "score": round(score, 4),
                    "metadata": record.metadata,
                })
        return results

    def delete_embedding(self, entity_id: str) -> None:
        self._store.pop(entity_id, None)
        self._index.pop(entity_id, None)
        logger.info("[VectorStore] deleted embedding entity=%s", entity_id)


import math


class KnowledgeGraph:
    def __init__(self) -> None:
        self._entities: dict[str, KnowledgeEntity] = {}
        self._relationships: dict[str, list[dict[str, Any]]] = {}

    def add_entity(self, entity_id: str, entity_type: str, properties: dict[str, Any] | None = None) -> KnowledgeEntity:
        entity = KnowledgeEntity(id=entity_id, type=entity_type, properties=properties or {})
        self._entities[entity_id] = entity
        return entity

    def add_relationship(self, source_id: str, target_id: str, relationship_type: str, properties: dict[str, Any] | None = None) -> None:
        if source_id not in self._relationships:
            self._relationships[source_id] = []
        self._relationships[source_id].append({
            "target_id": target_id,
            "type": relationship_type,
            "properties": properties or {},
        })

    def query_graph(self, sparql_query: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for _entity_id, entity in self._entities.items():
            results.append({
                "id": entity.id,
                "type": entity.type,
                "properties": entity.properties,
            })
        return results

    def get_entity(self, entity_id: str, entity_type: str | None = None) -> KnowledgeEntity | None:
        entity = self._entities.get(entity_id)
        if entity and entity_type and entity.type != entity_type:
            return None
        return entity

    def get_relationships(self, entity_id: str, relationship_type: str | None = None) -> list[dict[str, Any]]:
        relationships = self._relationships.get(entity_id, [])
        if relationship_type:
            relationships = [r for r in relationships if r["type"] == relationship_type]
        return relationships


class RAGEngine:
    def __init__(self) -> None:
        self._vector_stores: dict[str, VectorStore] = {}

    def register_vector_store(self, name: str, store: VectorStore) -> None:
        self._vector_stores[name] = store

    def retrieve_context(self, query: str, vector_store: VectorStore, k: int = 5) -> list[dict[str, Any]]:
        query_tokens = query.lower().split()
        dummy_embedding = [hash(t) % 1000 / 1000.0 for t in query_tokens]
        dummy_embedding = dummy_embedding[:128] if len(dummy_embedding) > 128 else dummy_embedding + [0.0] * (128 - len(dummy_embedding))
        return vector_store.search_similar(dummy_embedding, k=k)

    def augment_prompt(self, prompt: str, context: list[dict[str, Any]]) -> str:
        if not context:
            return prompt
        context_str = "\n".join(
            f"- {c.get('metadata', {}).get('text', '')}"
            for c in context
            if c.get("metadata", {}).get("text")
        )
        return f"Context:\n{context_str}\n\nQuestion: {prompt}"

    async def generate_with_context(self, query: str, context: list[dict[str, Any]], llm_gateway: LLMGateway, model: str = "gpt-3.5-turbo") -> dict[str, Any]:
        augmented_prompt = self.augment_prompt(query, context)
        return await llm_gateway.query_llm(augmented_prompt, model=model)


class ExplainabilityEngine:
    def explain_prediction(self, model: str, input_data: Any, output: Any) -> dict[str, Any]:
        features = self.get_feature_importance(model, input_data)
        explanation = self.generate_explanation_text(features)
        return {
            "model": model,
            "prediction": output,
            "explanation": explanation,
            "feature_importance": features,
            "method": "feature_attribution",
        }

    def get_feature_importance(self, model: str, input_data: Any) -> list[dict[str, Any]]:
        features: list[dict[str, Any]] = []
        if isinstance(input_data, dict):
            for i, (key, value) in enumerate(input_data.items()):
                importance = 1.0 / (i + 1)
                features.append({
                    "feature": key,
                    "value": value,
                    "importance": round(importance, 4),
                    "direction": "positive" if i % 2 == 0 else "negative",
                })
        return sorted(features, key=lambda f: -f["importance"])

    def generate_explanation_text(self, features: list[dict[str, Any]], importance: list[dict[str, Any]] | None = None) -> str:
        top_features = features[:3] if features else (importance or [])
        if not top_features:
            return "No feature importance data available."
        parts = ["Top contributing factors:"]
        for f in top_features:
            parts.append(f"- {f.get('feature', 'unknown')}: {f.get('importance', 0):.2%} importance ({f.get('direction', 'neutral')})")
        return "\n".join(parts)


class SafetyFilter:
    def __init__(self) -> None:
        self._blocked_patterns: list[str] = []
        self._blocked_categories: dict[str, list[str]] = {
            "pii": [r"\b\d{3}-\d{2}-\d{4}\b", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            "clinical_diagnosis": ["diagnosis:", "treatment:", "prescribe"],
            "harmful": ["suicide", "self-harm", "violence"],
        }

    def add_blocked_pattern(self, pattern: str) -> None:
        self._blocked_patterns.append(pattern)

    def filter_input(self, prompt: str, safety_rules: list[str] | None = None) -> dict[str, Any]:
        rules = safety_rules or list(self._blocked_categories.keys())
        violations: list[str] = []
        for category in rules:
            patterns = self._blocked_categories.get(category, [])
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    violations.append(f"{category}: matched pattern {pattern}")
        for pattern in self._blocked_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                violations.append(f"custom_block: {pattern}")
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "filtered_prompt": "[FILTERED]" if violations else prompt,
        }

    def filter_output(self, response: str, safety_rules: list[str] | None = None) -> dict[str, Any]:
        return self.filter_input(response, safety_rules)

    def classify_content(self, content: str, categories: list[str]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for category in categories:
            patterns = self._blocked_categories.get(category, [])
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    match_count += 1
            scores[category] = round(min(1.0, match_count / max(len(patterns), 1)), 3)
        return scores


class AIHumanApproval:
    def __init__(self) -> None:
        self._pending_approvals: dict[str, dict[str, Any]] = {}
        self._approval_history: list[dict[str, Any]] = []

    def request_approval(self, action: str, context: dict[str, Any], risk_level: str = "medium") -> dict[str, Any]:
        approval_id = str(uuid.uuid4())
        record = {
            "approval_id": approval_id,
            "action": action,
            "context": context,
            "risk_level": risk_level,
            "status": "pending",
            "requested_at": time.time(),
            "reviewed_at": None,
            "reviewed_by": None,
            "reason": "",
        }
        self._pending_approvals[approval_id] = record
        self._approval_history.append(record)
        logger.info(
            "[AIHumanApproval] requested id=%s action=%s risk=%s",
            approval_id,
            action,
            risk_level,
        )
        return record

    def approve_action(self, approval_id: str, reviewer: str = "system") -> dict[str, Any]:
        record = self._pending_approvals.get(approval_id)
        if record is None:
            raise ValueError(f"Approval {approval_id!r} not found")
        if record["status"] != "pending":
            raise ValueError(f"Approval {approval_id} is not pending")
        record["status"] = "approved"
        record["reviewed_at"] = time.time()
        record["reviewed_by"] = reviewer
        logger.info("[AIHumanApproval] approved id=%s by=%s", approval_id, reviewer)
        return record

    def reject_action(self, approval_id: str, reason: str = "", reviewer: str = "system") -> dict[str, Any]:
        record = self._pending_approvals.get(approval_id)
        if record is None:
            raise ValueError(f"Approval {approval_id!r} not found")
        if record["status"] != "pending":
            raise ValueError(f"Approval {approval_id} is not pending")
        record["status"] = "rejected"
        record["reviewed_at"] = time.time()
        record["reviewed_by"] = reviewer
        record["reason"] = reason
        logger.info("[AIHumanApproval] rejected id=%s by=%s reason=%s", approval_id, reviewer, reason)
        return record

    def get_pending_approvals(self, user: str | None = None) -> list[dict[str, Any]]:
        pending = [a for a in self._pending_approvals.values() if a["status"] == "pending"]
        if user:
            pending = [a for a in pending if a.get("context", {}).get("assigned_to") == user]
        return pending


class AIAuditEngine:
    def __init__(self) -> None:
        self._audit_log: list[AuditRecord] = []

    def log_interaction(self, model: str, input_data: Any, output: Any, metadata: dict[str, Any] | None = None) -> str:
        record_id = str(uuid.uuid4())
        record = AuditRecord(
            id=record_id,
            model=model,
            input_preview=str(input_data)[:200],
            output_preview=str(output)[:200],
            metadata=metadata or {},
            timestamp=time.time(),
            duration_ms=metadata.get("duration_ms", 0.0) if metadata else 0.0,
        )
        self._audit_log.append(record)
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]
        return record_id

    def query_audit_log(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        results = [vars(r) for r in self._audit_log]
        if filters:
            for key, value in filters.items():
                results = [r for r in results if r.get(key) == value]
        return sorted(results, key=lambda r: -r.get("timestamp", 0))

    def generate_audit_report(self, period: float = 86400 * 30) -> dict[str, Any]:
        cutoff = time.time() - period
        recent = [r for r in self._audit_log if r.timestamp >= cutoff]
        model_counts: dict[str, int] = {}
        for r in recent:
            model_counts[r.model] = model_counts.get(r.model, 0) + 1
        return {
            "period_seconds": period,
            "total_interactions": len(recent),
            "models_used": model_counts,
            "most_used_model": max(model_counts, key=model_counts.get) if model_counts else None,
            "report_generated_at": time.time(),
        }
