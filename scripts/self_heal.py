#!/usr/bin/env python3
"""
GULA Platform — Autonomous Self-Healing System (ASHS)
======================================================
Detects, diagnoses, acts, verifies, and logs — every minute.

Decision Policy:
  LOW-RISK   → auto-fix silently
  MEDIUM     → auto-fix + log warning
  HIGH       → contain (pause writes) + alert + require human

Run every minute via cron:
    * * * * * cd ~/gula-platform && python3 scripts/self_heal.py >> /var/log/gula-ashs.log 2>&1

Or as a daemon (blocks):
    python3 scripts/self_heal.py --watch --interval 60

Runbook actions (all are idempotent):
  restart_backend   — docker compose restart gula-backend
  restart_worker    — docker compose restart gula-backend   (worker is embedded)
  restart_gateway   — docker compose restart api-gateway
  restart_redis     — docker compose restart redis
  reduce_concurrency — sets WEB_CONCURRENCY=1 in a temp override file (requires restart)
  safe_mode         — creates /tmp/gula_safe_mode (backend reads this → 503 on writes)
  clear_safe_mode   — removes /tmp/gula_safe_mode

Requirements: requests  (pip3 install requests)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import requests
from backend.app._compat import UTC

# TLS certificate verification is intentionally fail-closed. Local health checks may
# use the default HTTP endpoint, but HTTPS connections must never disable validation.
if os.getenv("ASHS_VERIFY_TLS", "true").lower() != "true":
    raise RuntimeError("ASHS_VERIFY_TLS=false is not permitted; use a trusted CA bundle")
TLS_VERIFY: bool = True

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ASHS] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("ashs")

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL    = os.getenv("ASHS_BASE_URL",   "http://localhost:8080")
COMPOSE_DIR = os.getenv("ASHS_COMPOSE_DIR", Path(__file__).resolve().parent.parent)
SAFE_MODE_FILE = Path("/tmp/gula_safe_mode")
INCIDENT_LOG   = Path("/var/log/gula-incidents.jsonl")

HEALTH_TIMEOUT = 8   # seconds


# ── Risk levels ───────────────────────────────────────────────────────────────

class Risk(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ── Signal ────────────────────────────────────────────────────────────────────

@dataclass
class Signal:
    name:      str
    ok:        bool
    value:     object = None
    detail:    str    = ""
    risk:      Risk   = Risk.LOW


# ── Incident record ───────────────────────────────────────────────────────────

@dataclass
class Incident:
    ts:       str
    signal:   str
    detail:   str
    risk:     str
    actions:  list[str] = field(default_factory=list)
    verified: bool = False


def log_incident(inc: Incident) -> None:
    """Append incident to JSONL file for later analysis."""
    try:
        INCIDENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with INCIDENT_LOG.open("a") as f:
            f.write(json.dumps(inc.__dict__) + "\n")
    except Exception as e:
        log.warning("Could not write incident log: %s", e)


# ── Docker helpers ────────────────────────────────────────────────────────────

def _compose(args: list[str], timeout: int = 60) -> bool:
    try:
        r = subprocess.run(
            ["docker", "compose", *args],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(COMPOSE_DIR),
        )
        if r.returncode != 0:
            log.warning("docker compose %s failed: %s", " ".join(args), r.stderr[:200])
        return r.returncode == 0
    except Exception as exc:
        log.error("docker compose %s error: %s", " ".join(args), exc)
        return False


def restart_service(name: str) -> bool:
    log.info("ACTION: restarting %s", name)
    return _compose(["restart", name])


def service_running(name: str) -> bool:
    r = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True, text=True, cwd=str(COMPOSE_DIR),
    )
    return name in r.stdout


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(path: str, timeout: int = HEALTH_TIMEOUT) -> dict | None:
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=timeout, verify=TLS_VERIFY)
        if r.status_code == 200:
            return r.json()
        return {"__status": r.status_code}
    except Exception:
        return None


# ── Detection ─────────────────────────────────────────────────────────────────

def detect() -> list[Signal]:
    """
    Collect all signals. Returns list of Signal objects.
    Each signal is either OK or describes a problem.
    """
    signals: list[Signal] = []

    # ── 1. API Gateway reachable ─────────────────────────────────────────────
    health = _get("/health")
    if health is None:
        signals.append(Signal("api_unreachable", False, risk=Risk.HIGH,
                               detail="gateway not responding"))
    else:
        signals.append(Signal("api_reachable", True))

        # ── 2. System ready ──────────────────────────────────────────────────
        ready = health.get("system_ready")
        if ready is not True:
            signals.append(Signal("system_not_ready", False, value=ready, risk=Risk.HIGH,
                                   detail=f"system_ready={ready}"))
        else:
            signals.append(Signal("system_ready", True))

        # ── 3. Degraded mode ─────────────────────────────────────────────────
        degraded = health.get("degraded_mode", False)
        if degraded:
            signals.append(Signal("degraded_mode", False, risk=Risk.MEDIUM,
                                   detail=str(health.get("degraded_reason", "unknown"))))
        else:
            signals.append(Signal("degraded_mode_off", True))

        # ── 4. DB latency ────────────────────────────────────────────────────
        db_ms = health.get("db_latency_ms", 0)
        if db_ms and db_ms > 500:
            signals.append(Signal("db_slow", False, value=db_ms, risk=Risk.MEDIUM,
                                   detail=f"db_latency={db_ms}ms"))
        elif db_ms and db_ms > 1000:
            signals.append(Signal("db_very_slow", False, value=db_ms, risk=Risk.HIGH,
                                   detail=f"db_latency={db_ms}ms"))
        else:
            signals.append(Signal("db_latency_ok", True, value=db_ms))

    # ── 5. Deep health (queue backlog) ────────────────────────────────────────
    deep = _get("/health/deep")
    if deep and isinstance(deep.get("queue_backlog"), int):
        backlog = deep["queue_backlog"]
        if backlog > 1000:
            signals.append(Signal("queue_exploded", False, value=backlog, risk=Risk.HIGH,
                                   detail=f"queue_backlog={backlog}"))
        elif backlog > 100:
            signals.append(Signal("queue_growing", False, value=backlog, risk=Risk.MEDIUM,
                                   detail=f"queue_backlog={backlog}"))
        else:
            signals.append(Signal("queue_healthy", True, value=backlog))

    # ── 6. Docker container states ────────────────────────────────────────────
    for svc in ("gula-backend", "api-gateway", "gula-postgres", "redis"):
        running = service_running(svc)
        signals.append(Signal(
            f"container_{svc.replace('-','_')}_running", running,
            risk=Risk.HIGH if not running else Risk.LOW,
            detail="" if running else f"{svc} container is not running",
        ))

    return signals


# ── Diagnosis → Decision ──────────────────────────────────────────────────────

@dataclass
class Decision:
    signal:   Signal
    actions:  list[str]
    risk:     Risk
    rationale: str


def diagnose(signals: list[Signal]) -> list[Decision]:
    """Map failed signals to runbook actions."""
    decisions: list[Decision] = []
    failed = {s.name: s for s in signals if not s.ok}

    if "api_unreachable" in failed:
        decisions.append(Decision(
            signal=failed["api_unreachable"],
            actions=["restart_gateway", "restart_backend"],
            risk=Risk.HIGH,
            rationale="API gateway not responding — restart both layers",
        ))

    if "system_not_ready" in failed:
        decisions.append(Decision(
            signal=failed["system_not_ready"],
            actions=["restart_backend"],
            risk=Risk.MEDIUM,
            rationale="Backend stuck in not-ready — restart to re-run startup_guard",
        ))

    if "container_gula_backend_running" in failed:
        decisions.append(Decision(
            signal=failed["container_gula_backend_running"],
            actions=["restart_backend"],
            risk=Risk.HIGH,
            rationale="Backend container is down — restart",
        ))

    if "container_api_gateway_running" in failed:
        decisions.append(Decision(
            signal=failed["container_api_gateway_running"],
            actions=["restart_gateway"],
            risk=Risk.HIGH,
            rationale="api-gateway container is down — restart",
        ))

    if "container_redis_running" in failed:
        decisions.append(Decision(
            signal=failed["container_redis_running"],
            actions=["restart_redis"],
            risk=Risk.MEDIUM,
            rationale="Redis down — restart (backend falls back to in-memory)",
        ))

    if "queue_exploded" in failed:
        decisions.append(Decision(
            signal=failed["queue_exploded"],
            actions=["restart_backend"],
            risk=Risk.HIGH,
            rationale="Queue backlog >1000 — worker may be stuck, restart backend",
        ))

    if "db_very_slow" in failed:
        decisions.append(Decision(
            signal=failed["db_very_slow"],
            actions=["safe_mode"],
            risk=Risk.HIGH,
            rationale="DB latency >1s — enter safe mode to prevent write amplification",
        ))

    if "db_slow" in failed and "db_very_slow" not in failed:
        decisions.append(Decision(
            signal=failed["db_slow"],
            actions=[],  # monitor only — no auto-action for moderate slowness
            risk=Risk.MEDIUM,
            rationale="DB latency 500-999ms — monitoring, no action yet",
        ))

    return decisions


# ── Action Engine ─────────────────────────────────────────────────────────────

SAFE_MODE_ALREADY_ACTIVE = False


def execute(decision: Decision, dry_run: bool = False) -> list[str]:
    """Execute runbook actions. Returns list of actions taken."""
    taken: list[str] = []

    for action in decision.actions:
        if dry_run:
            log.info("DRY-RUN: would execute '%s' (risk=%s)", action, decision.risk.value)
            taken.append(f"dry:{action}")
            continue

        if action == "restart_backend":
            if restart_service("gula-backend"):
                taken.append("restart_backend")
                time.sleep(5)  # brief settle time

        elif action == "restart_gateway":
            if restart_service("api-gateway"):
                taken.append("restart_gateway")
                time.sleep(3)

        elif action == "restart_redis":
            if restart_service("redis"):
                taken.append("restart_redis")
                time.sleep(2)

        elif action == "safe_mode":
            SAFE_MODE_FILE.touch()
            taken.append("safe_mode_activated")
            log.warning("SAFE MODE ACTIVATED — writes may return 503 until cleared")

        elif action == "clear_safe_mode" and SAFE_MODE_FILE.exists():
            SAFE_MODE_FILE.unlink()
            taken.append("safe_mode_cleared")

    return taken


# ── Verification ──────────────────────────────────────────────────────────────

def verify_recovery(actions_taken: list[str]) -> bool:
    """After actions, confirm the system is back to healthy."""
    if not actions_taken:
        return True

    log.info("Verifying recovery after actions: %s", actions_taken)
    time.sleep(8)  # allow services to stabilise

    health = _get("/health")
    if health is None:
        log.error("VERIFY FAILED: API still unreachable after actions")
        return False

    ready = health.get("system_ready")
    if ready is not True:
        log.warning("VERIFY: system_ready=%s after actions", ready)
        return False

    log.info("VERIFY OK: system_ready=True after actions")
    return True


# ── Alert ─────────────────────────────────────────────────────────────────────

def alert(incident: Incident) -> None:
    """
    Send alert for HIGH-risk incidents.
    Extend this to POST to Slack/Telegram webhook if ASHS_WEBHOOK_URL is set.
    """
    webhook = os.getenv("ASHS_WEBHOOK_URL", "")
    if not webhook:
        log.warning("ALERT (no webhook configured): %s — %s", incident.signal, incident.detail)
        return

    payload = {
        "text": (
            f"🚨 *GULA ASHS ALERT*\n"
            f"Signal: `{incident.signal}`\n"
            f"Detail: {incident.detail}\n"
            f"Risk: `{incident.risk}`\n"
            f"Actions: {', '.join(incident.actions) or 'none'}\n"
            f"Verified: {'✅' if incident.verified else '❌'}\n"
            f"Time: {incident.ts}"
        )
    }
    try:
        requests.post(webhook, json=payload, timeout=5)
    except Exception as exc:
        log.warning("Webhook delivery failed: %s", exc)


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_cycle(dry_run: bool = False) -> int:
    """
    One detection → diagnosis → action → verify cycle.
    Returns count of unresolved incidents.
    """
    ts = datetime.now(UTC).isoformat()
    signals = detect()

    failures = [s for s in signals if not s.ok]
    if not failures:
        # All green — if safe mode was set by a prior cycle, clear it
        if SAFE_MODE_FILE.exists():
            SAFE_MODE_FILE.unlink()
            log.info("Safe mode cleared — system fully healthy")
        else:
            log.info("All signals OK — no action required")
        return 0

    decisions = diagnose(signals)
    unresolved = 0

    for dec in decisions:
        log.warning(
            "INCIDENT signal=%s risk=%s rationale=%s",
            dec.signal.name, dec.risk.value, dec.rationale,
        )

        if dec.risk == Risk.HIGH and not dec.actions:
            log.error("HIGH-RISK signal with no runbook: %s — HUMAN INTERVENTION REQUIRED",
                      dec.signal.name)
            unresolved += 1
            continue

        actions_taken = execute(dec, dry_run=dry_run)

        if actions_taken:
            verified = verify_recovery(actions_taken)
        else:
            verified = True  # monitor-only decision

        inc = Incident(
            ts=ts,
            signal=dec.signal.name,
            detail=dec.signal.detail,
            risk=dec.risk.value,
            actions=actions_taken,
            verified=verified,
        )
        log_incident(inc)

        if dec.risk == Risk.HIGH:
            alert(inc)

        if not verified:
            log.error("Recovery verification FAILED for %s — may need human review",
                      dec.signal.name)
            unresolved += 1

    # Log unresolved failures that had no matching decision
    decided_signals = {d.signal.name for d in decisions}
    for sig in failures:
        if sig.name not in decided_signals:
            log.warning("Unmatched signal (no runbook): %s — %s", sig.name, sig.detail)

    return unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description="GULA Autonomous Self-Healing System")
    parser.add_argument("--base", default=BASE_URL,
                        help=f"API gateway base URL (default: {BASE_URL})")
    parser.add_argument("--compose-dir", default=str(COMPOSE_DIR),
                        help="Path to docker-compose project directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Detect and diagnose only — do not execute any actions")
    parser.add_argument("--watch", action="store_true",
                        help="Run continuously (daemon mode)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Seconds between cycles in watch mode (default: 60)")
    args = parser.parse_args()

    # Override module-level config with CLI args
    import sys as _sys
    _mod = _sys.modules[__name__]
    _mod.BASE_URL    = args.base
    _mod.COMPOSE_DIR = Path(args.compose_dir)

    if args.watch:
        log.info("ASHS daemon started (interval=%ds dry_run=%s)", args.interval, args.dry_run)
        while True:
            try:
                run_cycle(dry_run=args.dry_run)
            except KeyboardInterrupt:
                log.info("ASHS stopped by user")
                return 0
            except Exception as exc:
                log.error("Unexpected error in cycle: %s", exc)
            time.sleep(args.interval)
    else:
        unresolved = run_cycle(dry_run=args.dry_run)
        return 1 if unresolved > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
