"""
Ali Reza Analysis Engine — GULA Platform
==========================================
Single-test flag interpreter for quick clinical hints.

ali_reza.py previously duplicated this logic with conflicting thresholds
(glucose >140 only, no creatinine) — that file now delegates here.

NOT a diagnostic tool.  Returns Arabic-language hints only.
"""

# Thresholds (mg/dL, g/dL, etc. — same units as LabResult.value)
_RULES = {
    "glucose": [
        (lambda v: v > 180, "ارتفاع شديد في سكر الدم"),
        (lambda v: v > 140, "ارتفاع محتمل في السكر"),
        (lambda v: v < 70,  "انخفاض في سكر الدم"),
    ],
    "hb": [
        (lambda v: v < 10, "فقر دم محتمل"),
        (lambda v: v < 12, "انخفاض طفيف في الهيموغلوبين"),
    ],
    "hemoglobin": [
        (lambda v: v < 10, "فقر دم محتمل"),
        (lambda v: v < 12, "انخفاض طفيف في الهيموغلوبين"),
    ],
    "creatinine": [
        (lambda v: v > 2.0, "ارتفاع شديد في الكرياتينين — احتمال ضعف وظائف الكلى"),
        (lambda v: v > 1.5, "احتمال ضعف وظائف الكلى"),
    ],
    "wbc": [
        (lambda v: v > 15.0, "ارتفاع شديد في كريات الدم البيضاء"),
        (lambda v: v > 11.0, "ارتفاع في كريات الدم البيضاء — قد يشير إلى التهاب"),
        (lambda v: v < 4.0,  "انخفاض في كريات الدم البيضاء"),
    ],
    "platelets": [
        (lambda v: v < 50,  "انخفاض حاد في الصفائح الدموية"),
        (lambda v: v < 150, "انخفاض في الصفائح الدموية"),
        (lambda v: v > 400, "ارتفاع في الصفائح الدموية"),
    ],
}

_DEFAULT = "القيمة ضمن الطبيعي"


def analyze(test: str, value) -> str:
    """Return a short Arabic clinical hint for a single test result.

    Args:
        test:  Test name / code (case-insensitive, e.g. "glucose", "hb").
        value: Numeric result value.

    Returns:
        Arabic hint string.  Never raises — returns default on unknown test
        or non-numeric value.
    """
    if value is None:
        return _DEFAULT
    try:
        v = float(value)
    except (TypeError, ValueError):
        return _DEFAULT

    rules = _RULES.get(str(test).lower().strip(), [])
    for condition, message in rules:
        try:
            if condition(v):
                return message
        except Exception:
            continue
    return _DEFAULT
