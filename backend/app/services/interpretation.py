"""
GULA Smart Interpretation Engine
Provides simple, safe medical interpretations for lab results.
NOT a diagnostic tool - informational only.
"""

# Common test interpretations database
INTERPRETATIONS = {
    "glucose": {
        "unit": "mg/dL",
        "low": {"threshold": 70, "text": "Blood sugar is below the normal range. This may indicate hypoglycemia.", "text_ar": "مستوى السكر في الدم أقل من الطبيعي. قد يشير إلى انخفاض سكر الدم.", "advice": "Consider eating a small meal. If symptoms persist, consult your doctor.", "advice_ar": "يُنصح بتناول وجبة خفيفة. إذا استمرت الأعراض، راجع طبيبك."},
        "normal": {"text": "Blood sugar is within the normal range.", "text_ar": "مستوى السكر في الدم ضمن المعدل الطبيعي.", "advice": "No action needed. Maintain healthy habits.", "advice_ar": "لا حاجة لإجراء. حافظ على نمط حياة صحي."},
        "high": {"threshold": 100, "text": "Blood sugar is above the normal range.", "text_ar": "مستوى السكر في الدم أعلى من الطبيعي.", "advice": "Consider repeating the test while fasting. Consult your doctor.", "advice_ar": "يُنصح بإعادة التحليل صائماً. راجع طبيبك."},
        "critical_high": {"threshold": 200, "text": "Blood sugar is significantly elevated.", "text_ar": "مستوى السكر في الدم مرتفع بشكل ملحوظ.", "advice": "Please consult your doctor as soon as possible.", "advice_ar": "يرجى مراجعة الطبيب في أقرب وقت ممكن."},
    },
    "hemoglobin": {
        "unit": "g/dL",
        "low": {"threshold": 12, "text": "Hemoglobin is below normal. This may indicate anemia.", "text_ar": "الهيموغلوبين أقل من الطبيعي. قد يشير إلى فقر الدم.", "advice": "An iron profile test is recommended. Consult your doctor.", "advice_ar": "يُنصح بإجراء فحص مخزون الحديد. راجع طبيبك."},
        "normal": {"text": "Hemoglobin level is normal.", "text_ar": "مستوى الهيموغلوبين طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 17, "text": "Hemoglobin is above normal.", "text_ar": "الهيموغلوبين أعلى من الطبيعي.", "advice": "Consult your doctor for further evaluation.", "advice_ar": "راجع طبيبك لمزيد من التقييم."},
    },
    "wbc": {
        "unit": "×10³/µL",
        "low": {"threshold": 4.0, "text": "White blood cell count is low.", "text_ar": "عدد كريات الدم البيضاء منخفض.", "advice": "This may indicate a weakened immune system. Consult your doctor.", "advice_ar": "قد يشير إلى ضعف في المناعة. راجع طبيبك."},
        "normal": {"text": "White blood cell count is normal.", "text_ar": "عدد كريات الدم البيضاء طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 11.0, "text": "White blood cell count is elevated.", "text_ar": "عدد كريات الدم البيضاء مرتفع.", "advice": "May indicate infection or inflammation. Consult your doctor.", "advice_ar": "قد يشير إلى التهاب أو عدوى. راجع طبيبك."},
    },
    "platelets": {
        "unit": "×10³/µL",
        "low": {"threshold": 150, "text": "Platelet count is low.", "text_ar": "عدد الصفائح الدموية منخفض.", "advice": "Consult your doctor for evaluation.", "advice_ar": "راجع طبيبك للتقييم."},
        "normal": {"text": "Platelet count is normal.", "text_ar": "عدد الصفائح الدموية طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 400, "text": "Platelet count is elevated.", "text_ar": "عدد الصفائح الدموية مرتفع.", "advice": "Consult your doctor for evaluation.", "advice_ar": "راجع طبيبك للتقييم."},
    },
    "creatinine": {
        "unit": "mg/dL",
        "low": {"threshold": 0.6, "text": "Creatinine is below normal.", "text_ar": "الكرياتينين أقل من الطبيعي.", "advice": "Usually not concerning. Consult your doctor if needed.", "advice_ar": "عادة لا يستدعي القلق. راجع طبيبك عند الحاجة."},
        "normal": {"text": "Kidney function appears normal.", "text_ar": "وظائف الكلى تبدو طبيعية.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 1.3, "text": "Creatinine is elevated. May indicate kidney function changes.", "text_ar": "الكرياتينين مرتفع. قد يشير إلى تغير في وظائف الكلى.", "advice": "Consult your doctor for kidney function evaluation.", "advice_ar": "راجع طبيبك لتقييم وظائف الكلى."},
    },
    "urea": {
        "unit": "mg/dL",
        "low": {"threshold": 15, "text": "Urea is below normal.", "text_ar": "اليوريا أقل من الطبيعي.", "advice": "Usually not concerning.", "advice_ar": "عادة لا يستدعي القلق."},
        "normal": {"text": "Urea level is normal.", "text_ar": "مستوى اليوريا طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 45, "text": "Urea is elevated.", "text_ar": "اليوريا مرتفعة.", "advice": "May indicate kidney function changes. Consult your doctor.", "advice_ar": "قد يشير إلى تغير في وظائف الكلى. راجع طبيبك."},
    },
    "cholesterol": {
        "unit": "mg/dL",
        "normal": {"text": "Total cholesterol is within desirable range.", "text_ar": "الكوليسترول الكلي ضمن المعدل المرغوب.", "advice": "Maintain a healthy diet.", "advice_ar": "حافظ على نظام غذائي صحي."},
        "high": {"threshold": 200, "text": "Total cholesterol is above desirable range.", "text_ar": "الكوليسترول الكلي أعلى من المعدل المرغوب.", "advice": "Consider dietary changes and consult your doctor.", "advice_ar": "يُنصح بتعديل النظام الغذائي ومراجعة الطبيب."},
    },
    "triglycerides": {
        "unit": "mg/dL",
        "normal": {"text": "Triglycerides are within normal range.", "text_ar": "الدهون الثلاثية ضمن المعدل الطبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 150, "text": "Triglycerides are elevated.", "text_ar": "الدهون الثلاثية مرتفعة.", "advice": "Consider dietary changes and exercise. Consult your doctor.", "advice_ar": "يُنصح بتعديل النظام الغذائي وممارسة الرياضة. راجع طبيبك."},
    },
    "alt": {
        "unit": "U/L",
        "normal": {"text": "Liver enzyme ALT is normal.", "text_ar": "إنزيم الكبد ALT طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 40, "text": "Liver enzyme ALT is elevated.", "text_ar": "إنزيم الكبد ALT مرتفع.", "advice": "May indicate liver stress. Consult your doctor.", "advice_ar": "قد يشير إلى إجهاد الكبد. راجع طبيبك."},
    },
    "ast": {
        "unit": "U/L",
        "normal": {"text": "Liver enzyme AST is normal.", "text_ar": "إنزيم الكبد AST طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 40, "text": "Liver enzyme AST is elevated.", "text_ar": "إنزيم الكبد AST مرتفع.", "advice": "May indicate liver stress. Consult your doctor.", "advice_ar": "قد يشير إلى إجهاد الكبد. راجع طبيبك."},
    },
    "tsh": {
        "unit": "mIU/L",
        "low": {"threshold": 0.4, "text": "TSH is below normal. May indicate overactive thyroid.", "text_ar": "هرمون TSH أقل من الطبيعي. قد يشير إلى فرط نشاط الغدة الدرقية.", "advice": "Consult your doctor for thyroid evaluation.", "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية."},
        "normal": {"text": "Thyroid function appears normal.", "text_ar": "وظيفة الغدة الدرقية تبدو طبيعية.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 4.5, "text": "TSH is above normal. May indicate underactive thyroid.", "text_ar": "هرمون TSH أعلى من الطبيعي. قد يشير إلى قصور الغدة الدرقية.", "advice": "Consult your doctor for thyroid evaluation.", "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية."},
    },
    "potassium": {
        "unit": "mEq/L",
        "low": {"threshold": 3.5, "text": "Potassium is below normal.", "text_ar": "البوتاسيوم أقل من الطبيعي.", "advice": "Consult your doctor.", "advice_ar": "راجع طبيبك."},
        "normal": {"text": "Potassium level is normal.", "text_ar": "مستوى البوتاسيوم طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 5.0, "text": "Potassium is elevated.", "text_ar": "البوتاسيوم مرتفع.", "advice": "Consult your doctor promptly.", "advice_ar": "راجع طبيبك في أقرب وقت."},
        "critical_high": {"threshold": 6.0, "text": "Potassium is critically elevated!", "text_ar": "البوتاسيوم مرتفع بشكل خطير!", "advice": "Seek immediate medical attention.", "advice_ar": "يرجى مراجعة الطبيب فوراً."},
    },
    "sodium": {
        "unit": "mEq/L",
        "low": {"threshold": 135, "text": "Sodium is below normal.", "text_ar": "الصوديوم أقل من الطبيعي.", "advice": "Consult your doctor.", "advice_ar": "راجع طبيبك."},
        "normal": {"text": "Sodium level is normal.", "text_ar": "مستوى الصوديوم طبيعي.", "advice": "No action needed.", "advice_ar": "لا حاجة لإجراء."},
        "high": {"threshold": 145, "text": "Sodium is elevated.", "text_ar": "الصوديوم مرتفع.", "advice": "Consult your doctor.", "advice_ar": "راجع طبيبك."},
    },
    "hba1c": {
        "unit": "%",
        "normal": {"text": "HbA1c is normal. Blood sugar control is good.", "text_ar": "HbA1c طبيعي. السيطرة على السكر جيدة.", "advice": "Maintain healthy lifestyle.", "advice_ar": "حافظ على نمط حياة صحي."},
        "high": {"threshold": 5.7, "text": "HbA1c is elevated. May indicate prediabetes or diabetes.", "text_ar": "HbA1c مرتفع. قد يشير إلى ما قبل السكري أو السكري.", "advice": "Consult your doctor for diabetes screening.", "advice_ar": "راجع طبيبك لفحص السكري."},
        "critical_high": {"threshold": 6.5, "text": "HbA1c indicates diabetes range.", "text_ar": "HbA1c في نطاق السكري.", "advice": "Please consult your doctor for diabetes management.", "advice_ar": "يرجى مراجعة الطبيب لإدارة السكري."},
    },
    "vitamin_d": {
        "unit": "ng/mL",
        "low": {"threshold": 20, "text": "Vitamin D is deficient.", "text_ar": "فيتامين د منخفض (نقص).", "advice": "Vitamin D supplementation may be needed. Consult your doctor.", "advice_ar": "قد تحتاج مكملات فيتامين د. راجع طبيبك."},
        "normal": {"text": "Vitamin D level is sufficient.", "text_ar": "مستوى فيتامين د كافٍ.", "advice": "Maintain sun exposure and healthy diet.", "advice_ar": "حافظ على التعرض للشمس والغذاء الصحي."},
        "high": {"threshold": 100, "text": "Vitamin D is elevated.", "text_ar": "فيتامين د مرتفع.", "advice": "Review supplementation with your doctor.", "advice_ar": "راجع المكملات مع طبيبك."},
    },
}


def interpret_result(test_name: str, value: float, normal_low: float = None, normal_high: float = None) -> dict:
    """
    Interpret a lab result and return explanation + advice.
    Returns both English and Arabic interpretations.
    """
    test_key = test_name.lower().replace(" ", "_").replace("-", "_")

    # Try to find matching interpretation
    interp = INTERPRETATIONS.get(test_key)

    if interp:
        return _interpret_with_rules(interp, value)

    # Fallback: generic interpretation based on normal range
    return _interpret_generic(value, normal_low, normal_high)


def _interpret_with_rules(interp: dict, value: float) -> dict:
    """Interpret using predefined rules."""
    # Check critical high first
    if "critical_high" in interp and value >= interp["critical_high"]["threshold"]:
        info = interp["critical_high"]
        return {
            "status": "critical",
            "interpretation": info["text"],
            "interpretation_ar": info["text_ar"],
            "advice": info["advice"],
            "advice_ar": info["advice_ar"],
        }

    # Check high
    if "high" in interp and "threshold" in interp["high"] and value >= interp["high"]["threshold"]:
        info = interp["high"]
        return {
            "status": "high",
            "interpretation": info["text"],
            "interpretation_ar": info["text_ar"],
            "advice": info["advice"],
            "advice_ar": info["advice_ar"],
        }

    # Check low
    if "low" in interp and "threshold" in interp["low"] and value < interp["low"]["threshold"]:
        info = interp["low"]
        return {
            "status": "low",
            "interpretation": info["text"],
            "interpretation_ar": info["text_ar"],
            "advice": info["advice"],
            "advice_ar": info["advice_ar"],
        }

    # Normal
    info = interp["normal"]
    return {
        "status": "normal",
        "interpretation": info["text"],
        "interpretation_ar": info["text_ar"],
        "advice": info["advice"],
        "advice_ar": info["advice_ar"],
    }


def _interpret_generic(value: float, normal_low: float = None, normal_high: float = None) -> dict:
    """Generic interpretation when no specific rules exist."""
    if normal_low is not None and normal_high is not None:
        if value < normal_low:
            return {
                "status": "low",
                "interpretation": "The result is below the normal range.",
                "interpretation_ar": "النتيجة أقل من المعدل الطبيعي.",
                "advice": "Consult your doctor for evaluation.",
                "advice_ar": "راجع طبيبك للتقييم.",
            }
        elif value > normal_high:
            return {
                "status": "high",
                "interpretation": "The result is above the normal range.",
                "interpretation_ar": "النتيجة أعلى من المعدل الطبيعي.",
                "advice": "Consult your doctor for evaluation.",
                "advice_ar": "راجع طبيبك للتقييم.",
            }
        else:
            return {
                "status": "normal",
                "interpretation": "The result is within the normal range.",
                "interpretation_ar": "النتيجة ضمن المعدل الطبيعي.",
                "advice": "No action needed.",
                "advice_ar": "لا حاجة لإجراء.",
            }

    return {
        "status": "unknown",
        "interpretation": "Unable to interpret without reference range.",
        "interpretation_ar": "لا يمكن التفسير بدون المدى المرجعي.",
        "advice": "Consult your doctor.",
        "advice_ar": "راجع طبيبك.",
    }


def get_flag(value: float, normal_low: float = None, normal_high: float = None) -> str:
    """Return flag for result: H, L, normal, or critical."""
    if normal_low is None or normal_high is None:
        return "unknown"
    if value < normal_low:
        return "L"
    elif value > normal_high:
        critical_threshold = normal_high * 1.5
        if value >= critical_threshold:
            return "critical"
        return "H"
    return "normal"
