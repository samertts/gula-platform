from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.observability")

_ctx_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


@dataclass
class TraceContext:
    trace_id: str = ""
    parent_span_id: str = ""
    span_id: str = ""
    service: str = ""


class Tracer:
    def __init__(self, service_name: str = "gula"):
        self._service = service_name

    def start_span(self, name: str, trace_id: str | None = None) -> TraceContext:
        tid = trace_id or _ctx_trace_id.get() or uuid.uuid4().hex
        ctx = TraceContext(
            trace_id=tid,
            span_id=uuid.uuid4().hex[:16],
            service=self._service,
        )
        _ctx_trace_id.set(tid)
        logger.debug("[TRACE] span=%s trace=%s service=%s", name, tid, self._service)
        return ctx

    def inject_headers(self, ctx: TraceContext) -> dict[str, str]:
        return {
            "X-Trace-Id": ctx.trace_id,
            "X-Span-Id": ctx.span_id,
        }

    def extract_from_headers(self, headers: dict[str, str]) -> TraceContext:
        return TraceContext(
            trace_id=headers.get("X-Trace-Id", ""),
            span_id=headers.get("X-Span-Id", ""),
            service=self._service,
        )


_tracer: Tracer | None = None


def get_tracer(service_name: str = "gula") -> Tracer:
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer


def trace(name: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            ctx = tracer.start_span(name)
            start = time.time()
            try:
                return fn(*args, **kwargs)
            finally:
                duration = time.time() - start
                logger.debug("[TRACE] span=%s duration=%.3fms", name, duration * 1000)
        return wrapper
    return decorator
