"""Ali Reza Analysis Engine — GULA Platform
==========================================
Context-aware single-test flag interpreter.

Context matters clinically:
  - Fasting glucose ≥ 126 mg/dL → diabetes (ADA guideline)
  - Random glucose  ≥ 200 mg/dL → diabetes
  - Post-meal glucose ≥ 140 mg/dL → impaired glucose tolerance

Without context, the engine falls back to conservative thresholds that are
appropriate for random (non-fasting) measurements — the most common scenario
in a routine lab setting.

NOT a diagnostic tool. Returns Arabic clinical hints only.
Results must be reviewed by a licensed physician.
"""

from __future__ import annotations

from typing import Literal

# Supported context values
GlucoseContext = Literal["fasting", "random", "post_meal", ""]

# Severity levels used by the central clinical engine
SEVERITY_NORMAL = "NORMAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"


# ── Context-aware glucose rules ────────────────────────────────────────────────


def _glucose_rules(context: str) -> list[tuple]:
    """Return ordered (condition, message, severity) tuples for glucose."""
    ctx = (context or "random").lower().strip()

    if ctx == "fasting":
        return [
            (
                lambda v: v >= 200,
                "ارتفاع حاد في سكر الدم الصائم — يُشير إلى سكري غير مسيطر عليه",
                SEVERITY_CRITICAL,
            ),
            (
                lambda v: v >= 126,
                "ارتفاع في سكر الدم الصائم — احتمال السكري (≥ 126 mg/dL)",
                SEVERITY_WARNING,
            ),
            (lambda v: v < 70, "انخفاض سكر الدم — قد يشير إلى نقص سكر الدم", SEVERITY_WARNING),
        ]
    if ctx == "post_meal":
        return [
            (
                lambda v: v >= 200,
                "ارتفاع حاد في سكر الدم بعد الأكل — يُشير إلى سكري",
                SEVERITY_CRITICAL,
            ),
            (
                lambda v: v >= 140,
                "ارتفاع في سكر الدم بعد الأكل — ضعف تحمل الغلوكوز (≥ 140 mg/dL)",
                SEVERITY_WARNING,
            ),
            (lambda v: v < 70, "انخفاض سكر الدم بعد الأكل", SEVERITY_WARNING),
        ]
    # random / default
    return [
        (
            lambda v: v >= 200,
            "ارتفاع شديد في سكر الدم العشوائي — يُشير إلى سكري (≥ 200 mg/dL)",
            SEVERITY_CRITICAL,
        ),
        (lambda v: v >= 140, "ارتفاع محتمل في السكر العشوائي", SEVERITY_WARNING),
        (lambda v: v < 70, "انخفاض سكر الدم", SEVERITY_WARNING),
    ]


# ── Context-independent rules (test → [(condition, message, severity)]) ────────

