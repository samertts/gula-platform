"""Structured JSON logging for GULA Platform.

In production (ENV=production) every log record is emitted as a single JSON
line so log-aggregation tools (Loki, ELK, CloudWatch) can parse it without
regex gymnastics.

Fields added to every record:
  ts          — ISO-8601 timestamp with microseconds
  level       — DEBUG / INFO / WARNING / ERROR / CRITICAL
  logger      — dotted logger name (e.g. "gula.audit")
  msg         — log message
  request_id  — UUID from X-Request-ID (set by RequestIDMiddleware, ctx-var)
  trace_id    — alias for request_id (for OpenTelemetry compatibility)
  user_id     — authenticated user id (set by get_current_user, ctx-var)
  lab_id      — lab context (set alongside user_id)
  latency_ms  — populated for slow-request warnings
  exc         — exception type:message (when exc_info is present)

Usage in route handlers:
    from ..core.logging_config import bind_log_context
    bind_log_context(request_id="...", user_id=42, lab_id=7)

In development (non-production) standard text logging is used (human-readable).
"""

import json
import logging
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# ── Context variables (populated per-request by middleware) ───────────────────
_ctx_request_id: ContextVar[str]         = ContextVar("request_id",  default="")
_ctx_user_id:    ContextVar[Optional[int]] = ContextVar("user_id",   default=None)
_ctx_lab_id:     ContextVar[Optional[int]] = ContextVar("lab_id",    default=None)


def bind_log_context(
    request_id: str = "",
    user_id: Optional[int] = None,
    lab_id:  Optional[int] = None,
):
    """Set per-request context that will appear in every log line for this request."""
    if request_id:
        _ctx_request_id.set(request_id)
    if user_id is not None:
        _ctx_user_id.set(user_id)
    if lab_id is not None:
        _ctx_lab_id.set(lab_id)


def get_request_id() -> str:
    return _ctx_request_id.get("")


# ── JSON log formatter ────────────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        doc: dict = {
            "ts":         datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level":      record.levelname,
            "logger":     record.name,
            "msg":        record.getMessage(),
        }

        # Per-request correlation IDs
        rid = _ctx_request_id.get("")
        if rid:
            doc["request_id"] = rid
            doc["trace_id"]   = rid  # OpenTelemetry alias
        uid = _ctx_user_id.get(None)
        if uid is not None:
            doc["user_id"] = uid
        lid = _ctx_lab_id.get(None)
        if lid is not None:
            doc["lab_id"] = lid

        # Access-log fields (attached by RequestTimingMiddleware via extra={})
        for _field in ("latency_ms", "path", "status"):
            if hasattr(record, _field):
                doc[_field] = getattr(record, _field)

        # Exception chain
        if record.exc_info:
            etype, evalue, _ = record.exc_info
            if etype is not None:
                doc["exc"] = f"{etype.__name__}: {evalue}"
                doc["traceback"] = traceback.format_exception(*record.exc_info)[-1].strip()

        # Caller location (only for WARNING+)
        if record.levelno >= logging.WARNING:
            doc["src"] = f"{record.pathname}:{record.lineno}"

        return json.dumps(doc, ensure_ascii=False, default=str)


# ── Public setup function ─────────────────────────────────────────────────────

def configure_logging(is_production: bool, log_level: str = "INFO") -> None:
    """Configure root logger with JSON or text formatter.

    Call once at application startup (main.py) before any other logging.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if is_production:
        formatter: logging.Formatter = _JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    root = logging.getLogger()
    root.setLevel(level)

    # Replace any existing handlers (avoid duplicate output)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quieten noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
