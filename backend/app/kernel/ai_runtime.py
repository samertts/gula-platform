from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum
from app.ai.approval import ApprovalStore, PendingApproval
from app.ai.approval import approval_store as _default_approval_store
from app.ai.guardrails import AISuggestion, ai_suggest
from app.ai.sandbox import AISandbox, SandboxResult
from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.ai_runtime")


class ModelProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class ModelCapability:
    name: str
    version: str
    provider: ModelProvider
    model_id: str
    description: str = ""
    max_context_length: int = 4096
    supports_structured_output: bool = False
    supports_streaming: bool = False
    requires_api_key: bool = True
    resource_requirements: dict[str, Any] = field(
        default_factory=lambda: {"memory_mb": 512, "gpu_vram_mb": 0}
    )
    tags: list[str] = field(default_factory=list)


@dataclass
class InferenceContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = ""
    prompt: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    duration_ms: float = 0.0
    provider: ModelProvider = ModelProvider.GEMINI
    operation: str = ""
    entity_type: str = ""
    entity_id: int | None = None
    trace_id: str = ""
    span_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self) -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


class ModelRegistry:
    def __init__(self):
        self._models: dict[str, ModelCapability] = {}

    def register(self, model: ModelCapability) -> None:
        self._models[model.name] = model
        logger.info(
            "Model registered", extra={"model": model.name, "provider": model.provider.value}
        )

    def get(self, name: str) -> ModelCapability | None:
        return self._models.get(name)

    def list_models(self) -> list[ModelCapability]:
        return list(self._models.values())

    def list_by_provider(self, provider: ModelProvider) -> list[ModelCapability]:
        return [m for m in self._models.values() if m.provider == provider]

    def list_by_tag(self, tag: str) -> list[ModelCapability]:
        return [m for m in self._models.values() if tag in m.tags]

    def unregister(self, name: str) -> bool:
        if name in self._models:
            del self._models[name]
            logger.info("Model unregistered", extra={"model": name})
            return True
        return False

    def count(self) -> int:
        return len(self._models)


class AIRuntime:
    def __init__(
        self,
        kernel: Kernel | None = None,
        approval_store: ApprovalStore | None = None,
    ):
        self._kernel = kernel
        self._registry = ModelRegistry()
        self._approval_store = approval_store or _default_approval_store
        self._sandbox = AISandbox()
        self._loaded_models: dict[str, Any] = {}

    @property
    def registry(self) -> ModelRegistry:
        return self._registry

    def register_default_models(self) -> None:
        defaults = [
            ModelCapability(
                name="gemini-pro",
                version="2.0",
                provider=ModelProvider.GEMINI,
                model_id="gemini-2.0-flash",
                description="Google Gemini 2.0 Flash",
                max_context_length=32768,
                supports_structured_output=True,
                supports_streaming=True,
                tags=["general", "clinical"],
            ),
            ModelCapability(
                name="gpt-4o",
                version="4.0",
                provider=ModelProvider.OPENAI,
                model_id="gpt-4o",
                description="OpenAI GPT-4o",
                max_context_length=128000,
                supports_structured_output=True,
                supports_streaming=True,
                resource_requirements={"memory_mb": 1024, "gpu_vram_mb": 0},
                tags=["general"],
            ),
            ModelCapability(
                name="claude-3-opus",
                version="3.0",
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-3-opus-20240229",
                description="Anthropic Claude 3 Opus",
                max_context_length=200000,
                supports_structured_output=True,
                supports_streaming=True,
                resource_requirements={"memory_mb": 1024, "gpu_vram_mb": 0},
                tags=["analysis", "clinical"],
            ),
        ]
        for m in defaults:
            self._registry.register(m)

    def load_model(self, name: str) -> bool:
        model = self._registry.get(name)
        if not model:
            logger.error("Model not found in registry", extra={"model": name})
            return False
        if name in self._loaded_models:
            return True
        self._loaded_models[name] = {"capability": model, "loaded_at": time.time()}
        logger.info("Model loaded", extra={"model": name, "provider": model.provider.value})
        return True

    def unload_model(self, name: str) -> bool:
        if name in self._loaded_models:
            del self._loaded_models[name]
            logger.info("Model unloaded", extra={"model": name})
            return True
        return False

    def is_loaded(self, name: str) -> bool:
        return name in self._loaded_models

    def infer(self, ctx: InferenceContext) -> AISuggestion | None:
        model = self._registry.get(ctx.model_name)
        if not model or ctx.model_name not in self._loaded_models:
            logger.error("Model not loaded", extra={"model": ctx.model_name})
            return None

        ctx.provider = model.provider
        ctx.start_time = time.time()

        try:
            suggestion = ai_suggest(
                operation=ctx.operation or "suggest_interpretation",
                payload={"prompt": ctx.prompt, **ctx.metadata},
                ai_model=ctx.model_name,
                confidence=ctx.temperature,
                entity_type=ctx.entity_type,
                entity_id=ctx.entity_id,
            )
            ctx.complete()
            return suggestion
        except Exception as exc:
            ctx.complete()
            logger.error("Inference failed", extra={"model": ctx.model_name, "error": str(exc)})
            return None

    def infer_and_submit(self, ctx: InferenceContext) -> PendingApproval | None:
        suggestion = self.infer(ctx)
        if not suggestion:
            return None
        return self._approval_store.submit(suggestion)

    def execute_approved(self, approval: PendingApproval) -> SandboxResult:
        return self._sandbox.execute(approval)

    def get_metrics(self) -> dict[str, Any]:
        return {
            "registered_models": self._registry.count(),
            "loaded_models": len(self._loaded_models),
            "loaded_names": list(self._loaded_models.keys()),
        }
