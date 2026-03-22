"""
GULA Clinical Intelligence Layer
Detects multi-test patterns and generates composite clinical alerts.

Rules-based (NOT AI) — deterministic, auditable, safe for clinical use.
This does NOT diagnose — it flags patterns requiring physician attention.
"""

from typing import Optional

# ─── Pattern Definitions ──────────────────────────────────────────────────────
# Each pattern: list of (test_key, condition_fn) + alert metadata

def _key(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


CLINICAL_PATTERNS = [
    {
        "id": "sepsis_risk",
        "name": "Possible Sepsis Pattern",
        "name_ar": "نمط محتمل للإنتان",
        "severity": "critical",
        "message": "WBC markedly elevated with abnormal hemoglobin and low platelets — possible sepsis or severe infection.",
        "message_ar": "ارتفاع واضح في كريات الدم البيضاء مع هيموغلوبين غير طبيعي وصفائح منخفضة — يُشير إلى إنتان محتمل أو عدوى شديدة.",
        "action": "Urgent physician review required.",
        "action_ar": "تلزم مراجعة طبية عاجلة.",
        "requires": ["wbc", "hemoglobin", "platelets"],
        "check": lambda r: (
            r.get("wbc", 0) > 15.0 and
            (r.get("hemoglobin", 99) < 10.0 or r.get("hemoglobin", 0) > 18.0) and
            r.get("platelets", 999) < 100
        ),
    },
    {
        "id": "dka_risk",
        "name": "Possible Diabetic Ketoacidosis (DKA)",
        "name_ar": "نمط محتمل للحماض الكيتوني السكري",
        "severity": "critical",
        "message": "Critically high glucose with markedly elevated HbA1c — possible DKA or uncontrolled diabetes.",
        "message_ar": "غلوكوز مرتفع بشكل حرج مع HbA1c مرتفع جداً — يُشير إلى حماض كيتوني محتمل أو سكري غير مسيطر عليه.",
        "action": "Immediate medical assessment required.",
        "action_ar": "تلزم تقييم طبي فوري.",
        "requires": ["glucose", "hba1c"],
        "check": lambda r: (
            r.get("glucose", 0) > 300 and
            r.get("hba1c", 0) > 8.0
        ),
    },
    {
        "id": "anemia_severe",
        "name": "Severe Anemia",
        "name_ar": "فقر دم شديد",
        "severity": "critical",
        "message": "Hemoglobin critically low with elevated WBC — possible hemolytic anemia or blood loss.",
        "message_ar": "هيموغلوبين منخفض بشكل حرج مع ارتفاع كريات الدم البيضاء — يُشير إلى فقر دم انحلالي أو نزيف.",
        "action": "Urgent hematology workup recommended.",
        "action_ar": "يُوصى بإجراء فحوصات دموية عاجلة.",
        "requires": ["hemoglobin", "wbc"],
        "check": lambda r: (
            r.get("hemoglobin", 99) < 7.0 and
            r.get("wbc", 0) > 12.0
        ),
    },
    {
        "id": "thyroid_storm_risk",
        "name": "Possible Thyroid Storm Risk",
        "name_ar": "نمط مخاطرة بعاصفة درقية",
        "severity": "warning",
        "message": "TSH critically suppressed with markedly elevated T-related indicators.",
        "message_ar": "TSH منخفض بشكل حرج — يُشير إلى خطر عاصفة درقية.",
        "action": "Endocrinology review recommended.",
        "action_ar": "يُوصى بمراجعة متخصص في الغدد الصماء.",
        "requires": ["tsh"],
        "check": lambda r: r.get("tsh", 99) < 0.01,
    },
    {
        "id": "renal_failure_risk",
        "name": "Possible Acute Renal Failure",
        "name_ar": "نمط محتمل لفشل كلوي حاد",
        "severity": "critical",
        "message": "Both creatinine and urea markedly elevated — possible acute kidney injury.",
        "message_ar": "ارتفاع ملحوظ في الكرياتينين واليوريا معاً — يُشير إلى إصابة كلوية حادة محتملة.",
        "action": "Nephrology consult recommended urgently.",
        "action_ar": "يُوصى بمشاورة أمراض الكلى بشكل عاجل.",
        "requires": ["creatinine", "urea"],
        "check": lambda r: (
            r.get("creatinine", 0) > 3.0 and
            r.get("urea", 0) > 80
        ),
    },
    {
        "id": "liver_injury_severe",
        "name": "Severe Hepatic Injury",
        "name_ar": "إصابة كبدية شديدة",
        "severity": "critical",
        "message": "Both ALT and AST markedly elevated — possible acute hepatitis or liver failure.",
        "message_ar": "ارتفاع ملحوظ في ALT وAST معاً — يُشير إلى التهاب كبد حاد أو فشل كبدي محتمل.",
        "action": "Hepatology assessment required.",
        "action_ar": "تلزم تقييم أمراض الكبد.",
        "requires": ["alt", "ast"],
        "check": lambda r: (
            r.get("alt", 0) > 200 and
            r.get("ast", 0) > 200
        ),
    },
    {
        "id": "electrolyte_crisis",
        "name": "Electrolyte Crisis",
        "name_ar": "أزمة شوارد كهربائية",
        "severity": "critical",
        "message": "Critical potassium and/or sodium levels — risk of cardiac arrhythmia.",
        "message_ar": "مستويات حرجة من البوتاسيوم و/أو الصوديوم — خطر اضطراب نظم القلب.",
        "action": "Immediate cardiac monitoring and electrolyte correction.",
        "action_ar": "مراقبة قلبية فورية وتصحيح الشوارد.",
        "requires": ["potassium"],
        "check": lambda r: (
            r.get("potassium", 4) < 2.5 or
            r.get("potassium", 4) > 6.5 or
            r.get("sodium", 140) < 120 or
            r.get("sodium", 140) > 160
        ),
    },
    {
        "id": "hyperlipidemia_severe",
        "name": "Severe Hyperlipidemia",
        "name_ar": "فرط شحوم الدم الشديد",
        "severity": "warning",
        "message": "Both cholesterol and triglycerides significantly elevated — high cardiovascular risk.",
        "message_ar": "ارتفاع ملحوظ في الكوليسترول والدهون الثلاثية معاً — خطر قلبي وعائي مرتفع.",
        "action": "Cardiovascular risk assessment recommended.",
        "action_ar": "يُوصى بتقييم مخاطر القلب والأوعية الدموية.",
        "requires": ["cholesterol", "triglycerides"],
        "check": lambda r: (
            r.get("cholesterol", 0) > 300 and
            r.get("triglycerides", 0) > 300
        ),
    },
]


def analyze_results(results: list[dict]) -> list[dict]:
    """
    Analyze a list of lab results for multi-test clinical patterns.

    Args:
        results: list of dicts with keys: test_name, value

    Returns:
        list of detected pattern alerts (empty if all normal)
    """
    # Build normalized lookup: {test_key: value}
    lookup: dict[str, float] = {}
    for r in results:
        if r.get("value") is not None:
            k = _key(r.get("test_name", ""))
            try:
                lookup[k] = float(r["value"])
            except (ValueError, TypeError):
                pass

    if not lookup:
        return []

    alerts = []
    for pattern in CLINICAL_PATTERNS:
        # Only evaluate if at least one required test is present
        present = [k for k in pattern["requires"] if k in lookup]
        if not present:
            continue

        try:
            if pattern["check"](lookup):
                alerts.append({
                    "pattern_id": pattern["id"],
                    "name": pattern["name"],
                    "name_ar": pattern["name_ar"],
                    "severity": pattern["severity"],
                    "message": pattern["message"],
                    "message_ar": pattern["message_ar"],
                    "action": pattern["action"],
                    "action_ar": pattern["action_ar"],
                    "tests_involved": present,
                })
        except Exception:
            continue

    # Sort: critical first
    alerts.sort(key=lambda a: 0 if a["severity"] == "critical" else 1)
    return alerts


def quick_flag_summary(results: list[dict]) -> dict:
    """
    Produce a quick summary of result flags for a batch.
    Returns counts: {normal, high, low, critical, total}
    """
    from .interpretation import get_flag

    counts = {"normal": 0, "high": 0, "low": 0, "critical": 0, "unknown": 0}
    for r in results:
        val = r.get("value")
        if val is None:
            continue
        flag = get_flag(
            float(val),
            r.get("normal_range_low"),
            r.get("normal_range_high"),
            r.get("test_name"),
        )
        counts[flag] = counts.get(flag, 0) + 1

    counts["total"] = sum(counts.values())
    return counts
