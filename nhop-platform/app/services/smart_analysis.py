"""Smart analysis for lab test results.

Provides four capabilities layered on top of a small, static reference table:

    1. ``validate_result``          — biologically plausible bounds
    2. ``compare_with_history``     — trend vs. the citizen's last N points
    3. ``get_arabic_interpretation``— patient-friendly Arabic plain text
    4. ``check_drug_interaction``   — rule-based drug/result safety hints

The tables here are deliberately small and hand-curated; they cover the most
common 20 tests and 10 drug/result interaction rules. Extend as needed; do
NOT add clinical rules here without a clinician sign-off.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session


# ─── Reference tables ───────────────────────────────────────────────────────
#
# Each entry:
#   (plausible_min, plausible_max,            -> outside = data error
#    ref_min,       ref_max,                  -> outside = abnormal
#    critical_low,  critical_high,            -> outside = critical
#    canonical_unit,
#    arabic_name)
#
# Values outside the plausible range are treated as data-entry errors and the
# row is rejected with ``is_valid=False``. Values between plausible and
# reference are flagged abnormal; values past the critical threshold trigger
# ``is_critical=True``.

_TEST_CATALOG: dict[str, dict] = {
    "HGB":   {"range": (0.0, 25.0),   "ref": (12.0, 17.0),  "crit": (7.0, 20.0),   "unit": "g/dL",   "ar": "الهيموغلوبين"},
    "HB":    {"alias": "HGB"},
    "HCT":   {"range": (0.0, 70.0),   "ref": (36.0, 50.0),  "crit": (20.0, 60.0),  "unit": "%",      "ar": "الهيماتوكريت"},
    "RBC":   {"range": (0.0, 10.0),   "ref": (4.0, 6.0),    "crit": (2.0, 7.5),    "unit": "10^6/uL","ar": "كريات الدم الحمراء"},
    "WBC":   {"range": (0.0, 200.0),  "ref": (4.0, 11.0),   "crit": (2.0, 30.0),   "unit": "10^3/uL","ar": "كريات الدم البيضاء"},
    "PLT":   {"range": (0.0, 2000.0), "ref": (150.0, 450.0),"crit": (50.0, 1000.0),"unit": "10^3/uL","ar": "الصفائح الدموية"},
    "GLU":   {"range": (10.0, 1000.0),"ref": (70.0, 100.0), "crit": (40.0, 400.0), "unit": "mg/dL",  "ar": "سكر الدم الصائم"},
    "GLUCOSE":{"alias": "GLU"},
    "HBA1C": {"range": (2.0, 20.0),   "ref": (4.0, 5.6),    "crit": (4.0, 10.0),   "unit": "%",      "ar": "السكر التراكمي"},
    "CR":    {"range": (0.0, 20.0),   "ref": (0.6, 1.3),    "crit": (0.4, 4.0),    "unit": "mg/dL",  "ar": "الكرياتينين"},
    "CREATININE":{"alias": "CR"},
    "BUN":   {"range": (0.0, 200.0),  "ref": (7.0, 20.0),   "crit": (5.0, 100.0),  "unit": "mg/dL",  "ar": "يوريا الدم"},
    "UREA":  {"alias": "BUN"},
    "NA":    {"range": (100.0, 200.0),"ref": (135.0, 145.0),"crit": (125.0, 155.0),"unit": "mmol/L", "ar": "الصوديوم"},
    "K":     {"range": (1.0, 10.0),   "ref": (3.5, 5.0),    "crit": (3.0, 6.0),    "unit": "mmol/L", "ar": "البوتاسيوم"},
    "CL":    {"range": (60.0, 140.0), "ref": (98.0, 107.0), "crit": (85.0, 120.0), "unit": "mmol/L", "ar": "الكلوريد"},
    "CA":    {"range": (4.0, 20.0),   "ref": (8.5, 10.5),   "crit": (7.0, 13.0),   "unit": "mg/dL",  "ar": "الكالسيوم"},
    "ALT":   {"range": (0.0, 5000.0), "ref": (7.0, 56.0),   "crit": (0.0, 400.0),  "unit": "U/L",    "ar": "إنزيم الكبد ALT"},
    "AST":   {"range": (0.0, 5000.0), "ref": (10.0, 40.0),  "crit": (0.0, 400.0),  "unit": "U/L",    "ar": "إنزيم الكبد AST"},
    "TSH":   {"range": (0.0, 200.0),  "ref": (0.4, 4.0),    "crit": (0.01, 50.0),  "unit": "mIU/L",  "ar": "الهرمون المنشّط للغدة الدرقية"},
    "CHOL":  {"range": (30.0, 800.0), "ref": (125.0, 200.0),"crit": (0.0, 300.0),  "unit": "mg/dL",  "ar": "الكوليسترول الكلي"},
    "LDL":   {"range": (10.0, 500.0), "ref": (0.0, 130.0),  "crit": (0.0, 190.0),  "unit": "mg/dL",  "ar": "الكوليسترول الضار"},
    "HDL":   {"range": (5.0, 200.0),  "ref": (40.0, 100.0), "crit": (20.0, 200.0), "unit": "mg/dL",  "ar": "الكوليسترول النافع"},
    "TG":    {"range": (10.0, 5000.0),"ref": (0.0, 150.0),  "crit": (0.0, 500.0),  "unit": "mg/dL",  "ar": "الدهون الثلاثية"},
    "CRP":   {"range": (0.0, 500.0),  "ref": (0.0, 10.0),   "crit": (0.0, 100.0),  "unit": "mg/L",   "ar": "البروتين المتفاعل CRP"},
    "INR":   {"range": (0.5, 20.0),   "ref": (0.8, 1.2),    "crit": (0.8, 5.0),    "unit": "",       "ar": "زمن البروثرومبين (INR)"},
}


def _resolve(test_code: str) -> Optional[dict]:
    code = (test_code or "").strip().upper()
    entry = _TEST_CATALOG.get(code)
    if entry and "alias" in entry:
        entry = _TEST_CATALOG.get(entry["alias"])
    return entry


# ─── Public dataclasses ─────────────────────────────────────────────────────

@dataclass
class Warning:
    code: str
    message: str
    severity: str = "warning"  # 'info' | 'warning' | 'critical'


@dataclass
class ValidationResult:
    is_valid: bool = True
    is_critical: bool = False
    is_abnormal: bool = False
    direction: Optional[str] = None  # 'low' | 'high' | 'normal'
    interpretation_ar: Optional[str] = None
    warnings: list[Warning] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "is_critical": self.is_critical,
            "is_abnormal": self.is_abnormal,
            "direction": self.direction,
            "interpretation_ar": self.interpretation_ar,
            "warnings": [w.__dict__ for w in self.warnings],
        }


@dataclass
class ComparisonResult:
    trend: str  # 'rising' | 'falling' | 'stable' | 'insufficient_data'
    delta_percent: Optional[float]
    previous_values: list[tuple]  # (performed_at, value)
    warnings: list[Warning] = field(default_factory=list)


# ─── 1. validate_result ─────────────────────────────────────────────────────

def validate_result(
    test_code: str,
    value: Optional[float],
    unit: Optional[str] = None,
    reference_min: Optional[float] = None,
    reference_max: Optional[float] = None,
) -> ValidationResult:
    """Check a single numeric result against the reference catalog.

    If the test code is unknown and explicit ref_min/ref_max are provided, we
    still do a basic abnormal check. If value is None (text-only result), we
    return a pass-through ValidationResult.
    """
    res = ValidationResult()
    if value is None:
        return res  # text results are not validated here

    entry = _resolve(test_code)

    # 1a. Unknown test + no explicit reference → nothing to validate.
    if entry is None:
        if reference_min is None or reference_max is None:
            res.warnings.append(Warning(
                code="unknown_test",
                message=f"Unknown test code '{test_code}'; cannot validate bounds.",
                severity="info",
            ))
            return res
        ref_lo, ref_hi = reference_min, reference_max
        crit_lo, crit_hi = ref_lo, ref_hi
        plausible_lo, plausible_hi = None, None
        expected_unit = None
        ar_name = test_code
    else:
        plausible_lo, plausible_hi = entry["range"]
        ref_lo, ref_hi = entry["ref"]
        crit_lo, crit_hi = entry["crit"]
        expected_unit = entry.get("unit")
        ar_name = entry.get("ar", test_code)
        # Caller-supplied ref overrides
        if reference_min is not None:
            ref_lo = reference_min
        if reference_max is not None:
            ref_hi = reference_max

    # 1b. Unit sanity.
    if expected_unit and unit and unit.strip() and unit.strip() != expected_unit:
        res.warnings.append(Warning(
            code="unit_mismatch",
            message=f"Unit '{unit}' differs from expected '{expected_unit}' for {test_code}.",
            severity="warning",
        ))

    # 1c. Biologically implausible → data error.
    if plausible_lo is not None and (value < plausible_lo or value > plausible_hi):
        res.is_valid = False
        res.warnings.append(Warning(
            code="implausible_value",
            message=f"Value {value} is outside the plausible range "
                    f"[{plausible_lo}, {plausible_hi}] for {test_code}.",
            severity="critical",
        ))
        return res

    # 1d. Abnormal vs. critical.
    if value < ref_lo:
        res.is_abnormal = True
        res.direction = "low"
    elif value > ref_hi:
        res.is_abnormal = True
        res.direction = "high"
    else:
        res.direction = "normal"

    if value < crit_lo or value > crit_hi:
        res.is_critical = True
        res.warnings.append(Warning(
            code="critical_value",
            message=f"{ar_name}: قيمة حرجة ({value} {unit or expected_unit or ''}).",
            severity="critical",
        ))

    # 1e. Arabic interpretation (best effort).
    res.interpretation_ar = get_arabic_interpretation(
        test_code, value, ref_lo, ref_hi
    )
    return res


# ─── 2. compare_with_history ────────────────────────────────────────────────

def compare_with_history(
    citizen_id: int,
    test_code: str,
    new_value: Optional[float],
    db: Session,
    *,
    lookback: int = 5,
    delta_alert_pct: float = 50.0,
) -> ComparisonResult:
    """Compare ``new_value`` to the citizen's recent results for the same test.

    Returns ``trend='insufficient_data'`` when fewer than two prior numeric
    points exist, and flags a 'large_delta' warning when the change vs. the
    most recent prior point exceeds ``delta_alert_pct``.
    """
    from ..models.test_result import TestResult

    if new_value is None:
        return ComparisonResult(trend="insufficient_data",
                                delta_percent=None,
                                previous_values=[])

    code = (test_code or "").strip().upper()
    rows = (
        db.query(TestResult)
          .filter(
              TestResult.citizen_id == citizen_id,
              TestResult.test_code == code,
              TestResult.value_numeric.is_not(None),
          )
          .order_by(desc(TestResult.performed_at))
          .limit(lookback)
          .all()
    )

    previous = [(r.performed_at, float(r.value_numeric)) for r in rows]

    if not previous:
        return ComparisonResult(trend="insufficient_data",
                                delta_percent=None,
                                previous_values=[])

    prev_value = previous[0][1]
    if prev_value == 0:
        delta_pct = None
    else:
        delta_pct = (new_value - prev_value) / abs(prev_value) * 100.0

    # Trend over the full window: compare new_value to mean of previous.
    mean_prev = sum(v for _, v in previous) / len(previous)
    if abs(new_value - mean_prev) < 0.05 * max(abs(mean_prev), 1.0):
        trend = "stable"
    elif new_value > mean_prev:
        trend = "rising"
    else:
        trend = "falling"

    warnings: list[Warning] = []
    if delta_pct is not None and abs(delta_pct) >= delta_alert_pct:
        warnings.append(Warning(
            code="large_delta",
            message=f"تغيّر كبير عن آخر قياس: {delta_pct:+.1f}% (من {prev_value} إلى {new_value}).",
            severity="warning",
        ))

    return ComparisonResult(
        trend=trend,
        delta_percent=delta_pct,
        previous_values=previous,
        warnings=warnings,
    )


# ─── 3. Arabic interpretation ───────────────────────────────────────────────

_AR_TEMPLATES: dict[str, tuple[str, str, str]] = {
    # code: (low, normal, high)
    "HGB":   ("الهيموغلوبين منخفض — احتمال فقر دم، راجع طبيبك.",
              "الهيموغلوبين طبيعي ✓",
              "الهيموغلوبين مرتفع — راجع طبيبك."),
    "HCT":   ("الهيماتوكريت منخفض.",
              "الهيماتوكريت طبيعي ✓",
              "الهيماتوكريت مرتفع."),
    "RBC":   ("كريات الدم الحمراء منخفضة.",
              "كريات الدم الحمراء طبيعية ✓",
              "كريات الدم الحمراء مرتفعة."),
    "WBC":   ("كريات الدم البيضاء منخفضة — احتمال ضعف مناعة.",
              "كريات الدم البيضاء طبيعية ✓",
              "كريات الدم البيضاء مرتفعة — احتمال التهاب."),
    "PLT":   ("الصفائح الدموية منخفضة — خطر نزيف.",
              "الصفائح الدموية طبيعية ✓",
              "الصفائح الدموية مرتفعة."),
    "GLU":   ("سكر الدم منخفض — قد تحتاج تناول طعام.",
              "نسبة السكر طبيعية ✓",
              "سكر الدم مرتفع — راجع طبيبك."),
    "HBA1C": ("السكر التراكمي منخفض.",
              "السكر التراكمي طبيعي ✓",
              "السكر التراكمي مرتفع — مؤشر على سوء ضبط السكري."),
    "CR":    ("الكرياتينين منخفض.",
              "الكرياتينين طبيعي ✓",
              "الكرياتينين مرتفع — تحقق من وظائف الكلى."),
    "BUN":   ("يوريا الدم منخفضة.",
              "يوريا الدم طبيعية ✓",
              "يوريا الدم مرتفعة — تحقق من وظائف الكلى."),
    "NA":    ("الصوديوم منخفض.", "الصوديوم طبيعي ✓", "الصوديوم مرتفع."),
    "K":     ("البوتاسيوم منخفض — قد يؤثر على القلب.",
              "البوتاسيوم طبيعي ✓",
              "البوتاسيوم مرتفع — خطر على القلب، راجع الطبيب فوراً."),
    "CL":    ("الكلوريد منخفض.", "الكلوريد طبيعي ✓", "الكلوريد مرتفع."),
    "CA":    ("الكالسيوم منخفض.", "الكالسيوم طبيعي ✓", "الكالسيوم مرتفع."),
    "ALT":   ("إنزيم ALT منخفض.", "إنزيم ALT طبيعي ✓",
              "إنزيم ALT مرتفع — احتمال التهاب بالكبد."),
    "AST":   ("إنزيم AST منخفض.", "إنزيم AST طبيعي ✓",
              "إنزيم AST مرتفع — احتمال التهاب بالكبد."),
    "TSH":   ("TSH منخفض — احتمال فرط نشاط الغدة الدرقية.",
              "وظيفة الغدة الدرقية طبيعية ✓",
              "TSH مرتفع — احتمال قصور الغدة الدرقية."),
    "CHOL":  ("الكوليسترول منخفض.",
              "الكوليسترول طبيعي ✓",
              "الكوليسترول مرتفع — راجع طبيبك."),
    "LDL":   ("LDL منخفض.",
              "LDL ضمن المعدل ✓",
              "LDL مرتفع — خطر على القلب."),
    "HDL":   ("HDL منخفض — عامل خطر للقلب.",
              "HDL ضمن المعدل ✓",
              "HDL مرتفع ✓"),
    "TG":    ("الدهون الثلاثية منخفضة.",
              "الدهون الثلاثية طبيعية ✓",
              "الدهون الثلاثية مرتفعة — راجع طبيبك."),
    "CRP":   ("CRP منخفض ✓",
              "CRP ضمن المعدل ✓",
              "CRP مرتفع — وجود التهاب."),
    "INR":   ("INR منخفض — خطر تخثر.",
              "INR ضمن المعدل ✓",
              "INR مرتفع — خطر نزيف."),
}


def get_arabic_interpretation(
    test_code: str,
    value: Optional[float],
    ref_min: Optional[float],
    ref_max: Optional[float],
) -> Optional[str]:
    """Return a one-line Arabic plain-language interpretation."""
    if value is None or ref_min is None or ref_max is None:
        return None
    code = (test_code or "").strip().upper()
    entry = _TEST_CATALOG.get(code)
    if entry and "alias" in entry:
        code = entry["alias"]
    template = _AR_TEMPLATES.get(code)
    if template is None:
        return None
    low_msg, normal_msg, high_msg = template
    if value < ref_min:
        return low_msg
    if value > ref_max:
        return high_msg
    return normal_msg


# ─── 4. Drug interaction checks ─────────────────────────────────────────────

@dataclass
class Alert:
    code: str
    message: str
    severity: str = "warning"


# Each rule:
#   name, predicate(results_by_code, meds) -> bool, message, severity
_DRUG_RULES: list[dict] = [
    {
        "code": "insulin_hypoglycemia",
        "drugs": {"insulin"},
        "check": lambda r: "GLU" in r and r["GLU"] is not None and r["GLU"] < 70,
        "message": "سكر الدم منخفض مع استخدام الإنسولين — احتمال جرعة زائدة.",
        "severity": "critical",
    },
    {
        "code": "nsaid_renal",
        "drugs": {"ibuprofen", "naproxen", "diclofenac", "nsaid"},
        "check": lambda r: "CR" in r and r["CR"] is not None and r["CR"] > 1.3,
        "message": "الكرياتينين مرتفع مع استخدام مضادات الالتهاب — خطر على الكلى.",
        "severity": "critical",
    },
    {
        "code": "metformin_lactic",
        "drugs": {"metformin"},
        "check": lambda r: "CR" in r and r["CR"] is not None and r["CR"] > 1.5,
        "message": "الكرياتينين مرتفع مع استخدام الميتفورمين — خطر حموضة لبنية.",
        "severity": "warning",
    },
    {
        "code": "warfarin_bleeding",
        "drugs": {"warfarin"},
        "check": lambda r: "INR" in r and r["INR"] is not None and r["INR"] > 3.5,
        "message": "INR مرتفع مع استخدام الوارفارين — خطر نزيف.",
        "severity": "critical",
    },
    {
        "code": "ace_hyperkalemia",
        "drugs": {"lisinopril", "enalapril", "ramipril", "ace"},
        "check": lambda r: "K" in r and r["K"] is not None and r["K"] > 5.2,
        "message": "البوتاسيوم مرتفع مع استخدام مثبطات ACE — خطر على القلب.",
        "severity": "critical",
    },
    {
        "code": "statin_liver",
        "drugs": {"atorvastatin", "simvastatin", "rosuvastatin", "statin"},
        "check": lambda r: ("ALT" in r and r["ALT"] is not None and r["ALT"] > 120)
                       or  ("AST" in r and r["AST"] is not None and r["AST"] > 120),
        "message": "إنزيمات الكبد مرتفعة مع استخدام الستاتين — توقف ومراجعة الطبيب.",
        "severity": "warning",
    },
    {
        "code": "diuretic_hypokalemia",
        "drugs": {"furosemide", "hydrochlorothiazide", "hctz"},
        "check": lambda r: "K" in r and r["K"] is not None and r["K"] < 3.5,
        "message": "البوتاسيوم منخفض مع استخدام مدرّات البول.",
        "severity": "warning",
    },
    {
        "code": "digoxin_hypokalemia",
        "drugs": {"digoxin"},
        "check": lambda r: "K" in r and r["K"] is not None and r["K"] < 3.5,
        "message": "البوتاسيوم منخفض مع استخدام الديجوكسين — خطر سمية قلبية.",
        "severity": "critical",
    },
    {
        "code": "levothyroxine_overdose",
        "drugs": {"levothyroxine"},
        "check": lambda r: "TSH" in r and r["TSH"] is not None and r["TSH"] < 0.1,
        "message": "TSH منخفض جداً مع استخدام الليفوثيروكسين — احتمال جرعة زائدة.",
        "severity": "warning",
    },
    {
        "code": "sulfonylurea_hypoglycemia",
        "drugs": {"glibenclamide", "glimepiride", "gliclazide"},
        "check": lambda r: "GLU" in r and r["GLU"] is not None and r["GLU"] < 70,
        "message": "سكر الدم منخفض مع استخدام السلفونيل يوريا — راجع الطبيب.",
        "severity": "critical",
    },
]


def _normalize_meds(meds: Iterable[str]) -> set[str]:
    return {m.strip().lower() for m in meds if m and m.strip()}


def check_drug_interaction(
    citizen_id: int,
    test_results: dict,
    db: Session,
    *,
    medications: Optional[Iterable[str]] = None,
) -> list[Alert]:
    """Apply the rule-based drug/result interaction table.

    ``test_results`` is a ``{test_code: numeric_value}`` dict. ``medications``
    is an iterable of lower-cased drug names for the citizen. We accept meds
    explicitly because NHOP does not yet track a prescription table.
    """
    meds = _normalize_meds(medications or [])
    results = {
        (k or "").strip().upper(): v for k, v in (test_results or {}).items()
    }
    alerts: list[Alert] = []
    for rule in _DRUG_RULES:
        if rule["drugs"] & meds and rule["check"](results):
            alerts.append(Alert(
                code=rule["code"],
                message=rule["message"],
                severity=rule["severity"],
            ))
    return alerts