_STATIC_RULES: dict[str, list[tuple]] = {
    "hb": [
        (lambda v: v < 8, "فقر دم شديد — يتطلب تقييم طبي عاجل", SEVERITY_CRITICAL),
        (lambda v: v < 10, "فقر دم محتمل", SEVERITY_WARNING),
        (lambda v: v < 12, "انخفاض طفيف في الهيموغلوبين", SEVERITY_WARNING),
        (lambda v: v > 18, "ارتفاع في الهيموغلوبين — يُنصح بالمتابعة الطبية", SEVERITY_WARNING),
    ],
    "hemoglobin": [
        (lambda v: v < 8, "فقر دم شديد — يتطلب تقييم طبي عاجل", SEVERITY_CRITICAL),
        (lambda v: v < 10, "فقر دم محتمل", SEVERITY_WARNING),
        (lambda v: v < 12, "انخفاض طفيف في الهيموغلوبين", SEVERITY_WARNING),
        (lambda v: v > 18, "ارتفاع في الهيموغلوبين — يُنصح بالمتابعة الطبية", SEVERITY_WARNING),
    ],
    "creatinine": [
        (lambda v: v > 4.0, "فشل كلوي محتمل — يتطلب تقييم طبي عاجل", SEVERITY_CRITICAL),
        (lambda v: v > 2.0, "ارتفاع شديد في الكرياتينين — ضعف وظائف الكلى", SEVERITY_CRITICAL),
        (lambda v: v > 1.5, "احتمال ضعف وظائف الكلى — يُنصح بمراجعة الطبيب", SEVERITY_WARNING),
    ],
    "wbc": [
        (
            lambda v: v > 20.0,
            "ارتفاع حاد في كريات الدم البيضاء — احتمال إنتان أو سرطان دم",
            SEVERITY_CRITICAL,
        ),
        (lambda v: v > 15.0, "ارتفاع شديد في كريات الدم البيضاء", SEVERITY_WARNING),
        (lambda v: v > 11.0, "ارتفاع في كريات الدم البيضاء — قد يشير إلى التهاب", SEVERITY_WARNING),
        (
            lambda v: v < 2.0,
            "انخفاض حاد في كريات الدم البيضاء — خطر العدوى مرتفع",
            SEVERITY_CRITICAL,
        ),
        (lambda v: v < 4.0, "انخفاض في كريات الدم البيضاء", SEVERITY_WARNING),
    ],
    "platelets": [
        (lambda v: v < 20, "انخفاض حاد خطير في الصفائح الدموية", SEVERITY_CRITICAL),
        (lambda v: v < 50, "انخفاض حاد في الصفائح الدموية", SEVERITY_CRITICAL),
        (lambda v: v < 150, "انخفاض في الصفائح الدموية", SEVERITY_WARNING),
        (lambda v: v > 600, "ارتفاع حاد في الصفائح الدموية", SEVERITY_WARNING),
        (lambda v: v > 400, "ارتفاع في الصفائح الدموية", SEVERITY_WARNING),
    ],
    "hba1c": [
        (lambda v: v >= 9.0, "سيطرة ضعيفة جداً على السكري — مراجعة طبية عاجلة", SEVERITY_CRITICAL),
        (lambda v: v >= 6.5, "يُشير إلى السكري (HbA1c ≥ 6.5%)", SEVERITY_WARNING),
        (lambda v: v >= 5.7, "مرحلة ما قبل السكري (HbA1c 5.7–6.4%)", SEVERITY_WARNING),
    ],
    "urea": [
        (lambda v: v > 100, "ارتفاع حاد في اليوريا — ضعف وظائف الكلى", SEVERITY_CRITICAL),
        (lambda v: v > 50, "ارتفاع في اليوريا — يُنصح بمراجعة الطبيب", SEVERITY_WARNING),
    ],
}

_DEFAULT_MSG = "القيمة ضمن الطبيعي"
_DEFAULT_SEVERITY = SEVERITY_NORMAL


def analyze(
    test: str,
    value,
    context: str = "",
) -> dict:
    """Return a clinical hint dict for a single test result.

    Args:
        test:    Test name / code (case-insensitive).
        value:   Numeric result value.
        context: Glucose collection context: "fasting" | "random" | "post_meal".
                 Ignored for non-glucose tests.

    Returns:
        dict with keys:
          - ``message``  (str)  — Arabic clinical hint
          - ``severity`` (str)  — NORMAL | WARNING | CRITICAL

    """
    if value is None:
        return {"message": _DEFAULT_MSG, "severity": _DEFAULT_SEVERITY}
    try:
        v = float(value)
    except (TypeError, ValueError):
        return {"message": _DEFAULT_MSG, "severity": _DEFAULT_SEVERITY}

    key = str(test).lower().strip()

    # Glucose uses context-aware rules
    rules = _glucose_rules(context) if key == "glucose" else _STATIC_RULES.get(key, [])

    for condition, message, severity in rules:
        try:
            if condition(v):
                return {"message": message, "severity": severity}
        except Exception:
            continue

    return {"message": _DEFAULT_MSG, "severity": _DEFAULT_SEVERITY}
