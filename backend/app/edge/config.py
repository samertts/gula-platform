"""Edge platform configuration — env-driven, hard-fail-safe.

All edge endpoints reject traffic when EDGE_KILL_SWITCH is enabled, which is
the global "stop everything" lever (Section 20 — Feature Flags / kill switch).

Per-tenant kill switches live in the `edge_policies` table; the global switch
here trumps any per-tenant setting.
"""

from __future__ import annotations

import os

# ── Global toggles ────────────────────────────────────────────────────────────

# Master enable. When False, edge HTTP endpoints respond 503 with a clear
# message but do NOT break the rest of the platform.
EDGE_ENABLED: bool = os.getenv("EDGE_ENABLED", "true").lower() == "true"

# Global emergency kill switch — overrides per-tenant policies. Use this when
# a vulnerability is suspected in the agent fleet.
EDGE_KILL_SWITCH: bool = os.getenv("EDGE_KILL_SWITCH", "false").lower() == "true"

# ── Heartbeat / health ────────────────────────────────────────────────────────

# Maximum interval (seconds) between agent heartbeats before it's marked offline.
EDGE_HEARTBEAT_TIMEOUT_S: int = int(os.getenv("EDGE_HEARTBEAT_TIMEOUT_S", "180"))

# Telemetry retention — sweeper deletes rows older than this.
EDGE_TELEMETRY_RETENTION_DAYS: int = int(os.getenv("EDGE_TELEMETRY_RETENTION_DAYS", "14"))

# Stale-task reaper — tasks dispatched longer than (timeout_s + grace) without
# completion are flipped back to `pending` (or `failed` if attempts exhausted).
EDGE_DISPATCH_GRACE_S: int = int(os.getenv("EDGE_DISPATCH_GRACE_S", "30"))

# ── Trust scoring ─────────────────────────────────────────────────────────────

EDGE_TRUST_INITIAL: float = float(os.getenv("EDGE_TRUST_INITIAL", "50.0"))
EDGE_TRUST_MAX: float = 100.0
EDGE_TRUST_MIN: float = 0.0
EDGE_TRUST_QUARANTINE_BELOW: float = float(os.getenv("EDGE_TRUST_QUARANTINE_BELOW", "20.0"))

# ── Agent token lifetime ───────────────────────────────────────────────────────

try:
    EDGE_AGENT_TOKEN_TTL_S: int = int(os.getenv("EDGE_AGENT_TOKEN_TTL_S", "86400"))
except ValueError as exc:
    raise RuntimeError("EDGE_AGENT_TOKEN_TTL_S must be an integer") from exc
if not 300 <= EDGE_AGENT_TOKEN_TTL_S <= 604800:
    raise RuntimeError("EDGE_AGENT_TOKEN_TTL_S must be between 300 and 604800 seconds")

# ── Task signing ──────────────────────────────────────────────────────────────

# Tasks are HMAC-signed with this secret. Defaults to SECRET_KEY for safety
# (no silent fallback — see config.py weak-secret detection).
def get_task_signing_key() -> bytes:
    """Return the secret used to sign edge tasks. Reads at call time so
    rotated secrets pick up on the next dispatch.
    """
    key = os.getenv("EDGE_TASK_SIGNING_KEY") or os.getenv("SECRET_KEY", "")
    if not key:
        raise RuntimeError("EDGE_TASK_SIGNING_KEY (or SECRET_KEY) must be set for task signing")
    return key.encode("utf-8")


# ── Allowed task kinds ────────────────────────────────────────────────────────

# Strict allowlist — agents reject any kind not in this set. New kinds must be
# added explicitly (Section 12 — Security Model: command allowlist only).
ALLOWED_TASK_KINDS: frozenset[str] = frozenset(
    {
        # AI inference (local model)
        "ai.summarize_report",
        "ai.translate",
        "ai.transcribe",
        "ai.classify",
        "ai.extract_lab_values",
        "ai.embed",
        # Lightweight processing
        "image.thumbnail",
        "pdf.extract_text",
        # Maintenance
        "agent.self_update",
        "agent.warmup_model",
        "agent.gc",
        # Diagnostics
        "diag.ping",
        "diag.benchmark",
    },
)


# ── Privacy levels ────────────────────────────────────────────────────────────

# A task tagged "phi" must NEVER leave the device — scheduler refuses to send it
# to a device whose trust score is below the highest threshold.
PRIVACY_MIN_TRUST: dict[str, float] = {
    "standard": 0.0,
    "sensitive": 60.0,
    "phi": 85.0,
}
