from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ..application.interfaces import OcrProvider
from ..domain.enums import OcrEngine, OcrEngineStatus, OcrLanguage
from ..exceptions import OcrProviderError, ProviderNotAvailableError

logger = logging.getLogger("gula.document_intelligence.providers.manager")


class OcrProviderManager:
    def __init__(self) -> None:
        self._providers: dict[OcrEngine, OcrProvider] = {}
        self._benchmarks: dict[OcrEngine, dict[str, float]] = {}
        self._default_engine: OcrEngine = OcrEngine.tesseract
        self._failover_order: list[OcrEngine] = []
        self._lock = asyncio.Lock()

    def register(self, engine: OcrEngine, provider: OcrProvider) -> None:
        self._providers[engine] = provider
        logger.info("OCR provider registered: %s (%s)", engine, provider.display_name)

    def get(self, engine: OcrEngine) -> OcrProvider:
        provider = self._providers.get(engine)
        if not provider:
            raise OcrProviderError(f"OCR provider '{engine}' not registered")
        return provider

    def get_all(self) -> dict[OcrEngine, OcrProvider]:
        return dict(self._providers)

    @property
    def available_engines(self) -> list[OcrEngine]:
        return list(self._providers.keys())

    @property
    def default_engine(self) -> OcrEngine:
        return self._default_engine

    @default_engine.setter
    def default_engine(self, engine: OcrEngine) -> None:
        if engine not in self._providers:
            raise OcrProviderError(f"Cannot set default to unregistered engine: {engine}")
        self._default_engine = engine

    async def initialize_all(self) -> dict[OcrEngine, bool]:
        results: dict[OcrEngine, bool] = {}
        for engine, provider in self._providers.items():
            try:
                await provider.initialize()
                results[engine] = True
                logger.info("Provider initialized: %s", engine)
            except Exception as exc:
                results[engine] = False
                logger.warning("Provider initialization failed: %s — %s", engine, exc)
        return results

    async def shutdown_all(self) -> None:
        for engine, provider in self._providers.items():
            try:
                await provider.shutdown()
            except Exception as exc:
                logger.warning("Provider shutdown error: %s — %s", engine, exc)

    async def get_best_provider(
        self, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> OcrProvider:
        available = []
        for engine, provider in self._providers.items():
            status = await provider.check_health()
            if status == OcrEngineStatus.available:
                available.append((engine, provider))

        if not available:
            raise ProviderNotAvailableError("No OCR providers are available")

        if len(available) == 1:
            return available[0][1]

        best = available[0][1]
        best_score = 0.0
        for engine, provider in available:
            benchmark = self._benchmarks.get(engine, {})
            score = benchmark.get("avg_latency_ms", 1000)
            weight = 1000 / max(score, 1)
            if weight > best_score:
                best_score = weight
                best = provider

        return best

    async def benchmark_all(self, test_images: list[bytes] | None = None) -> dict[str, Any]:
        if not test_images:
            test_images = []

        results: dict[str, Any] = {}
        for engine, provider in self._providers.items():
            try:
                result = await provider.benchmark(test_images)
                results[str(engine)] = result
                self._benchmarks[engine] = result
            except Exception as exc:
                results[str(engine)] = {"error": str(exc)}

        return {
            "results": results,
            "best_provider": str(
                (await self.get_best_provider()).engine_type,
            ),
            "timestamp": time.time(),
        }

    async def auto_select(
        self, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> OcrProvider:
        try:
            return await self.get_best_provider(language)
        except ProviderNotAvailableError:
            pass

        for engine in self._failover_order:
            if engine in self._providers:
                try:
                    status = await self._providers[engine].check_health()
                    if status == OcrEngineStatus.available:
                        return self._providers[engine]
                except Exception:
                    continue

        if self._default_engine in self._providers:
            status = await self._providers[self._default_engine].check_health()
            if status in (OcrEngineStatus.available, OcrEngineStatus.degraded):
                return self._providers[self._default_engine]

        raise ProviderNotAvailableError("No OCR providers available after failover")

    def set_failover_order(self, engines: list[OcrEngine]) -> None:
        self._failover_order = [
            e for e in engines if e != self._default_engine
        ]
        logger.info(
            "OCR failover order: %s → %s",
            self._default_engine,
            self._failover_order,
        )

    async def health_check_all(self) -> dict[OcrEngine, OcrEngineStatus]:
        results: dict[OcrEngine, OcrEngineStatus] = {}
        for engine, provider in self._providers.items():
            try:
                results[engine] = await provider.check_health()
            except Exception:
                results[engine] = OcrEngineStatus.unavailable
        return results
