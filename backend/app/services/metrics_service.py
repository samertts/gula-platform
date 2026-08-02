import os
import threading
import time
from datetime import date, datetime

from fastapi import Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import IS_PRODUCTION
from app.models.lab_order import LabOrder

_START = time.time()
_WIDE_ROLES = {"master_admin", "ministry_admin", "province_admin"}
_PROM_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

_LATENCY_BUCKETS_S = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_METRICS_LOCK = threading.Lock()
_requests_total: dict[tuple[str, str, str], int] = {}
_request_errors_total: dict[tuple[str, str], int] = {}
_latency_buckets: dict[tuple[float, str, str], int] = {}
_latency_sum: dict[tuple[str, str], float] = {}
_latency_count: dict[tuple[str, str], int] = {}
_security_events: dict[tuple[str, str, str], int] = {}


def get_rss_mb() -> float:
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return 0.0


def ping_db(db: Session) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1.0


def ping_db_detail() -> tuple[str, float]:
    from ..database import check_db_connection_detail

    t0 = time.perf_counter()
    status, _ = check_db_connection_detail()
    ms = round((time.perf_counter() - t0) * 1000, 1)
    return status, (ms if status == "ok" else -1.0)


def ping_redis() -> tuple[bool, float]:
    try:
        from ..security.redis_client import cache

        t0 = time.perf_counter()
        cache.ping()
        return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1.0


def get_order_stats(db: Session, lab_id: int | None) -> dict:
    today = date.today()
    q = db.query(
        func.count(LabOrder.id).label("total"),
        func.count(case((func.date(LabOrder.created_at) == today, LabOrder.id))).label("today"),
        func.count(case((LabOrder.status == "validated", LabOrder.id))).label("validated_total"),
        func.count(
            case(
                (
                    (LabOrder.status == "validated") & (func.date(LabOrder.validated_at) == today),
                    LabOrder.id,
                ),
            ),
        ).label("validated_today"),
        func.count(case((LabOrder.status == "pending", LabOrder.id))).label("pending"),
    )
    if lab_id is not None:
        q = q.filter(LabOrder.lab_id == lab_id)
    row = q.one()
    return {
        "orders_total": row.total,
        "orders_today": row.today,
        "validated_total": row.validated_total,
        "validated_today": row.validated_today,
        "pending": row.pending,
    }


def get_uptime_s() -> int:
    return int(time.time() - _START)


def get_queue_backlog() -> int:
    """Count outbox events pending delivery (best-effort, never raises)."""
    try:
        from ..database import SessionLocal
        from ..models.outbox import OutboxEvent

        _db = SessionLocal()
        try:
            return (
                _db.query(OutboxEvent).filter(OutboxEvent.processed_at.is_(None)).count()
            )
        finally:
            _db.close()
    except Exception:
        return 0


def get_degradation_level() -> int:
    try:
        from ..core.self_healing import health as _sh

        return _sh.degradation_level.value
    except Exception:
        return 0


def build_health_status() -> dict:
    """Liveness/readiness payload matching the frontend HealthStatus contract."""
    from ..config import APP_NAME, APP_VERSION, PLATFORM_NAME_AR, RUNTIME_MODE
    from ..core.startup_guard import is_system_ready

    db_status, _db_ms = ping_db_detail()
    red_ok, _red_ms = ping_redis()
    db_ok = db_status == "ok"
    degradation = get_degradation_level()
    startup_ok, _reason = is_system_ready()
    system_ready = startup_ok and db_ok and red_ok and degradation == 0
    return {
        "status": "ok" if system_ready else "degraded",
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": RUNTIME_MODE,
        "system_ready": system_ready,
        "database": db_status,
        "degraded_mode": degradation > 0,
        "degradation_level": degradation,
    }


