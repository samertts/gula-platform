"""
Epidemiology Service — GULA Platform
======================================
Outbreak detection with two complementary algorithms:

1. **Incidence-rate ratio** (always available)
   Fast, requires only current window data.
   Alert when observed_abnormal / expected >= alert_ratio.

2. **Z-score** (when historical baseline data is supplied)
   More robust: accounts for natural variance in the baseline period.
   Alert when z = (observed - mean) / std >= z_threshold.
   Falls back to ratio method if std == 0 or history is too short.

Neither algorithm accounts for seasonality or population size — this service
is an early-warning flag, not a definitive epidemiological analysis.
"""
from __future__ import annotations

import math
from typing import Sequence


_ABNORMAL_FLAGS = {"H", "L", "critical", "high", "low"}


def _count_abnormal(records: Sequence[dict], test_code: str) -> int:
    return sum(
        1 for r in records
        if (not test_code or str(r.get("test_code", "")).lower() == test_code.lower())
        and str(r.get("flag", "")).strip() in _ABNORMAL_FLAGS
    )


def detect_outbreak(
    results: Sequence[dict],
    *,
    test_code: str = "",
    window_days: int = 7,
    baseline_per_day: float = 10.0,
    alert_ratio: float = 3.0,
    history: Sequence[float] | None = None,
    z_threshold: float = 2.5,
) -> dict:
    """Detect a possible disease outbreak.

    Args:
        results:          Current-window result dicts ({"test_code", "flag"}).
        test_code:        Filter to one test code; "" = all tests.
        window_days:      Length of the current observation window in days.
        baseline_per_day: Expected abnormal results per day (ratio method).
        alert_ratio:      Ratio method alert threshold (observed / expected).
        history:          Optional list of per-day abnormal counts from prior
                          windows.  When supplied and long enough (≥ 7 days),
                          the z-score method is used as primary signal.
        z_threshold:      Z-score alert threshold (default 2.5 ≈ p < 0.006).

    Returns:
        dict with keys:
          status          — "alert" | "warning" | "normal" | "insufficient_data"
          observed        — int
          expected        — float (ratio method)
          ratio           — float
          z_score         — float | None
          method          — "z_score" | "ratio"
          message         — human-readable English summary
    """
    if not results:
        return {
            "status":   "normal",
            "observed": 0,
            "expected": baseline_per_day * window_days,
            "ratio":    0.0,
            "z_score":  None,
            "method":   "ratio",
            "message":  "No data provided.",
        }

    observed = _count_abnormal(results, test_code)
    expected = baseline_per_day * window_days
    ratio    = round(observed / expected, 2) if expected > 0 else 0.0

    # ── Z-score path ───────────────────────────────────────────────────────────
    z_score: float | None = None
    method = "ratio"

    if history and len(history) >= 7:
        n    = len(history)
        mean = sum(history) / n
        std  = math.sqrt(sum((x - mean) ** 2 for x in history) / n)

        if std > 0:
            z_score = round((observed - mean) / std, 2)
            method  = "z_score"

            if z_score >= z_threshold:
                status = "alert"
                msg = (
                    f"Outbreak alert (z-score): {observed} abnormal results, "
                    f"z={z_score:.1f} (threshold {z_threshold}). "
                    f"Baseline mean={mean:.1f}, std={std:.1f}. "
                    "Epidemiological review recommended."
                )
            elif z_score >= z_threshold * 0.7:
                status = "warning"
                msg = (
                    f"Elevated signal (z-score): {observed} abnormal results, "
                    f"z={z_score:.1f}. Monitor closely."
                )
            else:
                status = "normal"
                msg = (
                    f"No outbreak signal (z-score): {observed} abnormal results, "
                    f"z={z_score:.1f}."
                )
            return {
                "status":   status,
                "observed": observed,
                "expected": round(mean, 2),
                "ratio":    ratio,
                "z_score":  z_score,
                "method":   method,
                "message":  msg,
            }

    # ── Ratio path (fallback / primary when no history) ────────────────────────
    if ratio >= alert_ratio:
        status = "alert"
        msg = (
            f"Outbreak alert (ratio): {observed} abnormal results in "
            f"{window_days}-day window (expected ~{expected:.0f}, "
            f"ratio {ratio:.1f}×). Epidemiological review recommended."
        )
    elif ratio >= alert_ratio * 0.6:
        status = "warning"
        msg = (
            f"Elevated signal (ratio): {observed} abnormal results, "
            f"ratio {ratio:.1f}×. Monitor closely."
        )
    else:
        status = "normal"
        msg = (
            f"No outbreak signal: {observed} abnormal results in "
            f"{window_days}-day window (ratio {ratio:.1f}×)."
        )

    return {
        "status":   status,
        "observed": observed,
        "expected": expected,
        "ratio":    ratio,
        "z_score":  z_score,
        "method":   method,
        "message":  msg,
    }
