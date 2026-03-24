"""
Clinical Engine — GULA Platform
=================================
Central orchestrator for all clinical decision logic.

Instead of calling ali_reza, samir, and epidemiology independently (risking
inconsistent results and untraceable decisions), all clinical evaluation
passes through this single entry point.

Guarantees:
  ✔ Versioned decisions — every result includes the engine version that
    produced it, so historical results remain interpretable after rule changes.
  ✔ Fail-safe — each sub-engine is wrapped in try/except; a crash in one
    engine degrades gracefully rather than failing the whole evaluation.
  ✔ Severity classification — NORMAL / WARNING / CRITICAL / UNKNOWN.
  ✔ Audit trail — the returned dict includes enough context to reconstruct
    exactly why the decision was made (rule, engine, version, context).

NOT a diagnostic tool — results must be reviewed by a licensed physician.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.clinical_engine")

# ── Version ────────────────────────────────────────────────────────────────────
# Bump this whenever thresholds or rules change so stored results can be
# re-interpreted against the version that originally produced them.
CLINICAL_ENGINE_VERSION = "v2.0"

# Severity constants (ordered low → high for comparison)
SEVERITY_NORMAL   = "NORMAL"
SEVERITY_WARNING  = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_UNKNOWN  = "UNKNOWN"   # returned when the engine itself fails

_SEVERITY_RANK = {
    SEVERITY_NORMAL:   0,
    SEVERITY_WARNING:  1,
    SEVERITY_CRITICAL: 2,
    SEVERITY_UNKNOWN:  -1,
}


def _max_severity(a: str, b: str) -> str:
    return a if _SEVERITY_RANK.get(a, -1) >= _SEVERITY_RANK.get(b, -1) else b


# ── Safe wrappers ──────────────────────────────────────────────────────────────

def _safe_analyze(test: str, value, context: str = "") -> dict:
    """Call ali_reza_engine.analyze with full error isolation."""
    try:
        from .ali_reza_engine import analyze
        return analyze(test, value, context=context)
    except Exception as exc:
        logger.error("[ClinicalEngine] ali_reza_engine failed for test=%s: %s", test, exc)
        return {"message": "تعذّر تحليل النتيجة", "severity": SEVERITY_UNKNOWN}


def _safe_guidance(test: str, flag: str) -> str:
    """Call samir_engine for contextual guidance with full error isolation."""
    try:
        from .samir_engine import samir
        # Map test result to the most relevant page
        page_map = {
            "glucose": "results", "hba1c": "results",
            "hemoglobin": "results", "hb": "results",
            "wbc": "results", "platelets": "results",
            "creatinine": "results", "urea": "results",
        }
        page = page_map.get(str(test).lower().strip(), "results")
        return samir(page)
    except Exception as exc:
        logger.error("[ClinicalEngine] samir_engine failed for test=%s: %s", test, exc)
        return "يرجى مراجعة الطبيب المختص."


def _safe_outbreak(results: list[dict], test_code: str = "") -> dict:
    """Call epidemiology.detect_outbreak with full error isolation."""
    try:
        from .epidemiology import detect_outbreak
        return detect_outbreak(results, test_code=test_code)
    except Exception as exc:
        logger.error("[ClinicalEngine] epidemiology failed: %s", exc)
        return {"status": "unknown", "message": "Epidemiology check unavailable.", "ratio": None}


# ── Public API ─────────────────────────────────────────────────────────────────

def evaluate_result(
    test: str,
    value,
    *,
    context: str = "",
    flag: str = "",
    order_results: list[dict] | None = None,
) -> dict:
    """Evaluate a single lab result through all clinical sub-engines.

    Args:
        test:          Test name / code (e.g. "glucose", "hemoglobin").
        value:         Numeric result value.
        context:       Glucose collection context ("fasting" | "random" | "post_meal").
        flag:          Result flag from the analyser (H, L, critical, etc.).
        order_results: All results for the same order — used for outbreak check.
                       Each item: {"test_code": str, "flag": str}.

    Returns:
        dict with full audit trail::

            {
                "engine_version": "v2.0",
                "test":           "glucose",
                "value":          145.0,
                "context":        "fasting",
                "severity":       "WARNING",
                "analysis": {
                    "message":  "ارتفاع في سكر الدم الصائم ...",
                    "severity": "WARNING",
                },
                "guidance":       "يمكنك مراجعة النتائج الطبية ...",
                "outbreak": {
                    "status": "normal",
                    "ratio":  0.3,
                    ...
                },
                "rule_applied":   "ali_reza_engine@v2.0 context=fasting",
                "disclaimer":     "هذا تحليل استرشادي. لا يُغني عن رأي الطبيب.",
            }
    """
    analysis  = _safe_analyze(test, value, context)
    guidance  = _safe_guidance(test, flag)
    outbreak  = _safe_outbreak(order_results or [], test_code=test)

    # Escalate severity if the flag from the analyser says critical
    effective_severity = analysis.get("severity", SEVERITY_UNKNOWN)
    if str(flag).lower() in {"critical", "h", "l"} and effective_severity == SEVERITY_NORMAL:
        effective_severity = SEVERITY_WARNING

    return {
        "engine_version": CLINICAL_ENGINE_VERSION,
        "test":           str(test),
        "value":          value,
        "context":        context or "random",
        "severity":       effective_severity,
        "analysis":       analysis,
        "guidance":       guidance,
        "outbreak":       outbreak,
        "rule_applied":   f"ali_reza_engine@{CLINICAL_ENGINE_VERSION} context={context or 'random'}",
        "disclaimer":     "هذا تحليل استرشادي فقط ولا يُغني عن رأي الطبيب المختص.",
    }


def evaluate_order(
    results: list[dict[str, Any]],
    *,
    context: str = "",
) -> dict:
    """Evaluate all results in a lab order and return a consolidated summary.

    Args:
        results: List of result dicts, each with at least:
                 {"test": str, "value": float|None, "flag": str}
        context: Glucose collection context (applied to all glucose tests).

    Returns:
        dict with:
          - ``engine_version`` — version that produced this evaluation
          - ``overall_severity`` — highest severity across all results
          - ``results`` — per-result evaluation list
          - ``critical_count``, ``warning_count`` — quick counters
    """
    evaluations = []
    overall_severity = SEVERITY_NORMAL

    for r in results:
        test  = r.get("test") or r.get("test_name") or r.get("test_code", "")
        value = r.get("value")
        flag  = r.get("flag", "")

        ev = evaluate_result(
            test, value,
            context=context,
            flag=flag,
            order_results=results,
        )
        evaluations.append(ev)
        overall_severity = _max_severity(overall_severity, ev["severity"])

    critical_count = sum(1 for e in evaluations if e["severity"] == SEVERITY_CRITICAL)
    warning_count  = sum(1 for e in evaluations if e["severity"] == SEVERITY_WARNING)

    return {
        "engine_version":   CLINICAL_ENGINE_VERSION,
        "overall_severity": overall_severity,
        "critical_count":   critical_count,
        "warning_count":    warning_count,
        "results":          evaluations,
        "disclaimer":       "هذا تحليل استرشادي فقط ولا يُغني عن رأي الطبيب المختص.",
    }