def build_deep_health() -> dict:
    """Deep health payload matching the frontend DeepHealth contract."""
    db_status, db_ms = ping_db_detail()
    db_ok = db_status == "ok"
    red_ok, red_ms = ping_redis()
    backlog = get_queue_backlog()
    uptime_s = get_uptime_s()
    degradation = get_degradation_level()

    issues: list[str] = []
    if not db_ok:
        issues.append("database_unreachable")
    elif db_ms > 200:
        issues.append("database_slow")
    if not red_ok:
        issues.append("redis_unreachable")
    if backlog > 1000:
        issues.append("queue_backlog_high")
    if degradation > 0:
        issues.append(f"degraded_mode_l{degradation}")

    if not db_ok or not red_ok:
        grade = "F"
    elif degradation > 0 or db_ms > 500:
        grade = "C"
    elif backlog > 1000 or db_ms > 200 or red_ms > 50:
        grade = "B"
    else:
        grade = "A"

    active_requests = 0
    try:
        from ..middleware import ConcurrencyLimitMiddleware

        active_requests = ConcurrencyLimitMiddleware._active
    except Exception:
        pass

    return {
        "grade": grade,
        "issues": issues,
        "components": {
            "database": {
                "ok": db_ok,
                "latency_ms": db_ms,
                "error": None if db_ok else "unreachable",
            },
            "redis": {
                "ok": red_ok,
                "latency_ms": red_ms,
                "error": None if red_ok else "unreachable",
            },
            "queue": {"backlog": backlog, "error": None},
        },
        "process": {
            "memory_rss_mb": get_rss_mb(),
            "uptime_s": uptime_s,
            "uptime_h": round(uptime_s / 3600, 2),
            "active_requests": active_requests,
            "degraded_mode": degradation > 0,
        },
    }


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def record_request(method: str, route: str, status_code: int, duration_s: float) -> None:
    """Record a completed request for SLO metrics (thread-safe, in-process)."""
    status_class = f"{status_code // 100}xx"
    route_key = (method.upper(), route)
    with _METRICS_LOCK:
        _requests_total[(method.upper(), route, status_class)] = (
            _requests_total.get((method.upper(), route, status_class), 0) + 1
        )
        if status_code >= 500:
            _request_errors_total[route_key] = _request_errors_total.get(route_key, 0) + 1
        for bucket in _LATENCY_BUCKETS_S:
            if duration_s <= bucket:
                bkey = (bucket, *route_key)
                _latency_buckets[bkey] = _latency_buckets.get(bkey, 0) + 1
        _latency_sum[route_key] = _latency_sum.get(route_key, 0.0) + duration_s
        _latency_count[route_key] = _latency_count.get(route_key, 0) + 1


def record_security_event(event_type: str, method: str, route: str) -> None:
    """Record a security-relevant event (auth_failure/permission_denied/rate_limit_block)."""
    with _METRICS_LOCK:
        key = (event_type, method.upper(), route)
        _security_events[key] = _security_events.get(key, 0) + 1


def security_metrics_exposition() -> str:
    """Render security event counters consumed by gula-full.yml alert rules."""
    with _METRICS_LOCK:
        if not _security_events:
            return ""
        names = {
            "auth_failure": "gula_auth_failures_total",
            "permission_denied": "gula_permission_denied_total",
            "rate_limit_block": "gula_rate_limit_blocks_total",
        }
        lines: list[str] = []
        for event_type in names:
            lines.append(f"# HELP {names[event_type]} Security events by type")
            lines.append(f"# TYPE {names[event_type]} counter")
        for (event_type, method, route), count in sorted(_security_events.items()):
            lines.append(
                f'{names[event_type]}{{method="{_escape_label(method)}",'
                f'route="{_escape_label(route)}"}} {count}'
            )
        return "\n".join(lines) + "\n"


