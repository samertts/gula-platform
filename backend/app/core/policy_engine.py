"""
GULA Platform — Policy Engine
================================
Governance layer that controls what the system (including AI components)
is allowed to do autonomously.

Every autonomous action MUST pass through evaluate_policy() before execution.
No action is permitted without an explicit policy decision.

Design principles:
  - Default DENY: unknown actions are blocked unless explicitly allowed
  - Environment-aware: production has stricter rules than development
  - Frequency-aware: repeated actions trigger escalation
  - Audit-first: every evaluation is logged regardless of outcome
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("gula.policy")

_ENV = os.getenv("ENV", "production")
_CONTROL_LAYER_ENABLED = os.getenv("CONTROL_LAYER_ENABLED", "true").lower() != "false"


# ─── Action taxonomy ─────────────────────────────────────────────────────────

class ActionType(str, Enum):
    # Code & deployment
    CODE_CHANGE     = "code_change"      # Any modification to source files
    CONFIG_CHANGE   = "config_change"    # .env, nginx, haproxy changes
    DEPLOY          = "deploy"           # Container restart / new image
    # Database
    DB_SCHEMA       = "db_schema"        # DDL: CREATE/ALTER/DROP
    DB_WRITE        = "db_write"         # DML: INSERT/UPDATE/DELETE via auto
    DB_POOL_RECYCLE = "db_pool_recycle"  # Dispose connection pool
    # Infrastructure
    AUTO_REPAIR     = "auto_repair"      # Any autonomous repair action
    SCALING         = "scaling"          # Add/remove backend instances
    CIRCUIT_RESET   = "circuit_reset"    # Force circuit breaker state
    # Cache & messaging
    CACHE_FLUSH     = "cache_flush"      # Flush Redis keyspace
    QUEUE_PURGE     = "queue_purge"      # Remove outbox events
    # AI-specific
    AI_AUTO_FIX     = "ai_auto_fix"     # Self-audit agent applies a patch
    AI_COMMIT       = "ai_commit"        # Self-audit agent commits
    AI_DECISION     = "ai_decision"      # Any AI autonomous decision
    # Security
    SECRET_ROTATION = "secret_rotation"  # Rotate JWT/encryption keys
    AUDIT_DELETE    = "audit_delete"     # Remove audit log entries (NEVER)


class RiskLevel(str, Enum):
    LOW      = "low"       # Safe to auto-approve in all environments
    MEDIUM   = "medium"    # Auto-approve in dev; require log in prod
    HIGH     = "high"      # Require human approval in production
    CRITICAL = "critical"  # Always blocked — requires out-of-band change


# ─── Policy table ────────────────────────────────────────────────────────────

# Maps ActionType → (risk_level, allow_in_prod)
# allow_in_prod=False means BLOCKED in production regardless of risk
_POLICY_TABLE: dict[ActionType, tuple[RiskLevel, bool]] = {
    ActionType.CODE_CHANGE:     (RiskLevel.CRITICAL, False),
    ActionType.CONFIG_CHANGE:   (RiskLevel.HIGH,     False),
    ActionType.DEPLOY:          (RiskLevel.HIGH,     False),
    ActionType.DB_SCHEMA:       (RiskLevel.CRITICAL, False),
    ActionType.DB_WRITE:        (RiskLevel.HIGH,     False),
    ActionType.DB_POOL_RECYCLE: (RiskLevel.MEDIUM,   True),
    ActionType.AUTO_REPAIR:     (RiskLevel.MEDIUM,   True),
    ActionType.SCALING:         (RiskLevel.MEDIUM,   True),
    ActionType.CIRCUIT_RESET:   (RiskLevel.MEDIUM,   True),
    ActionType.CACHE_FLUSH:     (RiskLevel.HIGH,     False),
    ActionType.QUEUE_PURGE:     (RiskLevel.HIGH,     False),
    ActionType.AI_AUTO_FIX:     (RiskLevel.CRITICAL, False),
    ActionType.AI_COMMIT:       (RiskLevel.CRITICAL, False),
    ActionType.AI_DECISION:     (RiskLevel.HIGH,     True),
    ActionType.SECRET_ROTATION: (RiskLevel.CRITICAL, False),
    ActionType.AUDIT_DELETE:    (RiskLevel.CRITICAL, False),  # NEVER
}

# Maximum times the same action type may auto-execute within one hour
# before triggering mandatory human review (repetition = potential loop)
_HOURLY_LIMITS: dict[ActionType, int] = {
    ActionType.AUTO_REPAIR:     10,
    ActionType.DB_POOL_RECYCLE:  3,
    ActionType.CIRCUIT_RESET:    5,
    ActionType.AI_DECISION:      5,
}


# ─── Frequency tracker ───────────────────────────────────────────────────────

@dataclass
class _ActionCounter:
    count:      int   = 0
    window_start: float = field(default_factory=time.monotonic)

    def increment_and_check(self, limit: int) -> bool:
        """Return True if limit exceeded."""
        now = time.monotonic()
        if now - self.window_start > 3600:
            self.count = 0
            self.window_start = now
        self.count += 1
        return self.count > limit


# ─── Policy decision ─────────────────────────────────────────────────────────

@dataclass
class PolicyDecision:
    allowed:     bool
    risk:        RiskLevel
    action:      ActionType
    reason:      str
    env:         str
    context:     dict
    ts:          float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "risk":    self.risk.value,
            "action":  self.action.value,
            "reason":  self.reason,
            "env":     self.env,
        }


# ─── Policy Engine singleton ─────────────────────────────────────────────────

class PolicyEngine:
    def __init__(self):
        self._counters: dict[ActionType, _ActionCounter] = {}
        self._decisions: list[dict] = []   # rolling log (last 200)
        self._blocked_total  = 0
        self._allowed_total  = 0

    def _record(self, decision: PolicyDecision):
        self._decisions.append({
            **decision.to_dict(),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(decision.ts)),
        })
        if len(self._decisions) > 200:
            self._decisions.pop(0)

        if decision.allowed:
            self._allowed_total += 1
            logger.info("[POLICY] ALLOWED  %s risk=%s | %s", decision.action.value, decision.risk.value, decision.reason)
        else:
            self._blocked_total += 1
            logger.warning("[POLICY] BLOCKED  %s risk=%s | %s", decision.action.value, decision.risk.value, decision.reason)

    def evaluate(
        self,
        action:  ActionType,
        context: Optional[dict] = None,
    ) -> PolicyDecision:
        """
        Evaluate whether an action is permitted.

        context may include:
          - env: override environment ("production" | "development" | "test")
          - dry_run: bool — simulate without executing
          - reason: human-readable justification
          - affects_data: bool
        """
        if not _CONTROL_LAYER_ENABLED:
            return PolicyDecision(True, RiskLevel.LOW, action, "control layer disabled", _ENV, context or {})

        ctx = context or {}
        env = ctx.get("env", _ENV)

        # Default deny for unknown actions
        if action not in _POLICY_TABLE:
            decision = PolicyDecision(False, RiskLevel.CRITICAL, action, "unknown action — default deny", env, ctx)
            self._record(decision)
            return decision

        risk, allow_in_prod = _POLICY_TABLE[action]

        # CRITICAL always blocked
        if risk == RiskLevel.CRITICAL:
            decision = PolicyDecision(False, risk, action, "CRITICAL risk — requires out-of-band change", env, ctx)
            self._record(decision)
            return decision

        # Production restriction
        if env == "production" and not allow_in_prod:
            decision = PolicyDecision(False, risk, action, f"blocked in production (risk={risk.value})", env, ctx)
            self._record(decision)
            return decision

        # Frequency / repetition guard
        limit = _HOURLY_LIMITS.get(action)
        if limit is not None:
            counter = self._counters.setdefault(action, _ActionCounter())
            if counter.increment_and_check(limit):
                decision = PolicyDecision(
                    False, RiskLevel.HIGH, action,
                    f"frequency limit {limit}/hour exceeded — possible repair loop — manual check required",
                    env, ctx,
                )
                self._record(decision)
                return decision

        # Kill switch
        from app.core.kill_switch import is_kill_switch_active
        if is_kill_switch_active():
            decision = PolicyDecision(False, risk, action, "kill switch ACTIVE — all autonomous actions halted", env, ctx)
            self._record(decision)
            return decision

        reason = ctx.get("reason", "auto-approved")
        decision = PolicyDecision(True, risk, action, reason, env, ctx)
        self._record(decision)
        return decision

    def stats(self) -> dict:
        return {
            "blocked_total":  self._blocked_total,
            "allowed_total":  self._allowed_total,
            "enabled":        _CONTROL_LAYER_ENABLED,
            "env":            _ENV,
            "recent_decisions": self._decisions[-10:],
            "frequency_counters": {
                k.value: {"count": v.count, "window_start": v.window_start}
                for k, v in self._counters.items()
            },
        }


# Singleton
policy_engine = PolicyEngine()


def evaluate_policy(action: ActionType, context: Optional[dict] = None) -> PolicyDecision:
    """Module-level convenience function."""
    return policy_engine.evaluate(action, context)
