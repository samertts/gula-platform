import time
import uuid
from contextvars import ContextVar

_current_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_current_span_id: ContextVar[str | None] = ContextVar("span_id", default=None)


def get_current_trace_id() -> str | None:
    return _current_trace_id.get()


def get_current_span_id() -> str | None:
    return _current_span_id.get()


class Span:
    def __init__(self, name: str, trace_id: str, parent_span_id: str | None = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.start_time = time.monotonic()
        self.end_time: float | None = None
        self.duration_ms: float | None = None
        self.tags: dict[str, str] = {}
        self.error: str | None = None
        self._closed = False

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value

    def close(self) -> None:
        if self._closed:
            return
        self.end_time = time.monotonic()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self._closed = True


class Tracer:
    def __init__(self, service_name: str = "gula-platform"):
        self._service_name = service_name
        self._spans: dict[str, Span] = {}
        self._traces: dict[str, list[Span]] = {}
        self._enabled = True

    def start_span(self, name: str, trace_id: str | None = None, parent_span_id: str | None = None) -> Span:
        if not trace_id:
            trace_id = str(uuid.uuid4())
        span = Span(name, trace_id, parent_span_id)
        self._spans[span.span_id] = span
        self._traces.setdefault(trace_id, []).append(span)
        _current_trace_id.set(trace_id)
        _current_span_id.set(span.span_id)
        return span

    def end_span(self, span: Span) -> None:
        if not span._closed:
            span.close()

    def get_trace(self, trace_id: str) -> list[Span]:
        return self._traces.get(trace_id, [])

    def get_trace_ids(self) -> list[str]:
        return list(self._traces.keys())

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
