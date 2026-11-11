from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from app.ai_fabric.base import InferenceRequest, InferenceResponse
from app.ai_fabric.enums import AIProviderType
from shared.ai.client import AIClient
from shared.ai.provider import AIProvider, AIProviderUnavailable

logger = logging.getLogger("gula.ai_fabric.gateway")


@dataclass
class ProviderConfig:
    name: AIProviderType
    api_key_env: str
    base_url: str = ""
    models: list[str] = field(default_factory=list)
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    latency_p50_ms: float = 0.0
    weight: float = 1.0
    enabled: bool = True


class ProviderRouter:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderConfig] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults = [
            ProviderConfig(
                name=AIProviderType.OPENAI,
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com/v1",
                models=["gpt-4o", "gpt-4o-mini", "text-embedding-3-small"],
                cost_per_1k_input=0.0025,
                cost_per_1k_output=0.01,
                latency_p50_ms=1200,
            ),
            ProviderConfig(
                name=AIProviderType.ANTHROPIC,
                api_key_env="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com/v1",
                models=["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                latency_p50_ms=1500,
            ),
            ProviderConfig(
                name=AIProviderType.GEMINI,
                api_key_env="GEMINI_API_KEY",
                models=["gemini-2.0-flash", "gemini-2.0-pro"],
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
                latency_p50_ms=800,
            ),
            ProviderConfig(
                name=AIProviderType.OLLAMA,
                api_key_env="",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
                models=["llama3.2:1b", "llama3.1:8b", "mistral:7b"],
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                latency_p50_ms=2000,
                weight=0.5,
            ),
            ProviderConfig(
                name=AIProviderType.AZURE,
                api_key_env="AZURE_OPENAI_KEY",
                base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                cost_per_1k_input=0.0025,
                cost_per_1k_output=0.01,
                latency_p50_ms=1000,
            ),
            ProviderConfig(
                name=AIProviderType.VLLM,
                api_key_env="VLLM_API_KEY",
                base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8001"),
                models=["gula-medical-7b"],
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                latency_p50_ms=500,
                weight=2.0,
            ),
            ProviderConfig(
                name=AIProviderType.OPENROUTER,
                api_key_env="OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                cost_per_1k_input=0.001,
                cost_per_1k_output=0.003,
                latency_p50_ms=1500,
            ),
            ProviderConfig(
                name=AIProviderType.DEEPSEEK,
                api_key_env="DEEPSEEK_API_KEY",
                base_url="https://api.deepseek.com/v1",
                models=["deepseek-chat", "deepseek-coder"],
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.002,
                latency_p50_ms=900,
            ),
        ]
        for p in defaults:
            self.register(p)

    def register(self, config: ProviderConfig) -> None:
        if not config.enabled:
            return
        if config.api_key_env and not os.getenv(config.api_key_env):
            logger.info("Provider %s unavailable: credentials not configured", config.name.value)
            return
        self._providers[config.name.value] = config

    def get(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    def list_available(self) -> list[ProviderConfig]:
        return list(self._providers.values())

    def select_for_model(self, model: str, prefer_cost: bool = False) -> ProviderConfig | None:
        candidates = [p for p in self._providers.values() if not p.models or model in p.models]
        if not candidates:
            candidates = list(self._providers.values())
        if prefer_cost:
            candidates.sort(key=lambda p: p.cost_per_1k_input)
        else:
            candidates.sort(key=lambda p: p.latency_p50_ms)
        return candidates[0] if candidates else None


class FailoverStrategy:
    def __init__(self, router: ProviderRouter, max_retries: int = 2) -> None:
        self._router = router
        self._max_retries = max_retries

    def execute(
        self,
        request: InferenceRequest,
        call_fn: Callable[[str, InferenceRequest], InferenceResponse],
    ) -> InferenceResponse:
        primary = self._router.select_for_model(request.model)
        if not primary:
            return InferenceResponse(
                text="", model=request.model, provider="", request_id=request.request_id,
                error="No provider available",
            )

        providers_to_try = [primary, *[p for p in self._router.list_available() if p.name != primary.name][:self._max_retries]]

        last_error = ""
        for provider in providers_to_try:
            try:
                result = call_fn(provider.name.value, request)
                if not result.error:
                    return result
                last_error = result.error
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Failover from %s: %s", provider.name.value, last_error)

        return InferenceResponse(
            text="", model=request.model, provider="",
            request_id=request.request_id, error=f"All providers failed: {last_error}",
        )


class CostOptimizer:
    def __init__(self, router: ProviderRouter) -> None:
        self._router = router
        self._total_spent: float = 0.0
        self._request_count: int = 0

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        provider = self._router.select_for_model(model)
        if not provider:
            return 0.0
        input_cost = (input_tokens / 1000) * provider.cost_per_1k_input
        output_cost = (output_tokens / 1000) * provider.cost_per_1k_output
        return round(input_cost + output_cost, 6)

    def record_usage(self, response: InferenceResponse) -> None:
        cost = response.cost
        self._total_spent += cost
        self._request_count += 1

    @property
    def total_spent(self) -> float:
        return round(self._total_spent, 4)

    @property
    def average_cost(self) -> float:
        if not self._request_count:
            return 0.0
        return round(self._total_spent / self._request_count, 6)

    def cheapest_provider(self, model: str) -> ProviderConfig | None:
        return self._router.select_for_model(model, prefer_cost=True)


class AIGateway:
    def __init__(
        self,
        router: ProviderRouter | None = None,
        failover: FailoverStrategy | None = None,
        optimizer: CostOptimizer | None = None,
    ) -> None:
        self._router = router or ProviderRouter()
        self._failover = failover or FailoverStrategy(self._router)
        self._optimizer = optimizer or CostOptimizer(self._router)
        self._providers: dict[str, AIProvider] = {}
        self._clients: dict[str, AIClient] = {}
        self._init_clients()

    def _init_clients(self) -> None:
        for config in self._router.list_available():
            provider = AIProvider(api_key=os.getenv(config.api_key_env, ""))
            self._providers[config.name.value] = provider
            self._clients[config.name.value] = AIClient(provider=provider)

    def chat(self, request: InferenceRequest) -> InferenceResponse:
        start = time.monotonic()

        def _call(provider_name: str, req: InferenceRequest) -> InferenceResponse:
            client = self._clients.get(provider_name)
            if not client:
                return InferenceResponse(
                    text="", model=req.model, provider=provider_name,
                    request_id=req.request_id, error=f"Provider {provider_name} not initialized",
                )
            result = client.analyze(req.prompt, temperature=req.temperature)
            elapsed = (time.monotonic() - start) * 1000
            return InferenceResponse(
                text=result, model=req.model, provider=provider_name,
                request_id=req.request_id, latency_ms=elapsed,
            )

        response = self._failover.execute(request, _call)
        response.latency_ms = (time.monotonic() - start) * 1000
        self._optimizer.record_usage(response)
        return response

    def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        provider = self._router.select_for_model(model)
        if not provider:
            raise AIProviderUnavailable(
                f"no provider is configured for embedding model {model!r}",
            )
        ai_provider = self._providers.get(provider.name.value)
        if not ai_provider:
            raise AIProviderUnavailable(
                f"provider {provider.name.value!r} is registered but has no client",
            )
        # IA-074: this used to prompt a CHAT model with "embed: {text}" and
        # return [hash(raw) % 1000 / 1000.0] * 384, or [0.0] * 384 on failure.
        # Both are constant vectors, so every text was maximally similar to
        # every other and any similarity search over them was meaningless. The
        # hash made it worse than local_ai.py's [0.5] * 384: Python salts str
        # hashes per process, so the same text embedded to a different constant
        # after every restart, and nothing persisted across a deploy.
        #
        # embed_many uses a real embedding endpoint and raises rather than
        # inventing a vector.
        return ai_provider.embed_many(list(texts))

    @property
    def router(self) -> ProviderRouter:
        return self._router

    @property
    def cost_optimizer(self) -> CostOptimizer:
        return self._optimizer
