"""
Epidemiology Service — GULA Platform
======================================
Outbreak detection using incidence-rate thresholds rather than a raw
record count.  A raw count of >1000 is meaningless — a busy lab with
1 001 routine CBC results is not an outbreak.

Algorithm (simple, deterministic, auditable):
  1. Count results for a specific test within a rolling time window.
  2. Compare against the baseline (expected results per day × window days).
  3. If observed / expected >= threshold ratio → alert.

Returns a dict so callers can decide how to display the result.
"""
from __future__ import annotations

from typing import Sequence


def detect_outbreak(
    results: Sequence[dict],
    *,
    test_code: str = "",
    window_days: int = 7,
    baseline_per_day: float = 10.0,
    alert_ratio: float = 3.0,
) -> dict:
    """Detect a possible disease outbreak from a sequence of result records.

    Args:
        results:          Iterable of result dicts.  Each dict must contain at
                          least ``{"test_code": str, "flag": str}``.
        test_code:        Filter to a specific test code.  Empty string = all.
        window_days:      Rolling window length in days (used to derive expected
                          count from ``baseline_per_day``).
        baseline_per_day: Expected number of *flagged* results per day under
                          normal conditions.
        alert_ratio:      Raise alert when observed / expected >= this ratio.

    Returns:
        dict with keys:
          - ``status``: "alert" | "normal"
          - ``observed``: int — count of abnormal results in window
          - ``expected``: float — baseline count for the window
          - ``ratio``: float — observed / expected (or 0 if expected == 0)
          - ``message``: str — human-readable summary
    """
    if not results:
        return {
            "status": "normal",
            "observed": 0,
            "expected": baseline_per_day * window_days,
            "ratio": 0.0,
            "message": "No data provided.",
        }

    abnormal_flags = {"H", "L", "critical", "high", "low"}

    observed = sum(
        1 for r in results
        if (not test_code or str(r.get("test_code", "")).lower() == test_code.lower())
        and str(r.get("flag", "")).strip() in abnormal_flags
    )

    expected = baseline_per_day * window_days
    ratio = (observed / expected) if expected > 0 else 0.0

    if ratio >= alert_ratio:
        status = "alert"
        message = (
            f"Possible outbreak detected: {observed} abnormal results "
            f"in {window_days}-day window (expected ~{expected:.0f}, "
            f"ratio {ratio:.1f}×). Epidemiological review recommended."
        )
    else:
        status = "normal"
        message = (
            f"No outbreak signal: {observed} abnormal results "
            f"in {window_days}-day window (ratio {ratio:.1f}×)."
        )

    return {
        "status": status,
        "observed": observed,
        "expected": expected,
        "ratio": round(ratio, 2),
        "message": message,
    }
