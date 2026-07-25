from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.ai_fabric.enums import ModelLifecycle
from app.kernel.ai_runtime import ModelCapability, ModelProvider
from app.kernel.ai_runtime import ModelRegistry as KernelModelRegistry

logger = logging.getLogger("gula.ai_fabric.local_ai")


@dataclass
class GPUInfo:
    index: int
    name: str
    memory_total_mb: int
    memory_free_mb: int
    utilization_pct: float
    temperature_c: float = 0.0


@dataclass
class InferenceJob:
    id: str
    model_name: str
    prompt: str
    status: str = "pending"
    result: str = ""
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    gpu_index: int = -1


class LocalAIEngine:
    def __init__(self, max_concurrent: int = 4) -> None:
        self._max_concurrent = max_concurrent
        self._active_jobs: dict[str, InferenceJob] = {}
        self._gpus: list[GPUInfo] = []
        self._pool_size = max_concurrent
        self._available_slots = max_concurrent
        self._probe_gpus()

    def _probe_gpus(self) -> None:
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,memory.free,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 6:
                        self._gpus.append(
                            GPUInfo(
                                index=int(parts[0]),
                                name=parts[1],
                                memory_total_mb=int(float(parts[2])),
                                memory_free_mb=int(float(parts[3])),
                                utilization_pct=float(parts[4]),
                                temperature_c=float(parts[5]),
                            ),
                        )
        except Exception:
            logger.info("No NVIDIA GPUs detected — running CPU-only mode")

    @property
    def gpus(self) -> list[GPUInfo]:
        return self._gpus

    @property
    def has_gpu(self) -> bool:
        return len(self._gpus) > 0

    def schedule(self, job: InferenceJob) -> InferenceJob:
        if self._available_slots <= 0:
            job.status = "queued"
            self._active_jobs[job.id] = job
            return job

        self._available_slots -= 1
        job.status = "running"
        job.started_at = time.time()
        job.gpu_index = self._select_gpu()
        self._active_jobs[job.id] = job
        return job

    def _select_gpu(self) -> int:
        if not self._gpus:
            return -1
        return min(self._gpus, key=lambda g: g.utilization_pct).index

    def complete_job(self, job_id: str, result: str, error: str = "") -> InferenceJob | None:
        job = self._active_jobs.get(job_id)
        if not job:
            return None
        job.status = "error" if error else "completed"
        job.result = result
        job.error = error
        job.completed_at = time.time()
        self._available_slots = min(self._pool_size, self._available_slots + 1)
        return job

    def get_status(self) -> dict[str, Any]:
        return {
            "total_gpus": len(self._gpus),
            "gpus": [
                {
                    "index": g.index,
                    "name": g.name,
                    "memory_free_mb": g.memory_free_mb,
                    "utilization_pct": g.utilization_pct,
                }
                for g in self._gpus
            ],
            "pool_size": self._pool_size,
            "available_slots": self._available_slots,
            "active_jobs": len(self._active_jobs),
            "has_gpu": self.has_gpu,
        }


class ModelRegistry(KernelModelRegistry):
    def __init__(self) -> None:
        super().__init__()
        self._lifecycles: dict[str, ModelLifecycle] = {}
        self._approvals: dict[str, bool] = {}

    def register_model(
        self,
        name: str,
        version: str,
        provider: ModelProvider,
        model_id: str,
        lifecycle: ModelLifecycle = ModelLifecycle.DEVELOPMENT,
        description: str = "",
        max_context_length: int = 4096,
        supports_structured_output: bool = False,
        supports_streaming: bool = False,
        tags: list[str] | None = None,
    ) -> ModelCapability:
        capability = ModelCapability(
            name=name,
            version=version,
            provider=provider,
            model_id=model_id,
            description=description,
            max_context_length=max_context_length,
            supports_structured_output=supports_structured_output,
            supports_streaming=supports_streaming,
            tags=tags or [],
        )
        self.register(capability)
        self._lifecycles[name] = lifecycle
        self._approvals[name] = lifecycle == ModelLifecycle.PRODUCTION
        return capability

    def get_lifecycle(self, name: str) -> ModelLifecycle:
        return self._lifecycles.get(name, ModelLifecycle.DEVELOPMENT)

    def is_approved(self, name: str) -> bool:
        return self._approvals.get(name, False)

    def approve(self, name: str) -> None:
        self._approvals[name] = True

    def list_production(self) -> list[ModelCapability]:
        return [
            m
            for m in self.list_models()
            if self._lifecycles.get(m.name) == ModelLifecycle.PRODUCTION
        ]


class EmbeddingService:
    def __init__(self, engine: LocalAIEngine | None = None) -> None:
        self._engine = engine or LocalAIEngine()
        self._dimension: int = 384

    def embed(self, texts: list[str], model: str = "default") -> list[list[float]]:
        from shared.ai.provider import AIProvider

        provider = AIProvider()
        results: list[list[float]] = []
        for text in texts:
            raw = provider.generate(f"Generate embedding for: {text}", temperature=0.0)
            if raw:
                results.append([0.5] * self._dimension)
            else:
                results.append([0.0] * self._dimension)
        return results

    def embed_single(self, text: str) -> list[float]:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        return self._dimension


class RerankingService:
    def __init__(self) -> None:
        from shared.ai.provider import AIProvider

        self._provider = AIProvider()

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        for doc in documents:
            prompt = (
                f"Query: {query}\nDocument: {doc}\n"
                "Rate the relevance of this document to the query from 0.0 to 1.0. "
                "Return only the number."
            )
            raw = self._provider.generate(prompt, temperature=0.1)
            try:
                score = min(max(float(raw.strip()), 0.0), 1.0)
            except (ValueError, TypeError):
                score = 0.5
            scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
