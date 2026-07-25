import contextlib
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.patient import Patient

logger = logging.getLogger("gula.stats")

_CACHE_TTL = int(os.getenv("STATS_CACHE_TTL_SECONDS", "300"))


def _get_redis():
    try:
        import redis as _redis

        url = os.getenv("REDIS_URL") or os.getenv("REDIS_URI")
        if not url:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD")
            url = f"redis://:{password}@{host}:{port}/0" if password else f"redis://{host}:{port}/0"
        return _redis.from_url(url, decode_responses=True, socket_timeout=1)
    except Exception:
        return None


def _cache_get(key: str) -> dict | None:
    r = _get_redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key: str, data: dict, ttl: int = _CACHE_TTL) -> None:
    r = _get_redis()
    if not r:
        return
    with contextlib.suppress(Exception):
        r.setex(key, ttl, json.dumps(data, default=str))


def _cache_key(lab_id: int, endpoint: str, **params) -> str:
    param_str = json.dumps(params, sort_keys=True)
    h = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()[:8]
    return f"stats:{lab_id}:{endpoint}:{h}"


def daily_trends(lab_id: int, days: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "daily_trends", days=days)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(UTC) - timedelta(days=days)

    try:
        rows = db.execute(
            text("""
                    SELECT
                        DATE(lo.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Baghdad') AS day,
                        COUNT(DISTINCT lo.id)          AS orders,
                        COUNT(lr.id)                   AS tests,
                        COUNT(CASE WHEN lr.flag = 'critical' THEN 1 END) AS critical_tests,
                        COUNT(CASE WHEN lr.flag IN ('H','L','critical') THEN 1 END) AS abnormal_tests
                    FROM lab_orders lo
                    LEFT JOIN lab_results lr ON lr.order_id = lo.id
                    WHERE lo.lab_id = :lab_id
                      AND lo.created_at >= :cutoff
                    GROUP BY day
                    ORDER BY day ASC
                """),
            {"lab_id": lab_id, "cutoff": cutoff},
        ).fetchall()
        series = [
            {
                "date": str(r[0]),
                "orders": r[1],
                "tests": r[2],
                "critical_tests": r[3],
                "abnormal_tests": r[4],
            }
            for r in rows
        ]
    except Exception:
        logger.debug("daily_trends: raw SQL unsupported on this DB dialect — returning empty series")
        series = []

    result = {"days": days, "series": series, "data_points": len(series)}
    _cache_set(cache_key, result)
    return result


def test_frequency(lab_id: int, days: int, limit: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "test_frequency", days=days, limit=limit)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(UTC) - timedelta(days=days)

    rows = (
        db.query(
            LabResult.test_name,
            func.count(LabResult.id).label("count"),
            func.avg(LabResult.value).label("avg_value"),
            func.count(case((LabResult.flag == "critical", LabResult.id))).label("critical_count"),
            func.count(case((LabResult.flag.in_(["H", "L", "critical"]), LabResult.id))).label(
                "abnormal_count",
            ),
        )
        .join(LabOrder)
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.created_at >= cutoff,
        )
        .group_by(LabResult.test_name)
        .order_by(func.count(LabResult.id).desc())
        .limit(limit)
        .all()
    )

    tests = [
        {
            "test_name": r.test_name,
            "count": r.count,
            "avg_value": round(r.avg_value, 2) if r.avg_value is not None else None,
            "critical_count": r.critical_count,
            "abnormal_count": r.abnormal_count,
            "abnormal_rate": round(r.abnormal_count / r.count * 100, 1) if r.count else 0,
        }
        for r in rows
    ]

    result = {"days": days, "top_tests": tests}
    _cache_set(cache_key, result)
    return result


def flag_distribution(lab_id: int, days: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "flag_distribution", days=days)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(UTC) - timedelta(days=days)

    rows = (
        db.query(
            LabResult.flag,
            func.count(LabResult.id).label("count"),
        )
        .join(LabOrder)
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.created_at >= cutoff,
        )
        .group_by(LabResult.flag)
        .all()
    )

    total = sum(r.count for r in rows)
    distribution = {
        r.flag or "unknown": {
            "count": r.count,
            "percentage": round(r.count / total * 100, 1) if total else 0,
        }
        for r in rows
    }

    result = {
        "days": days,
        "total_results": total,
        "distribution": distribution,
    }
    _cache_set(cache_key, result)
    return result