def request_metrics_exposition() -> str:
    """Render request SLO metrics (counters + latency histogram) in Prometheus text format."""
    with _METRICS_LOCK:
        if not _latency_count:
            return ""
        lines: list[str] = []
        lines.append("# HELP gula_requests_total Total HTTP requests completed")
        lines.append("# TYPE gula_requests_total counter")
        for (method, route, status_class), count in sorted(_requests_total.items()):
            lines.append(
                f'gula_requests_total{{method="{_escape_label(method)}",'
                f'route="{_escape_label(route)}",status="{status_class}"}} {count}'
            )
        lines.append("")
        lines.append("# HELP gula_request_errors_total HTTP requests ending in 5xx")
        lines.append("# TYPE gula_request_errors_total counter")
        for (method, route), count in sorted(_request_errors_total.items()):
            lines.append(
                f'gula_request_errors_total{{method="{_escape_label(method)}",'
                f'route="{_escape_label(route)}"}} {count}'
            )
        lines.append("")
        lines.append("# HELP gula_request_duration_seconds Request latency distribution")
        lines.append("# TYPE gula_request_duration_seconds histogram")
        for le in _LATENCY_BUCKETS_S:
            for (method, route) in sorted(_latency_count):
                count = _latency_buckets.get((le, method, route), 0)
                lines.append(
                    f'gula_request_duration_seconds_bucket{{le="{le}",'
                    f'method="{_escape_label(method)}",route="{_escape_label(route)}"}} {count}'
                )
        for (method, route) in sorted(_latency_count):
            lines.append(
                f'gula_request_duration_seconds_bucket{{le="+Inf",'
                f'method="{_escape_label(method)}",route="{_escape_label(route)}"}} {_latency_count[(method, route)]}'
            )
        for (method, route) in sorted(_latency_count):
            lines.append(
                f'gula_request_duration_seconds_sum{{method="{_escape_label(method)}",'
                f'route="{_escape_label(route)}"}} {round(_latency_sum[(method, route)], 6)}'
            )
            lines.append(
                f'gula_request_duration_seconds_count{{method="{_escape_label(method)}",'
                f'route="{_escape_label(route)}"}} {_latency_count[(method, route)]}'
            )
        return "\n".join(lines) + "\n"


def get_json_metrics(
    db: Session,
    lab_id: int | None,
    is_wide: bool,
) -> dict:
    db_status, db_ms = ping_db_detail()
    red_ok, red_ms = ping_redis()
    stats = get_order_stats(db, lab_id=lab_id if not is_wide else None)
    uptime_s = get_uptime_s()
    return {
        "uptime_s": uptime_s,
        "uptime_h": round(uptime_s / 3600, 2),
        "memory_mb": get_rss_mb(),
        "db": {"status": db_status, "ok": db_status == "ok", "ping_ms": db_ms},
        "redis": {"ok": red_ok, "ping_ms": red_ms},
        "stats": stats,
        "scope": "platform" if is_wide else "lab",
        "timestamp": datetime.now(UTC).isoformat(),
    }


