from __future__ import annotations

import json
import logging
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

_ctx_request_id: ContextVar[str] = ContextVar("request_id", default="")
_ctx_user_id: ContextVar[int | None] = ContextVar("user_id", default=None)
_ctx_lab_id: ContextVar[int | None] = ContextVar("lab_id", default=None)


def bind_log_context(
    request_id: str = "",
    user_id: int | None = None,
    lab_id: int | None = None,
) -> None:
    if request_id:
        _ctx_request_id.set(request_id)
    if user_id is not None:
        _ctx_user_id.set(user_id)
    if lab_id is not None:
        _ctx_lab_id.set(lab_id)


def get_request_id() -> str:
    return _ctx_request_id.get("")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        doc: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = _ctx_request_id.get("")
        if rid:
            doc["request_id"] = rid
            doc["trace_id"] = rid
        uid = _ctx_user_id.get(None)
        if uid is not None:
            doc["user_id"] = uid
        lid = _ctx_lab_id.get(None)
        if lid is not None:
            doc["lab_id"] = lid
        for field in ("latency_ms", "path", "status"):
            if hasattr(record, field):
                doc[field] = getattr(record, field)
        if record.exc_info:
            etype, evalue, _ = record.exc_info
            if etype is not None:
                doc["exc"] = f"{etype.__name__}: {evalue}"
                doc["traceback"] = traceback.format_exception(*record.exc_info)[-1].strip()
        if record.levelno >= logging.WARNING:
            doc["src"] = f"{record.pathname}:{record.lineno}"
        return json.dumps(doc, ensure_ascii=False, default=str)


def configure_logging(is_production: bool, log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    if is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
    root.addHandler(handler)
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