def patient_growth(lab_id: int, days: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "patient_growth", days=days)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(UTC) - timedelta(days=days)

    try:
        rows = db.execute(
            text("""
                    SELECT
                        DATE_TRUNC('week', created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Baghdad') AS week_start,
                        COUNT(*) AS new_patients
                    FROM patients
                    WHERE lab_id = :lab_id
                      AND created_at >= :cutoff
                    GROUP BY week_start
                    ORDER BY week_start ASC
                """),
            {"lab_id": lab_id, "cutoff": cutoff},
        ).fetchall()
        series = [{"week_start": str(r[0]), "new_patients": r[1]} for r in rows]
        total_new = sum(r[1] for r in rows)
    except Exception:
        logger.debug("patient_growth: raw SQL unsupported on this DB dialect — returning empty series")
        series = []
        total_new = 0

    result = {
        "days": days,
        "total_new_patients": total_new,
        "weekly_series": series,
    }
    _cache_set(cache_key, result)
    return result


def stats_summary(lab_id: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "summary")
    cached = _cache_get(cache_key)
    if cached:
        return cached

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0
    total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0
    total_tests = (
        db.query(func.count(LabResult.id)).join(LabOrder).filter(LabOrder.lab_id == lab_id).scalar()
        or 0
    )
    total_critical = (
        db.query(func.count(LabResult.id))
        .join(LabOrder)
        .filter(LabOrder.lab_id == lab_id, LabResult.flag == "critical")
        .scalar()
        or 0
    )

    orders_today = (
        db.query(func.count(LabOrder.id))
        .filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= today_start)
        .scalar()
        or 0
    )

    orders_week = (
        db.query(func.count(LabOrder.id))
        .filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= week_start)
        .scalar()
        or 0
    )

    orders_month = (
        db.query(func.count(LabOrder.id))
        .filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= month_start)
        .scalar()
        or 0
    )

    critical_today = (
        db.query(func.count(LabResult.id))
        .join(LabOrder)
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.flag == "critical",
            LabResult.created_at >= today_start,
        )
        .scalar()
        or 0
    )

    result = {
        "totals": {
            "patients": total_patients,
            "orders": total_orders,
            "tests": total_tests,
            "critical_results": total_critical,
            "critical_rate_pct": round(total_critical / total_tests * 100, 2) if total_tests else 0,
        },
        "today": {
            "orders": orders_today,
            "critical_results": critical_today,
        },
        "this_week": {"orders": orders_week},
        "this_month": {"orders": orders_month},
        "generated_at": now.isoformat(),
    }
    _cache_set(cache_key, result, ttl=120)
    return result


def turnaround_times(lab_id: int, days: int, db: Session) -> dict:
    cache_key = _cache_key(lab_id, "turnaround", days=days)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(UTC) - timedelta(days=days)

    try:
        row = db.execute(
            text("""
                    SELECT
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 60)  AS avg_minutes,
                        MIN(EXTRACT(EPOCH FROM (updated_at - created_at)) / 60)  AS min_minutes,
                        MAX(EXTRACT(EPOCH FROM (updated_at - created_at)) / 60)  AS max_minutes,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (
                            ORDER BY EXTRACT(EPOCH FROM (updated_at - created_at)) / 60
                        ) AS median_minutes,
                        COUNT(*) AS completed_orders
                    FROM lab_orders
                    WHERE lab_id = :lab_id
                      AND status = 'completed'
                      AND created_at >= :cutoff
                      AND updated_at > created_at
                """),
            {"lab_id": lab_id, "cutoff": cutoff},
        ).fetchone()
        result = {
            "days": days,
            "avg_minutes": round(row[0], 1) if row[0] else None,
            "min_minutes": round(row[1], 1) if row[1] else None,
            "max_minutes": round(row[2], 1) if row[2] else None,
            "median_minutes": round(row[3], 1) if row[3] else None,
            "completed_orders_sampled": row[4] or 0,
        }
    except Exception:
        logger.debug("turnaround: raw SQL unsupported on this DB dialect — returning null metrics")
        result = {
            "days": days,
            "avg_minutes": None,
            "min_minutes": None,
            "max_minutes": None,
            "median_minutes": None,
            "completed_orders_sampled": 0,
        }

    _cache_set(cache_key, result, ttl=600)
    return result
