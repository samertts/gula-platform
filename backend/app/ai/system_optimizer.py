"""
AI System Optimizer — GULA Platform
=====================================
Lightweight, server-safe performance monitoring and optimization engine.

Design:
  - Zero new dependencies: /proc (Linux stdlib) + httpx (already in requirements)
  - Metrics cached 30s, analysis cached 60s — safe to poll
  - Ollama is optional: falls back to rule-based analysis if unavailable
  - Ollama calls rate-limited (1 per 60s) and hard-timeout (15s)
  - Never blocks the event loop — all I/O is async or reads tiny /proc files
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("gula.ai.optimizer")

# ─── Configuration (all overridable via env) ──────────────────────────────────

OLLAMA_BASE_URL            = os.getenv("OLLAMA_BASE_URL",            "http://host.docker.internal:11434")
OLLAMA_MODEL               = os.getenv("OLLAMA_MODEL",               "llama3.2:1b")  # tiny & fast
OLLAMA_TIMEOUT             = float(os.getenv("OLLAMA_TIMEOUT",       "15"))   # seconds
OLLAMA_RATE_LIMIT_SECONDS  = int(os.getenv("OLLAMA_RATE_LIMIT_SECONDS", "60"))
METRICS_CACHE_SECONDS      = int(os.getenv("METRICS_CACHE_SECONDS",  "30"))
ANALYSIS_CACHE_SECONDS     = int(os.getenv("ANALYSIS_CACHE_SECONDS", "60"))

# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class CPUMetrics:
    load_1m:  float
    load_5m:  float
    load_15m: float
    num_cpus: int

    @property
    def load_per_cpu(self) -> float:
        return round(self.load_1m / max(self.num_cpus, 1), 2)

    @property
    def status(self) -> str:
        r = self.load_per_cpu
        if r > 2.0:  return "critical"
        if r > 1.0:  return "high"
        if r > 0.7:  return "moderate"
        return "healthy"


@dataclass
class MemoryMetrics:
    total_mb:     int
    available_mb: int
    used_mb:      int
    used_pct:     float

    @property
    def status(self) -> str:
        if self.used_pct > 90:  return "critical"
        if self.used_pct > 80:  return "high"
        if self.used_pct > 70:  return "moderate"
        return "healthy"


@dataclass
class DBMetrics:
    pool_size:   int
    checked_out: int
    overflow:    int
    checked_in:  int

    @property
    def utilization_pct(self) -> float:
        capacity = max(self.pool_size + max(self.overflow, 0), 1)
        return round(self.checked_out / capacity * 100, 1)

    @property
    def status(self) -> str:
        u = self.utilization_pct
        if u > 90:  return "critical"
        if u > 70:  return "high"
        if u > 50:  return "moderate"
        return "healthy"


@dataclass
class SystemSnapshot:
    cpu:    CPUMetrics
    memory: MemoryMetrics
    db:     DBMetrics
    collected_at: float = field(default_factory=time.time)

    @property
    def overall_status(self) -> str:
        statuses = {self.cpu.status, self.memory.status, self.db.status}
        for level in ("critical", "high", "moderate"):
            if level in statuses:
                return level
        return "healthy"


# ─── /proc Collectors ─────────────────────────────────────────────────────────

def _collect_cpu() -> CPUMetrics:
    try:
        parts = open("/proc/loadavg").read().split()
        load_1m, load_5m, load_15m = float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        load_1m = load_5m = load_15m = 0.0

    try:
        num_cpus = sum(1 for line in open("/proc/cpuinfo") if line.startswith("processor"))
    except Exception:
        num_cpus = 1

    return CPUMetrics(load_1m=load_1m, load_5m=load_5m, load_15m=load_15m,
                      num_cpus=max(num_cpus, 1))


def _collect_memory() -> MemoryMetrics:
    mem: Dict[str, int] = {}
    try:
        for line in open("/proc/meminfo"):
            parts = line.split()
            if len(parts) >= 2:
                mem[parts[0].rstrip(":")] = int(parts[1])  # kB
    except Exception:
        pass

    total_mb     = mem.get("MemTotal",     0) // 1024
    available_mb = mem.get("MemAvailable", 0) // 1024
    used_mb      = total_mb - available_mb
    used_pct     = round(used_mb / max(total_mb, 1) * 100, 1)

    return MemoryMetrics(total_mb=total_mb, available_mb=available_mb,
                         used_mb=used_mb, used_pct=used_pct)


def _collect_db() -> DBMetrics:
    try:
        from app.database import get_pool_status
        p = get_pool_status()
        return DBMetrics(pool_size=p["pool_size"], checked_out=p["checked_out"],
                         overflow=p["overflow"], checked_in=p["checked_in"])
    except Exception:
        return DBMetrics(pool_size=0, checked_out=0, overflow=0, checked_in=0)


# ─── Snapshot Cache ────────────────────────────────────────────────────────────

_snapshot_cache: Optional[SystemSnapshot] = None
_snapshot_ts: float = 0.0


def get_snapshot() -> SystemSnapshot:
    """Return cached metrics (refreshed every METRICS_CACHE_SECONDS)."""
    global _snapshot_cache, _snapshot_ts
    now = time.time()
    if _snapshot_cache is None or (now - _snapshot_ts) > METRICS_CACHE_SECONDS:
        _snapshot_cache = SystemSnapshot(
            cpu=_collect_cpu(),
            memory=_collect_memory(),
            db=_collect_db(),
        )
        _snapshot_ts = now
    return _snapshot_cache


# ─── Rule-Based Recommendations ───────────────────────────────────────────────

def _rule_recommendations(snap: SystemSnapshot) -> List[Dict[str, str]]:
    recs: List[Dict[str, str]] = []

    if snap.cpu.status == "critical":
        recs.append({
            "severity": "critical", "area": "cpu",
            "message":    f"CPU load/core is {snap.cpu.load_per_cpu:.1f}x — reduce WEB_CONCURRENCY or scale horizontally.",
            "message_ar": f"حمل المعالج {snap.cpu.load_per_cpu:.1f}x — قلّل عدد العمال أو وسّع الخادم.",
        })
    elif snap.cpu.status == "high":
        recs.append({
            "severity": "warning", "area": "cpu",
            "message":    f"CPU load/core is {snap.cpu.load_per_cpu:.1f}x — enable response caching or tune Nginx worker_processes.",
            "message_ar": f"حمل المعالج {snap.cpu.load_per_cpu:.1f}x — فعّل التخزين المؤقت أو اضبط worker_processes.",
        })

    if snap.memory.status == "critical":
        recs.append({
            "severity": "critical", "area": "memory",
            "message":    f"Memory at {snap.memory.used_pct}% — restart workers or add RAM.",
            "message_ar": f"الذاكرة {snap.memory.used_pct}% — أعد تشغيل العمال أو أضف ذاكرة.",
        })
    elif snap.memory.status == "high":
        recs.append({
            "severity": "warning", "area": "memory",
            "message":    f"Memory at {snap.memory.used_pct}% — check for leaks, lower DB_POOL_SIZE.",
            "message_ar": f"الذاكرة {snap.memory.used_pct}% — افحص تسرّبات الذاكرة، قلّل DB_POOL_SIZE.",
        })

    if snap.db.status == "critical":
        recs.append({
            "severity": "critical", "area": "database",
            "message":    f"DB pool {snap.db.utilization_pct}% full — increase DB_MAX_OVERFLOW or investigate slow queries.",
            "message_ar": f"مجموعة DB {snap.db.utilization_pct}% — زد DB_MAX_OVERFLOW أو افحص الاستعلامات البطيئة.",
        })
    elif snap.db.status == "high":
        recs.append({
            "severity": "warning", "area": "database",
            "message":    f"DB pool {snap.db.utilization_pct}% utilized — monitor for saturation.",
            "message_ar": f"استخدام مجموعة DB {snap.db.utilization_pct}% — راقب للتشبع.",
        })

    if not recs:
        recs.append({
            "severity": "info", "area": "system",
            "message":    "System is operating within normal parameters.",
            "message_ar": "النظام يعمل ضمن المعاملات الطبيعية.",
        })

    return recs


# ─── Ollama Integration ────────────────────────────────────────────────────────

_last_ollama_call: float = 0.0


async def _ask_ollama(prompt: str) -> Optional[str]:
    """
    Call local Ollama. Never raises — returns None on any failure.
    Rate-limited: max 1 call per OLLAMA_RATE_LIMIT_SECONDS.
    Hard timeout: OLLAMA_TIMEOUT seconds.
    """
    global _last_ollama_call
    now = time.time()

    if (now - _last_ollama_call) < OLLAMA_RATE_LIMIT_SECONDS:
        remaining = int(OLLAMA_RATE_LIMIT_SECONDS - (now - _last_ollama_call))
        logger.debug("Ollama rate-limited — %ds remaining", remaining)
        return None

    _last_ollama_call = now
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 200, "temperature": 0.3},
                },
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip() or None
    except Exception as exc:
        logger.debug("Ollama unavailable (%s) — using rule-based fallback", exc)

    return None


def _build_ollama_prompt(snap: SystemSnapshot, recs: List[Dict]) -> str:
    issues = [r["message"] for r in recs if r["severity"] in ("critical", "warning")]
    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "- No issues detected"
    return (
        "You are a system performance advisor for a medical lab platform "
        "(FastAPI + PostgreSQL + Docker on Linux).\n"
        f"Current overall status: {snap.overall_status}\n"
        f"CPU load/core: {snap.cpu.load_per_cpu:.2f}x ({snap.cpu.num_cpus} CPUs)\n"
        f"Memory used: {snap.memory.used_pct:.1f}% of {snap.memory.total_mb} MB\n"
        f"DB pool: {snap.db.utilization_pct:.1f}% utilized "
        f"({snap.db.checked_out} active / {snap.db.pool_size} pool size)\n"
        f"Detected issues:\n{issues_text}\n\n"
        "In 2-3 concise sentences, give the system administrator a clear optimization recommendation."
    )


# ─── Analysis Cache ────────────────────────────────────────────────────────────

_analysis_cache: Optional[Dict[str, Any]] = None
_analysis_ts: float = 0.0


async def analyze(use_ai: bool = True) -> Dict[str, Any]:
    """
    Full system analysis with optional Ollama-powered narrative.
    Cached for ANALYSIS_CACHE_SECONDS — safe to poll repeatedly.
    """
    global _analysis_cache, _analysis_ts
    now = time.time()

    if _analysis_cache and (now - _analysis_ts) < ANALYSIS_CACHE_SECONDS:
        return {**_analysis_cache, "cached": True}

    snap = get_snapshot()
    recs = _rule_recommendations(snap)

    ai_summary: Optional[str] = None
    if use_ai:
        ai_summary = await _ask_ollama(_build_ollama_prompt(snap, recs))

    result: Dict[str, Any] = {
        "status":       snap.overall_status,
        "collected_at": snap.collected_at,
        "metrics": {
            "cpu": {
                "load_1m":      snap.cpu.load_1m,
                "load_5m":      snap.cpu.load_5m,
                "load_15m":     snap.cpu.load_15m,
                "num_cpus":     snap.cpu.num_cpus,
                "load_per_cpu": snap.cpu.load_per_cpu,
                "status":       snap.cpu.status,
            },
            "memory": {
                "total_mb":     snap.memory.total_mb,
                "used_mb":      snap.memory.used_mb,
                "available_mb": snap.memory.available_mb,
                "used_pct":     snap.memory.used_pct,
                "status":       snap.memory.status,
            },
            "database": {
                "pool_size":        snap.db.pool_size,
                "checked_out":      snap.db.checked_out,
                "overflow":         snap.db.overflow,
                "utilization_pct":  snap.db.utilization_pct,
                "status":           snap.db.status,
            },
        },
        "recommendations": recs,
        "ai_summary":      ai_summary,
        "ai_model":        OLLAMA_MODEL if ai_summary else None,
        "ai_available":    ai_summary is not None,
        "cached":          False,
    }

    _analysis_cache = result
    _analysis_ts    = now
    return result
