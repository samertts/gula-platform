from __future__ import annotations

import logging
import time
from abc import ABC
from pathlib import Path
from typing import Any

from ..application.interfaces import OcrProvider
from ..domain.entities import DocumentPage
from ..domain.enums import OcrEngineStatus, OcrLanguage

logger = logging.getLogger("gula.document_intelligence.providers")


class OcrProviderBase(OcrProvider, ABC):
    def __init__(self) -> None:
        self._initialized = False
        self._benchmark_results: dict[str, float] = {}

    async def check_health(self) -> OcrEngineStatus:
        if self._initialized:
            return OcrEngineStatus.available
        try:
            await self.initialize()
            return OcrEngineStatus.available
        except Exception:
            return OcrEngineStatus.unavailable

    async def is_available(self) -> bool:
        status = await self.check_health()
        return status == OcrEngineStatus.available

    async def get_supported_languages(self) -> list[OcrLanguage]:
        return [OcrLanguage.arabic, OcrLanguage.english, OcrLanguage.arabic_english]

    async def ocr_batch(
        self,
        images: list[bytes | Path],
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> list[DocumentPage]:
        results = []
        for img in images:
            if isinstance(img, Path):
                page = await self.ocr_image_path(img, language)
            else:
                page = await self.ocr_image(img, language)
            results.append(page)
        return results

    async def get_benchmark_score(self) -> dict[str, float]:
        if not self._benchmark_results:
            self._benchmark_results = await self._run_benchmark()
        return dict(self._benchmark_results)

    async def _run_benchmark(self) -> dict[str, float]:
        latencies: list[float] = []
        for _ in range(5):
            t0 = time.perf_counter()
            try:
                await self.ocr_image(b"dummy_benchmark", OcrLanguage.english)
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception:
                pass
        if not latencies:
            return {"avg_latency_ms": -1, "throughput_pages_per_sec": 0}
        avg_latency = sum(latencies) / len(latencies)
        return {
            "avg_latency_ms": round(avg_latency, 2),
            "throughput_pages_per_sec": round(1000 / avg_latency, 2) if avg_latency > 0 else 0,
            "samples": len(latencies),
        }

    async def benchmark(self, test_images: list[bytes]) -> dict[str, Any]:
        latencies: list[float] = []
        for img in test_images:
            t0 = time.perf_counter()
            await self.ocr_image(img)
            latencies.append((time.perf_counter() - t0) * 1000)

        avg = sum(latencies) / max(len(latencies), 1)
        return {
            "engine": str(self.engine_type),
            "version": self.version,
            "avg_latency_ms": round(avg, 2),
            "min_latency_ms": round(min(latencies), 2) if latencies else 0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0,
            "samples": len(latencies),
            "throughput_pages_per_sec": round(1000 / avg, 2) if avg > 0 else 0,
        }