def build_prometheus_response(request: Request, db: Session) -> PlainTextResponse:
    token = os.getenv("METRICS_BEARER_TOKEN", "")
    if token and IS_PRODUCTION:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            return PlainTextResponse(status_code=401, content="Unauthorized")

    db_ok, db_ms = ping_db(db)
    red_ok, red_ms = ping_redis()
    rss = get_rss_mb()
    uptime_s = get_uptime_s()

    try:
        stats = get_order_stats(db, lab_id=None)
    except Exception:
        stats = {}

    queue_backlog = get_queue_backlog()

    lines = [
        "# HELP gula_up Platform is operational (1=up, 0=down)",
        "# TYPE gula_up gauge",
        "gula_up 1",
        "",
        "# HELP gula_down Platform is down (1=down, 0=up)",
        "# TYPE gula_down gauge",
        "gula_down 0",
        "",
        "# HELP gula_uptime_seconds Process uptime in seconds",
        "# TYPE gula_uptime_seconds counter",
        f"gula_uptime_seconds {uptime_s}",
        "",
        "# HELP gula_memory_rss_mb Resident set size in MB",
        "# TYPE gula_memory_rss_mb gauge",
        f"gula_memory_rss_mb {rss}",
        "",
        "# HELP gula_db_up Database connectivity (1=ok, 0=down)",
        "# TYPE gula_db_up gauge",
        f"gula_db_up {1 if db_ok else 0}",
        "",
        "# HELP gula_db_latency_ms Last DB ping latency in milliseconds",
        "# TYPE gula_db_latency_ms gauge",
        f"gula_db_latency_ms {db_ms}",
        "",
        "# HELP gula_redis_up Redis connectivity (1=ok, 0=down)",
        "# TYPE gula_redis_up gauge",
        f"gula_redis_up {1 if red_ok else 0}",
        "",
        "# HELP gula_redis_latency_ms Last Redis ping latency in milliseconds",
        "# TYPE gula_redis_latency_ms gauge",
        f"gula_redis_latency_ms {red_ms}",
        "",
        "# HELP gula_orders_total Total lab orders ever created",
        "# TYPE gula_orders_total counter",
        f"gula_orders_total {stats.get('orders_total', 0)}",
        "",
        "# HELP gula_orders_pending Orders currently in pending state",
        "# TYPE gula_orders_pending gauge",
        f"gula_orders_pending {stats.get('pending', 0)}",
        "",
        "# HELP gula_active_requests Concurrent requests being processed",
        "# TYPE gula_active_requests gauge",
        "",
        "# HELP gula_queue_backlog Outbox events pending delivery",
        "# TYPE gula_queue_backlog gauge",
        f"gula_queue_backlog {queue_backlog}",
    ]

    try:
        from ..middleware import ConcurrencyLimitMiddleware

        lines.append(f"gula_active_requests {ConcurrencyLimitMiddleware._active}")
    except Exception:
        lines.append("gula_active_requests 0")

    try:
        from ..database import get_db_error_counts

        ec = get_db_error_counts()
        lines += [
            "",
            "# HELP gula_db_refused_total Cumulative DB 'connection refused' errors",
            "# TYPE gula_db_refused_total counter",
            f"gula_db_refused_total {ec.get('refused', 0)}",
            "",
            "# HELP gula_db_auth_failed_total Cumulative DB authentication failures",
            "# TYPE gula_db_auth_failed_total counter",
            f"gula_db_auth_failed_total {ec.get('auth_failed', 0)}",
            "",
            "# HELP gula_db_timeout_total Cumulative DB connection timeouts",
            "# TYPE gula_db_timeout_total counter",
            f"gula_db_timeout_total {ec.get('timeout', 0)}",
            "",
            "# HELP gula_db_error_total Cumulative DB unknown/other errors",
            "# TYPE gula_db_error_total counter",
            f"gula_db_error_total {ec.get('error', 0)}",
        ]
    except Exception:
        pass

    try:
        from ..database import get_db_window_snapshot

        win = get_db_window_snapshot(window_s=300)
        total_events = max(win["ok"] + win["refused"] + win["timeout"], 1)
        lines += [
            "",
            "# HELP gula_db_refused_rate_5m DB 'refused' events per minute (5min window)",
            "# TYPE gula_db_refused_rate_5m gauge",
            f"gula_db_refused_rate_5m {win['refused_per_min']}",
            "",
            "# HELP gula_db_timeout_rate_5m DB timeout events per minute (5min window)",
            "# TYPE gula_db_timeout_rate_5m gauge",
            f"gula_db_timeout_rate_5m {win['timeout_per_min']}",
            "",
            "# HELP gula_db_error_ratio_5m Fraction of DB checks that failed in last 5min (0-1)",
            "# TYPE gula_db_error_ratio_5m gauge",
            f"gula_db_error_ratio_5m {round((win['refused'] + win['timeout']) / total_events, 4)}",
        ]
    except Exception:
        pass

    try:
        from ..core.policy_engine import policy_engine

        ps = policy_engine.stats()
        lines += [
            "",
            "# HELP gula_policy_block_total Total autonomous actions blocked by policy",
            "# TYPE gula_policy_block_total counter",
            f"gula_policy_block_total {ps['blocked_total']}",
            "",
            "# HELP gula_policy_allow_total Total autonomous actions permitted by policy",
            "# TYPE gula_policy_allow_total counter",
            f"gula_policy_allow_total {ps['allowed_total']}",
        ]
    except Exception:
        pass

    try:
        from ..core.auto_repair import auto_repair

        total_repairs = sum(v["triggered"] for v in auto_repair.stats().values())
        lines += [
            "",
            "# HELP gula_auto_repair_total Total autonomous repair actions triggered",
            "# TYPE gula_auto_repair_total counter",
            f"gula_auto_repair_total {total_repairs}",
        ]
    except Exception:
        pass

    try:
        from ..core.kill_switch import is_kill_switch_active

        lines += [
            "",
            "# HELP gula_kill_switch_active Kill switch state (1=active, 0=inactive)",
            "# TYPE gula_kill_switch_active gauge",
            f"gula_kill_switch_active {1 if is_kill_switch_active() else 0}",
            "",
            "# HELP gula_degradation_level Current degradation level (0=NONE 1=L1 2=L2 3=L3)",
            "# TYPE gula_degradation_level gauge",
            f"gula_degradation_level {get_degradation_level()}",
        ]
    except Exception:
        pass

    lines.append("")
    lines.append(request_metrics_exposition())
    lines.append(security_metrics_exposition())
    lines.append("")
    return PlainTextResponse("\n".join(lines) + "\n", media_type=_PROM_CONTENT_TYPE)
