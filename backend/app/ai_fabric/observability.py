from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.ai_fabric.base import InferenceRequest, InferenceResponse

logger = logging.getLogger("gula.ai_fabric.observability")


@dataclass
class UsageRecord:
    timestamp: float = 0.0
    model: str = ""
    provider: str = ""
    user_id: str = ""
    endpoint: str = ""
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    success: bool = True
    error: str = ""


class AIObserver:
    _instance: AIObserver | None = None

    def __new__(cls) -> AIObserver:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._records: list[UsageRecord] = []
            cls._instance._started_at = time.time()
        return cls._instance

    def record(
        self,
        model: str = "",
        provider: str = "",
        user_id: str = "",
        endpoint: str = "",
        latency_ms: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        success: bool = True,
        error: str = "",
    ) -> None:
        record = UsageRecord(
            timestamp=time.time(),
            model=model,
            provider=provider,
            user_id=user_id,
            endpoint=endpoint,
            latency_ms=round(latency_ms, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=round(cost, 6),
            success=success,
            error=error,
        )
        self._records.append(record)
        if len(self._records) > 100_000:
            self._records = self._records[-50_000:]

    def record_inference(
        self,
        request: InferenceRequest,
        response: InferenceResponse,
        endpoint: str = "",
        user_id: str = "",
    ) -> None:
        self.record(
            model=response.model or request.model,
            provider=response.provider,
            user_id=user_id,
            endpoint=endpoint,
            latency_ms=response.latency_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=response.cost,
            success=not response.error,
            error=response.error,
        )

    def get_statistics(self, window_hours: float = 24.0) -> dict[str, Any]:
        cutoff = time.time() - (window_hours * 3600)
        windowed = [r for r in self._records if r.timestamp >= cutoff]

        total = len(windowed)
        if not total:
            return {
                "total_requests": 0,
                "window_hours": window_hours,
                "uptime_hours": round((time.time() - self._started_at) / 3600, 2),
            }

        latencies = [r.latency_ms for r in windowed if r.success]
        costs = [r.cost for r in windowed]
        errors = [r for r in windowed if not r.success]
        by_model: dict[str, int] = defaultdict(int)
        for r in windowed:
            by_model[r.model] += 1

        total_tokens = sum(r.input_tokens + r.output_tokens for r in windowed)

        return {
            "total_requests": total,
            "window_hours": window_hours,
            "successful_requests": total - len(errors),
            "error_count": len(errors),
            "error_rate": round(len(errors) / total * 100, 2) if total else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "p50_latency_ms": round(sorted(latencies)[len(latencies) // 2], 2)
            if latencies
            else 0.0,
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2)
            if latencies
            else 0.0,
            "p99_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.99)], 2)
            if latencies
            else 0.0,
            "total_tokens": total_tokens,
            "total_cost": round(sum(costs), 6),
            "avg_cost_per_request": round(sum(costs) / total, 6) if total else 0.0,
            "models_used": dict(by_model),
            "errors_by_model": {
                model: len([r for r in errors if r.model == model])
                for model in {r.model for r in errors}
            },
            "uptime_hours": round((time.time() - self._started_at) / 3600, 2),
        }

    def get_model_performance(self, model: str) -> dict[str, Any]:
        model_records = [r for r in self._records if r.model == model]
        if not model_records:
            return {"model": model, "requests": 0}

        latencies = [r.latency_ms for r in model_records if r.success]
        costs = [r.cost for r in model_records]
        errors = [r for r in model_records if not r.success]

        return {
            "model": model,
            "requests": len(model_records),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "error_rate": round(len(errors) / len(model_records) * 100, 2)
            if model_records
            else 0.0,
            "total_cost": round(sum(costs), 6),
            "avg_cost_per_request": round(sum(costs) / len(model_records), 6)
            if model_records
            else 0.0,
        }

    def get_recent_errors(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {
                "timestamp": r.timestamp,
                "model": r.model,
                "provider": r.provider,
                "endpoint": r.endpoint,
                "error": r.error,
            }
            for r in self._records
            if not r.success
        ][-limit:]

    def get_daily_usage(self, days: int = 30) -> list[dict[str, Any]]:
        daily: dict[str, dict] = {}
        cutoff = time.time() - (days * 86400)
        for r in self._records:
            if r.timestamp < cutoff:
                continue
            day = time.strftime("%Y-%m-%d", time.localtime(r.timestamp))
            if day not in daily:
                daily[day] = {"date": day, "requests": 0, "cost": 0.0, "tokens": 0, "errors": 0}
            daily[day]["requests"] += 1
            daily[day]["cost"] += r.cost
            daily[day]["tokens"] += r.input_tokens + r.output_tokens
            if not r.success:
                daily[day]["errors"] += 1
        return sorted(daily.values(), key=lambda d: d["date"])

    def reset(self) -> None:
        self._records.clear()
        self._started_at = time.time()
        logger.info("AIObserver records reset")


ai_observer = AIObserver()
