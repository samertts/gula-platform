"""Clinical Engine — GULA Platform  v2.1
=======================================
Central orchestrator for all clinical decision logic.

Design principles
-----------------
1. **Single entry point** — all clinical evaluation goes through evaluate_result()
   or evaluate_order().  No caller should import ali_reza/samir/epidemiology directly.

2. **Versioned decisions** — every output carries CLINICAL_ENGINE_VERSION so
   historical results remain interpretable after rule changes.

3. **Fail-safe** — each sub-engine call is wrapped in try/except.  A crash in
   one engine degrades gracefully; the others still run.

4. **Priority-based conflict resolution** — when sub-engines disagree on severity,
   the engine with the highest ENGINE_PRIORITY wins.  Ties go to the more severe.

   Priority table (higher = more authoritative):
     clinical analysis  (ali_reza)   → priority 3  (direct measurement)
     multi-test patterns (clinical_intelligence) → priority 2
     epidemiology                     → priority 1  (population signal)
     guidance text      (samir)       → priority 0  (informational only)

5. **Patient context** — callers may supply a PatientContext dict to enable
   age/gender-adjusted thresholds and flag interactions with known conditions.

NOT a diagnostic tool — results must be reviewed by a licensed physician.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.clinical_engine")

# ── Version ────────────────────────────────────────────────────────────────────
CLINICAL_ENGINE_VERSION = "v2.1"

# ── Severity constants ─────────────────────────────────────────────────────────
SEVERITY_NORMAL = "NORMAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_UNKNOWN = "UNKNOWN"

_SEVERITY_RANK: dict[str, int] = {
    SEVERITY_NORMAL: 0,
    SEVERITY_WARNING: 1,
    SEVERITY_CRITICAL: 2,
    SEVERITY_UNKNOWN: -1,
}

# ── Engine priorities (for conflict resolution) ────────────────────────────────
_ENGINE_PRIORITY: dict[str, int] = {
    "clinical": 3,  # ali_reza direct measurement analysis
    "multi_pattern": 2,  # clinical_intelligence multi-test patterns
    "epidemiology": 1,  # population-level outbreak signal
    "guidance": 0,  # samir informational tips (never overrides clinical)
}


def _max_severity(a: str, b: str) -> str:
    return a if _SEVERITY_RANK.get(a, -1) >= _SEVERITY_RANK.get(b, -1) else b


def _resolve_severity(sources: list[tuple[str, str]]) -> tuple[str, str]:
    """Resolve conflicting severities using engine priority + max severity.

    Args:
        sources: List of (engine_name, severity) from all sub-engines.

    Returns:
        (winning_severity, winning_engine_name)

    """
    if not sources:
        return SEVERITY_UNKNOWN, "none"

    # Group by severity rank
    best_severity = SEVERITY_NORMAL
    best_engine = sources[0][0]
    best_priority = -1

    for engine, sev in sources:
        sev_rank = _SEVERITY_RANK.get(sev, -1)
        prio = _ENGINE_PRIORITY.get(engine, 0)
        best_rank = _SEVERITY_RANK.get(best_severity, 0)

        if sev_rank > best_rank or (sev_rank == best_rank and prio > best_priority):
            best_severity = sev
            best_engine = engine
            best_priority = prio

    return best_severity, best_engine


# ── Safe sub-engine wrappers ───────────────────────────────────────────────────


def _safe_analyze(test: str, value, context: str, patient_context: dict) -> dict:
    """ali_reza_engine — direct single-test analysis."""
    try:
        from .ali_reza_engine import analyze

        result = analyze(test, value, context=context)

        # Age/gender adjustment — example: anaemia threshold lower for children
        age = patient_context.get("age")
        if test.lower() in ("hb", "hemoglobin") and isinstance(age, (int, float)) and age < 12:
            if (
                value is not None
                and float(value) < 11.5
                and result.get("severity") == SEVERITY_NORMAL
            ):
                result = {
                    "message": "هيموغلوبين منخفض للعمر (طفل < 12 سنة)",
                    "severity": SEVERITY_WARNING,
                }

        return result
    except Exception as exc:
        logger.error("[ClinicalEngine] ali_reza_engine failed test=%s: %s", test, exc)
        return {"message": "تعذّر تحليل النتيجة", "severity": SEVERITY_UNKNOWN}


def _safe_multi_pattern(order_results: list[dict]) -> list[dict]:
    """clinical_intelligence — multi-test pattern detection."""
    try:
        from .clinical_intelligence import detect_patterns

        values_map = {}
        for r in order_results:
            key = str(r.get("test") or r.get("test_name") or r.get("test_code", "")).lower().strip()
            if key and r.get("value") is not None:
                values_map[key] = float(r["value"])
        return detect_patterns(values_map)
    except Exception as exc:
        logger.error("[ClinicalEngine] clinical_intelligence failed: %s", exc)
        return []


def _safe_guidance(test: str) -> str:
    """samir_engine — contextual navigation guidance."""
    try:
        from .samir_engine import samir

        return samir("results")
    except Exception as exc:
        logger.error("[ClinicalEngine] samir_engine failed test=%s: %s", test, exc)
        return "يرجى مراجعة الطبيب المختص."


def _safe_outbreak(order_results: list[dict], test_code: str) -> dict:
    """Epidemiology — population outbreak signal."""
    try:
        from .epidemiology import detect_outbreak

        return detect_outbreak(order_results, test_code=test_code)
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
    patient_context: dict | None = None,
) -> dict:
    """Evaluate a single lab result through all clinical sub-engines.

    Args:
        test:            Test name / code (e.g. "glucose", "hemoglobin").
        value:           Numeric result value.
        context:         Glucose context: "fasting" | "random" | "post_meal".
        flag:            Device flag (H, L, critical, normal).
        order_results:   All results for the same order (for outbreak + patterns).
        patient_context: Optional patient metadata dict::

                            {
                                "age":    int,          # years
                                "gender": "M" | "F",
                                "chronic": ["diabetes", "hypertension"],
                                "previous_results": [
                                    {"test": "glucose", "value": 135.0, ...}
                                ]
                            }

    Returns:
        Full audit-trail dict including engine_version, severity, conflict
        resolution details, and per-engine outputs.

    """
    pctx = patient_context or {}

    # Run all sub-engines independently (fail-safe)
    analysis = _safe_analyze(test, value, context, pctx)
    guidance = _safe_guidance(test)
    outbreak = _safe_outbreak(order_results or [], test)
    patterns = _safe_multi_pattern(order_results or []) if order_results else []

    # Derive epidemiology severity from outbreak status
    epi_sev_map = {
        "alert": SEVERITY_CRITICAL,
        "warning": SEVERITY_WARNING,
        "normal": SEVERITY_NORMAL,
    }
    epi_severity = epi_sev_map.get(outbreak.get("status", "normal"), SEVERITY_NORMAL)

    # Derive pattern severity (highest across all detected patterns)
    pattern_severity = SEVERITY_NORMAL
    for p in patterns:
        ps = SEVERITY_CRITICAL if p.get("severity") == "critical" else SEVERITY_WARNING
        pattern_severity = _max_severity(pattern_severity, ps)

    # Escalate if device flag says critical but analysis says normal
    analysis_sev = analysis.get("severity", SEVERITY_UNKNOWN)
    if str(flag).lower() in {"critical", "h", "l"} and analysis_sev == SEVERITY_NORMAL:
        analysis_sev = SEVERITY_WARNING

    # Priority-based conflict resolution
    severity_sources = [
        ("clinical", analysis_sev),
        ("multi_pattern", pattern_severity),
        ("epidemiology", epi_severity),
    ]
    final_severity, winning_engine = _resolve_severity(severity_sources)

    return {
        "engine_version": CLINICAL_ENGINE_VERSION,
        "test": str(test),
        "value": value,
        "context": context or "random",
        "severity": final_severity,
        "severity_source": winning_engine,
        "severity_sources": dict(severity_sources),
        "analysis": analysis,
        "patterns": patterns,
        "guidance": guidance,
        "outbreak": outbreak,
        "patient_context": {
            "age": pctx.get("age"),
            "gender": pctx.get("gender"),
            "chronic": pctx.get("chronic", []),
        },
        "rule_applied": f"ali_reza_engine@{CLINICAL_ENGINE_VERSION} context={context or 'random'}",
        "disclaimer": "هذا تحليل استرشادي فقط ولا يُغني عن رأي الطبيب المختص.",
    }


def evaluate_order(
    results: list[dict[str, Any]],
    *,
    context: str = "",
    patient_context: dict | None = None,
) -> dict:
    """Evaluate all results in a lab order.

    Returns a consolidated summary with:
      - overall_severity (highest across all results)
      - per-result evaluation list
      - multi-test pattern alerts
      - critical / warning counts
    """
    pctx = patient_context or {}
    evaluations = []
    overall_sev = SEVERITY_NORMAL

    for r in results:
        test = r.get("test") or r.get("test_name") or r.get("test_code", "")
        value = r.get("value")
        flag = r.get("flag", "")

        ev = evaluate_result(
            test,
            value,
            context=context,
            flag=flag,
            order_results=results,
            patient_context=pctx,
        )
        evaluations.append(ev)
        overall_sev = _max_severity(overall_sev, ev["severity"])

    # Order-level multi-test pattern check (runs once for all results)
    order_patterns = _safe_multi_pattern(results)
    for p in order_patterns:
        ps = SEVERITY_CRITICAL if p.get("severity") == "critical" else SEVERITY_WARNING
        overall_sev = _max_severity(overall_sev, ps)

    critical_count = sum(1 for e in evaluations if e["severity"] == SEVERITY_CRITICAL)
    warning_count = sum(1 for e in evaluations if e["severity"] == SEVERITY_WARNING)

    return {
        "engine_version": CLINICAL_ENGINE_VERSION,
        "overall_severity": overall_sev,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "order_patterns": order_patterns,
        "results": evaluations,
        "patient_context": {
            "age": pctx.get("age"),
            "gender": pctx.get("gender"),
            "chronic": pctx.get("chronic", []),
        },
        "disclaimer": "هذا تحليل استرشادي فقط ولا يُغني عن رأي الطبيب المختص.",
    }
