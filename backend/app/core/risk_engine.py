"""
GULA Platform — Risk Scoring Engine
=======================================
Computes a numeric risk score (0–10) for any proposed action before execution.

Score thresholds:
  0–2  → LOW    auto-approve in all envs
  3–5  → MEDIUM auto-approve in dev; log in prod
  6–8  → HIGH   human approval required in prod
  9–10 → CRITICAL always blocked

Risk factors:
  - Environment (production adds +3)
  - Data impact (touching patient records adds +3)
  - Frequency (repeated actions add +2 per occurrence)
  - Blast radius (affects all users adds +2)
  - Reversibility (irreversible adds +2)
  - Recency (last similar action < 5min adds +1)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger("gula.risk")


@dataclass
class RiskAssessment:
    score: int  # 0–10
    level: str  # "low" | "medium" | "high" | "critical"
    factors: list[str]  # human-readable breakdown
    action: str
    recommended: str  # "allow" | "warn" | "block"

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level,
            "factors": self.factors,
            "action": self.action,
            "recommended": self.recommended,
        }


# Recent action tracker for recency scoring
_recent_actions: dict[str, float] = {}  # action_type → last_ts


def compute_risk(
    action: str,
    context: dict | None = None,
) -> RiskAssessment:
    """
    Compute risk score for an action.

    Context keys (all optional, default False/0):
      env:            "production" | "development" | "test"
      affects_data:   bool — touches patient records
      all_users:      bool — blast radius is all tenants
      reversible:     bool — can be undone (default True)
      frequency:      int  — how many times in the last hour
      dry_run:        bool — simulation only
    """
    ctx = context or {}
    score = 0
    factors = []

    env = ctx.get("env", "production")

    # Dry run — zero risk
    if ctx.get("dry_run"):
        return RiskAssessment(0, "low", ["dry_run=true"], action, "allow")

    # ── Environment ──────────────────────────────────────────────────────────
    if env == "production":
        score += 3
        factors.append("+3 production environment")
    elif env == "development":
        score += 0
        factors.append("+0 development environment")

    # ── Data impact ──────────────────────────────────────────────────────────
    if ctx.get("affects_data"):
        score += 3
        factors.append("+3 affects patient data")

    # ── Blast radius ─────────────────────────────────────────────────────────
    if ctx.get("all_users"):
        score += 2
        factors.append("+2 affects all tenants")

    # ── Reversibility ────────────────────────────────────────────────────────
    if not ctx.get("reversible", True):
        score += 2
        factors.append("+2 irreversible operation")

    # ── Frequency ────────────────────────────────────────────────────────────
    freq = ctx.get("frequency", 0)
    if freq > 5:
        score += 2
        factors.append(f"+2 high frequency ({freq}/hr)")
    elif freq > 2:
        score += 1
        factors.append(f"+1 moderate frequency ({freq}/hr)")

    # ── Recency ──────────────────────────────────────────────────────────────
    last_ts = _recent_actions.get(action, 0)
    if last_ts and (time.time() - last_ts) < 300:
        score += 1
        factors.append("+1 repeated within 5 min")
    _recent_actions[action] = time.time()

    # ── Clamp and classify ───────────────────────────────────────────────────
    score = min(score, 10)

    if score <= 2:
        level, recommended = "low", "allow"
    elif score <= 5:
        level, recommended = "medium", "warn"
    elif score <= 8:
        level, recommended = "high", "block" if env == "production" else "warn"
    else:
        level, recommended = "critical", "block"

    assessment = RiskAssessment(score, level, factors, action, recommended)

    if score >= 6:
        logger.warning("[RISK] %s score=%d (%s) factors=%s", action, score, level, factors)
    elif score >= 3:
        logger.info("[RISK] %s score=%d (%s)", action, score, level)

    return assessment


def assess_repair(repair_name: str, env: str = "production", frequency: int = 0) -> RiskAssessment:
    """Quick scorer for auto_repair actions."""
    return compute_risk(
        "auto_repair." + repair_name,
        {
            "env": env,
            "reversible": True,
            "frequency": frequency,
        },
    )
