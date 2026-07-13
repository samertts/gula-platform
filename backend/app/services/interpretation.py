"""
GULA Smart Interpretation Engine
Provides simple, safe medical interpretations for lab results.
NOT a diagnostic tool - informational only.
"""

# Common test interpretations database
INTERPRETATIONS = {
    "glucose": {
        "unit": "mg/dL",
        "low": {
            "threshold": 70,
            "text": "Blood sugar is below the normal range. This may indicate hypoglycemia.",
            "text_ar": "مستوى السكر في الدم أقل من الطبيعي. قد يشير إلى انخفاض سكر الدم.",
            "advice": "Consider eating a small meal. If symptoms persist, consult your doctor.",
            "advice_ar": "يُنصح بتناول وجبة خفيفة. إذا استمرت الأعراض، راجع طبيبك.",
        },
        "normal": {
            "text": "Blood sugar is within the normal range.",
            "text_ar": "مستوى السكر في الدم ضمن المعدل الطبيعي.",
            "advice": "No action needed. Maintain healthy habits.",
            "advice_ar": "لا حاجة لإجراء. حافظ على نمط حياة صحي.",
        },
        "high": {
            "threshold": 100,
            "text": "Blood sugar is above the normal range.",
            "text_ar": "مستوى السكر في الدم أعلى من الطبيعي.",
            "advice": "Consider repeating the test while fasting. Consult your doctor.",
            "advice_ar": "يُنصح بإعادة التحليل صائماً. راجع طبيبك.",
        },
        "critical_high": {
            "threshold": 200,
            "text": "Blood sugar is significantly elevated.",
            "text_ar": "مستوى السكر في الدم مرتفع بشكل ملحوظ.",
            "advice": "Please consult your doctor as soon as possible.",
            "advice_ar": "يرجى مراجعة الطبيب في أقرب وقت ممكن.",
        },
    },
    "hemoglobin": {
        "unit": "g/dL",
        "low": {
            "threshold": 12,
            "text": "Hemoglobin is below normal. This may indicate anemia.",
            "text_ar": "الهيموغلوبين أقل من الطبيعي. قد يشير إلى فقر الدم.",
            "advice": "An iron profile test is recommended. Consult your doctor.",
            "advice_ar": "يُنصح بإجراء فحص مخزون الحديد. راجع طبيبك.",
        },
        "normal": {
            "text": "Hemoglobin level is normal.",
            "text_ar": "مستوى الهيموغلوبين طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 17,
            "text": "Hemoglobin is above normal.",
            "text_ar": "الهيموغلوبين أعلى من الطبيعي.",
            "advice": "Consult your doctor for further evaluation.",
            "advice_ar": "راجع طبيبك لمزيد من التقييم.",
        },
    },
    "wbc": {
        "unit": "×10³/µL",
        "low": {
            "threshold": 4.0,
            "text": "White blood cell count is low.",
            "text_ar": "عدد كريات الدم البيضاء منخفض.",
            "advice": "This may indicate a weakened immune system. Consult your doctor.",
            "advice_ar": "قد يشير إلى ضعف في المناعة. راجع طبيبك.",
        },
        "normal": {
            "text": "White blood cell count is normal.",
            "text_ar": "عدد كريات الدم البيضاء طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 11.0,
            "text": "White blood cell count is elevated.",
            "text_ar": "عدد كريات الدم البيضاء مرتفع.",
            "advice": "May indicate infection or inflammation. Consult your doctor.",
            "advice_ar": "قد يشير إلى التهاب أو عدوى. راجع طبيبك.",
        },
    },
    "platelets": {
        "unit": "×10³/µL",
        "low": {
            "threshold": 150,
            "text": "Platelet count is low.",
            "text_ar": "عدد الصفائح الدموية منخفض.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "normal": {
            "text": "Platelet count is normal.",
            "text_ar": "عدد الصفائح الدموية طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 400,
            "text": "Platelet count is elevated.",
            "text_ar": "عدد الصفائح الدموية مرتفع.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
    },
    "creatinine": {
        "unit": "mg/dL",
        "low": {
            "threshold": 0.6,
            "text": "Creatinine is below normal.",
            "text_ar": "الكرياتينين أقل من الطبيعي.",
            "advice": "Usually not concerning. Consult your doctor if needed.",
            "advice_ar": "عادة لا يستدعي القلق. راجع طبيبك عند الحاجة.",
        },
        "normal": {
            "text": "Kidney function appears normal.",
            "text_ar": "وظائف الكلى تبدو طبيعية.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 1.3,
            "text": "Creatinine is elevated. May indicate kidney function changes.",
            "text_ar": "الكرياتينين مرتفع. قد يشير إلى تغير في وظائف الكلى.",
            "advice": "Consult your doctor for kidney function evaluation.",
            "advice_ar": "راجع طبيبك لتقييم وظائف الكلى.",
        },
    },
    "urea": {
        "unit": "mg/dL",
        "low": {
            "threshold": 15,
            "text": "Urea is below normal.",
            "text_ar": "اليوريا أقل من الطبيعي.",
            "advice": "Usually not concerning.",
            "advice_ar": "عادة لا يستدعي القلق.",
        },
        "normal": {
            "text": "Urea level is normal.",
            "text_ar": "مستوى اليوريا طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 45,
            "text": "Urea is elevated.",
            "text_ar": "اليوريا مرتفعة.",
            "advice": "May indicate kidney function changes. Consult your doctor.",
            "advice_ar": "قد يشير إلى تغير في وظائف الكلى. راجع طبيبك.",
        },
    },
    "cholesterol": {
        "unit": "mg/dL",
        "normal": {
            "text": "Total cholesterol is within desirable range.",
            "text_ar": "الكوليسترول الكلي ضمن المعدل المرغوب.",
            "advice": "Maintain a healthy diet.",
            "advice_ar": "حافظ على نظام غذائي صحي.",
        },
        "high": {
            "threshold": 200,
            "text": "Total cholesterol is above desirable range.",
            "text_ar": "الكوليسترول الكلي أعلى من المعدل المرغوب.",
            "advice": "Consider dietary changes and consult your doctor.",
            "advice_ar": "يُنصح بتعديل النظام الغذائي ومراجعة الطبيب.",
        },
    },
    "triglycerides": {
        "unit": "mg/dL",
        "normal": {
            "text": "Triglycerides are within normal range.",
            "text_ar": "الدهون الثلاثية ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 150,
            "text": "Triglycerides are elevated.",
            "text_ar": "الدهون الثلاثية مرتفعة.",
            "advice": "Consider dietary changes and exercise. Consult your doctor.",
            "advice_ar": "يُنصح بتعديل النظام الغذائي وممارسة الرياضة. راجع طبيبك.",
        },
    },
    "alt": {
        "unit": "U/L",
        "normal": {
            "text": "Liver enzyme ALT is normal.",
            "text_ar": "إنزيم الكبد ALT طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 40,
            "text": "Liver enzyme ALT is elevated.",
            "text_ar": "إنزيم الكبد ALT مرتفع.",
            "advice": "May indicate liver stress. Consult your doctor.",
            "advice_ar": "قد يشير إلى إجهاد الكبد. راجع طبيبك.",
        },
    },
    "ast": {
        "unit": "U/L",
        "normal": {
            "text": "Liver enzyme AST is normal.",
            "text_ar": "إنزيم الكبد AST طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 40,
            "text": "Liver enzyme AST is elevated.",
            "text_ar": "إنزيم الكبد AST مرتفع.",
            "advice": "May indicate liver stress. Consult your doctor.",
            "advice_ar": "قد يشير إلى إجهاد الكبد. راجع طبيبك.",
        },
    },
    "tsh": {
        "unit": "mIU/L",
        "low": {
            "threshold": 0.4,
            "text": "TSH is below normal. May indicate overactive thyroid.",
            "text_ar": "هرمون TSH أقل من الطبيعي. قد يشير إلى فرط نشاط الغدة الدرقية.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
        "normal": {
            "text": "Thyroid function appears normal.",
            "text_ar": "وظيفة الغدة الدرقية تبدو طبيعية.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 4.5,
            "text": "TSH is above normal. May indicate underactive thyroid.",
            "text_ar": "هرمون TSH أعلى من الطبيعي. قد يشير إلى قصور الغدة الدرقية.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
    },
    "potassium": {
        "unit": "mEq/L",
        "low": {
            "threshold": 3.5,
            "text": "Potassium is below normal.",
            "text_ar": "البوتاسيوم أقل من الطبيعي.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "normal": {
            "text": "Potassium level is normal.",
            "text_ar": "مستوى البوتاسيوم طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 5.0,
            "text": "Potassium is elevated.",
            "text_ar": "البوتاسيوم مرتفع.",
            "advice": "Consult your doctor promptly.",
            "advice_ar": "راجع طبيبك في أقرب وقت.",
        },
        "critical_high": {
            "threshold": 6.0,
            "text": "Potassium is critically elevated!",
            "text_ar": "البوتاسيوم مرتفع بشكل خطير!",
            "advice": "Seek immediate medical attention.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    "sodium": {
        "unit": "mEq/L",
        "low": {
            "threshold": 135,
            "text": "Sodium is below normal.",
            "text_ar": "الصوديوم أقل من الطبيعي.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "normal": {
            "text": "Sodium level is normal.",
            "text_ar": "مستوى الصوديوم طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 145,
            "text": "Sodium is elevated.",
            "text_ar": "الصوديوم مرتفع.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
    },
    "hba1c": {
        "unit": "%",
        "normal": {
            "text": "HbA1c is normal. Blood sugar control is good.",
            "text_ar": "HbA1c طبيعي. السيطرة على السكر جيدة.",
            "advice": "Maintain healthy lifestyle.",
            "advice_ar": "حافظ على نمط حياة صحي.",
        },
        "high": {
            "threshold": 5.7,
            "text": "HbA1c is elevated. May indicate prediabetes or diabetes.",
            "text_ar": "HbA1c مرتفع. قد يشير إلى ما قبل السكري أو السكري.",
            "advice": "Consult your doctor for diabetes screening.",
            "advice_ar": "راجع طبيبك لفحص السكري.",
        },
        "critical_high": {
            "threshold": 6.5,
            "text": "HbA1c indicates diabetes range.",
            "text_ar": "HbA1c في نطاق السكري.",
            "advice": "Please consult your doctor for diabetes management.",
            "advice_ar": "يرجى مراجعة الطبيب لإدارة السكري.",
        },
    },
    "vitamin_d": {
        "unit": "ng/mL",
        "low": {
            "threshold": 20,
            "text": "Vitamin D is deficient.",
            "text_ar": "فيتامين د منخفض (نقص).",
            "advice": "Vitamin D supplementation may be needed. Consult your doctor.",
            "advice_ar": "قد تحتاج مكملات فيتامين د. راجع طبيبك.",
        },
        "normal": {
            "text": "Vitamin D level is sufficient.",
            "text_ar": "مستوى فيتامين د كافٍ.",
            "advice": "Maintain sun exposure and healthy diet.",
            "advice_ar": "حافظ على التعرض للشمس والغذاء الصحي.",
        },
        "high": {
            "threshold": 100,
            "text": "Vitamin D is elevated.",
            "text_ar": "فيتامين د مرتفع.",
            "advice": "Review supplementation with your doctor.",
            "advice_ar": "راجع المكملات مع طبيبك.",
        },
    },
    # ─── Iron Studies ─────────────────────────────────────────────────────────
    "iron": {
        "unit": "µg/dL",
        "low": {
            "threshold": 60,
            "text": "Serum iron is below normal. May indicate iron deficiency.",
            "text_ar": "الحديد في الدم أقل من الطبيعي. قد يشير إلى نقص الحديد.",
            "advice": "An iron profile test is recommended. Consult your doctor.",
            "advice_ar": "يُنصح بإجراء فحص مستوى الحديد الكامل. راجع طبيبك.",
        },
        "normal": {
            "text": "Serum iron is within normal range.",
            "text_ar": "الحديد في الدم ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 170,
            "text": "Serum iron is elevated.",
            "text_ar": "الحديد في الدم مرتفع.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 500,
            "text": "Serum iron is critically elevated — possible iron overload.",
            "text_ar": "الحديد مرتفع بشكل خطير — يُشير إلى تراكم الحديد.",
            "advice": "Seek medical attention urgently.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    "ferritin": {
        "unit": "ng/mL",
        "low": {
            "threshold": 12,
            "text": "Ferritin is low — iron stores are depleted.",
            "text_ar": "الفيريتين منخفض — مخازن الحديد مستنزفة.",
            "advice": "Iron supplementation may be required. Consult your doctor.",
            "advice_ar": "قد تحتاج مكملات حديد. راجع طبيبك.",
        },
        "normal": {
            "text": "Ferritin level is normal.",
            "text_ar": "مستوى الفيريتين طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 300,
            "text": "Ferritin is elevated. May indicate inflammation or iron overload.",
            "text_ar": "الفيريتين مرتفع. قد يشير إلى التهاب أو تراكم الحديد.",
            "advice": "Consult your doctor for further evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 1000,
            "text": "Ferritin is markedly elevated — investigate iron overload or hepatic disease.",
            "text_ar": "الفيريتين مرتفع بشكل واضح — يستوجب تقييم تراكم الحديد أو أمراض الكبد.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    "tibc": {
        "unit": "µg/dL",
        "low": {
            "threshold": 250,
            "text": "TIBC is low — may indicate iron overload or inflammation.",
            "text_ar": "القدرة الكلية على ارتباط الحديد منخفضة — قد يشير إلى تراكم الحديد أو التهاب.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "normal": {
            "text": "TIBC is within normal range.",
            "text_ar": "القدرة الكلية على ارتباط الحديد طبيعية.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 450,
            "text": "TIBC is elevated — may indicate iron deficiency.",
            "text_ar": "القدرة الكلية على ارتباط الحديد مرتفعة — قد يشير إلى نقص الحديد.",
            "advice": "Consult your doctor for iron deficiency evaluation.",
            "advice_ar": "راجع طبيبك لتقييم نقص الحديد.",
        },
    },
    # ─── Inflammation Markers ──────────────────────────────────────────────────
    "crp": {
        "unit": "mg/L",
        "normal": {
            "text": "C-reactive protein is within normal range — no significant inflammation.",
            "text_ar": "بروتين سي التفاعلي ضمن المعدل الطبيعي — لا التهاب ملحوظ.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 5,
            "text": "CRP is elevated — possible infection or inflammation.",
            "text_ar": "CRP مرتفع — يُشير إلى التهاب أو عدوى محتملة.",
            "advice": "Consult your doctor to identify the cause.",
            "advice_ar": "راجع طبيبك لتحديد السبب.",
        },
        "critical_high": {
            "threshold": 100,
            "text": "CRP is markedly elevated — severe infection or inflammation.",
            "text_ar": "CRP مرتفع بشكل واضح — عدوى أو التهاب شديد.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    "c_reactive_protein": {
        "unit": "mg/L",
        "normal": {
            "text": "C-reactive protein is within normal range.",
            "text_ar": "بروتين سي التفاعلي ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 5,
            "text": "CRP is elevated — possible infection or inflammation.",
            "text_ar": "CRP مرتفع — يُشير إلى التهاب أو عدوى محتملة.",
            "advice": "Consult your doctor to identify the cause.",
            "advice_ar": "راجع طبيبك لتحديد السبب.",
        },
        "critical_high": {
            "threshold": 100,
            "text": "CRP is markedly elevated — severe infection or inflammation.",
            "text_ar": "CRP مرتفع بشكل واضح — عدوى أو التهاب شديد.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    "esr": {
        "unit": "mm/hr",
        "normal": {
            "text": "ESR is within normal range.",
            "text_ar": "سرعة ترسب الكريات ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 30,
            "text": "ESR is elevated — possible inflammation or infection.",
            "text_ar": "سرعة الترسب مرتفعة — يُشير إلى التهاب أو عدوى.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "critical_high": {
            "threshold": 100,
            "text": "ESR is markedly elevated — investigate systemic disease.",
            "text_ar": "سرعة الترسب مرتفعة بشكل واضح — يستوجب تقييم أمراض جهازية.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    "procalcitonin": {
        "unit": "ng/mL",
        "normal": {
            "text": "Procalcitonin is normal — bacterial infection unlikely.",
            "text_ar": "البروكالسيتونين طبيعي — العدوى البكتيرية مستبعدة.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 0.5,
            "text": "Procalcitonin elevated — possible bacterial infection.",
            "text_ar": "البروكالسيتونين مرتفع — يُشير إلى عدوى بكتيرية محتملة.",
            "advice": "Consult your doctor promptly.",
            "advice_ar": "راجع طبيبك في أقرب وقت.",
        },
        "critical_high": {
            "threshold": 2.0,
            "text": "Procalcitonin markedly elevated — high risk of sepsis.",
            "text_ar": "البروكالسيتونين مرتفع بشكل ملحوظ — خطر مرتفع للإنتان.",
            "advice": "Immediate medical attention required.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    # ─── Metabolic ─────────────────────────────────────────────────────────────
    "uric_acid": {
        "unit": "mg/dL",
        "low": {
            "threshold": 2.4,
            "text": "Uric acid is below normal.",
            "text_ar": "حمض اليوريك أقل من الطبيعي.",
            "advice": "Usually not clinically significant.",
            "advice_ar": "عادة لا يستدعي القلق.",
        },
        "normal": {
            "text": "Uric acid is within normal range.",
            "text_ar": "حمض اليوريك ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 7.0,
            "text": "Uric acid is elevated — possible gout risk.",
            "text_ar": "حمض اليوريك مرتفع — يُشير إلى خطر النقرس.",
            "advice": "Dietary modification and physician consultation recommended.",
            "advice_ar": "يُنصح بتعديل النظام الغذائي ومراجعة الطبيب.",
        },
        "critical_high": {
            "threshold": 10.0,
            "text": "Uric acid is critically elevated — risk of acute gout attack or nephropathy.",
            "text_ar": "حمض اليوريك مرتفع بشكل خطير — خطر نوبة نقرس حادة أو اعتلال كلوي.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    "calcium": {
        "unit": "mg/dL",
        "low": {
            "threshold": 8.5,
            "text": "Calcium is below normal — possible hypocalcemia.",
            "text_ar": "الكالسيوم أقل من الطبيعي — نقص كالسيوم محتمل.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "normal": {
            "text": "Calcium level is normal.",
            "text_ar": "مستوى الكالسيوم طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 10.5,
            "text": "Calcium is elevated — possible hypercalcemia.",
            "text_ar": "الكالسيوم مرتفع — فرط كالسيوم محتمل.",
            "advice": "Consult your doctor for further evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 13.0,
            "text": "Calcium is critically elevated — risk of hypercalcemic crisis.",
            "text_ar": "الكالسيوم مرتفع بشكل خطير — خطر أزمة فرط كالسيوم.",
            "advice": "Seek urgent medical attention.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    "phosphorus": {
        "unit": "mg/dL",
        "low": {
            "threshold": 2.5,
            "text": "Phosphorus is below normal.",
            "text_ar": "الفوسفور أقل من الطبيعي.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "normal": {
            "text": "Phosphorus level is normal.",
            "text_ar": "مستوى الفوسفور طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 4.5,
            "text": "Phosphorus is elevated.",
            "text_ar": "الفوسفور مرتفع.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
    },
    "magnesium": {
        "unit": "mg/dL",
        "low": {
            "threshold": 1.7,
            "text": "Magnesium is below normal — possible hypomagnesemia.",
            "text_ar": "المغنيسيوم أقل من الطبيعي — نقص مغنيسيوم محتمل.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "normal": {
            "text": "Magnesium level is normal.",
            "text_ar": "مستوى المغنيسيوم طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 2.4,
            "text": "Magnesium is elevated.",
            "text_ar": "المغنيسيوم مرتفع.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "critical_high": {
            "threshold": 4.0,
            "text": "Magnesium is critically elevated — risk of cardiac and respiratory depression.",
            "text_ar": "المغنيسيوم مرتفع بشكل خطير — خطر على القلب والتنفس.",
            "advice": "Immediate medical attention required.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    # ─── Vitamins ──────────────────────────────────────────────────────────────
    "vitamin_b12": {
        "unit": "pg/mL",
        "low": {
            "threshold": 200,
            "text": "Vitamin B12 is deficient.",
            "text_ar": "فيتامين ب12 منخفض (نقص).",
            "advice": "B12 supplementation or investigation is recommended. Consult your doctor.",
            "advice_ar": "يُنصح بمكملات ب12 أو الفحص. راجع طبيبك.",
        },
        "normal": {
            "text": "Vitamin B12 level is sufficient.",
            "text_ar": "مستوى فيتامين ب12 كافٍ.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 900,
            "text": "Vitamin B12 is elevated.",
            "text_ar": "فيتامين ب12 مرتفع.",
            "advice": "Review supplementation and consult your doctor.",
            "advice_ar": "راجع المكملات مع طبيبك.",
        },
    },
    "folate": {
        "unit": "ng/mL",
        "low": {
            "threshold": 3.0,
            "text": "Folate is deficient — risk of megaloblastic anemia.",
            "text_ar": "الفولات منخفض — خطر فقر الدم الضخم الكريات.",
            "advice": "Folic acid supplementation recommended. Consult your doctor.",
            "advice_ar": "يُنصح بمكملات حمض الفوليك. راجع طبيبك.",
        },
        "normal": {
            "text": "Folate level is normal.",
            "text_ar": "مستوى الفولات طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 20,
            "text": "Folate is elevated.",
            "text_ar": "الفولات مرتفع.",
            "advice": "Review supplementation.",
            "advice_ar": "راجع المكملات مع طبيبك.",
        },
    },
    # ─── Liver & Bilirubin ─────────────────────────────────────────────────────
    "bilirubin_total": {
        "unit": "mg/dL",
        "normal": {
            "text": "Total bilirubin is within normal range.",
            "text_ar": "البيليروبين الكلي ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 1.2,
            "text": "Total bilirubin is elevated — possible liver or hemolytic disorder.",
            "text_ar": "البيليروبين الكلي مرتفع — يُشير إلى مشكلة كبدية أو انحلال دموي.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 10.0,
            "text": "Total bilirubin is critically elevated — severe liver dysfunction.",
            "text_ar": "البيليروبين الكلي مرتفع بشكل خطير — خلل وظيفي حاد في الكبد.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    "bilirubin_direct": {
        "unit": "mg/dL",
        "normal": {
            "text": "Direct bilirubin is within normal range.",
            "text_ar": "البيليروبين المباشر ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 0.3,
            "text": "Direct bilirubin is elevated — possible liver or bile duct disease.",
            "text_ar": "البيليروبين المباشر مرتفع — يُشير إلى مشكلة كبدية أو في القناة الصفراوية.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
    },
    "ggt": {
        "unit": "U/L",
        "normal": {
            "text": "GGT is within normal range.",
            "text_ar": "إنزيم GGT ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 50,
            "text": "GGT is elevated — possible liver disease or alcohol use.",
            "text_ar": "إنزيم GGT مرتفع — يُشير إلى مشكلة كبدية أو تناول الكحول.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 300,
            "text": "GGT is markedly elevated — significant hepatic or biliary pathology.",
            "text_ar": "إنزيم GGT مرتفع بشكل واضح — اعتلال كبدي أو صفراوي مهم.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    "alp": {
        "unit": "U/L",
        "normal": {
            "text": "Alkaline phosphatase is within normal range.",
            "text_ar": "الفوسفاتاز القلوي ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 120,
            "text": "ALP is elevated — possible liver, bone, or biliary disease.",
            "text_ar": "الفوسفاتاز القلوي مرتفع — يُشير إلى أمراض الكبد أو العظام أو القنوات الصفراوية.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 500,
            "text": "ALP is markedly elevated — significant hepatic or bone pathology.",
            "text_ar": "الفوسفاتاز القلوي مرتفع بشكل واضح — اعتلال كبدي أو عظمي مهم.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    # ─── Coagulation ───────────────────────────────────────────────────────────
    "pt": {
        "unit": "seconds",
        "normal": {
            "text": "Prothrombin time is normal.",
            "text_ar": "زمن البروثرومبين طبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 14.0,
            "text": "PT is prolonged — possible coagulation disorder or anticoagulant effect.",
            "text_ar": "زمن البروثرومبين مطوّل — يُشير إلى اضطراب في التخثر.",
            "advice": "Consult your doctor for further evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 30.0,
            "text": "PT is critically prolonged — high bleeding risk.",
            "text_ar": "زمن البروثرومبين مطوّل بشكل خطير — خطر نزيف مرتفع.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    "inr": {
        "unit": "",
        "normal": {
            "text": "INR is within therapeutic or normal range.",
            "text_ar": "INR ضمن المعدل الطبيعي أو العلاجي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 1.5,
            "text": "INR is elevated — possible coagulation disorder.",
            "text_ar": "INR مرتفع — يُشير إلى اضطراب في التخثر.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
        "critical_high": {
            "threshold": 4.0,
            "text": "INR is critically elevated — high bleeding risk.",
            "text_ar": "INR مرتفع بشكل خطير — خطر نزيف مرتفع.",
            "advice": "Urgent medical attention required.",
            "advice_ar": "يرجى مراجعة الطبيب فوراً.",
        },
    },
    "aptt": {
        "unit": "seconds",
        "normal": {
            "text": "APTT is within normal range.",
            "text_ar": "زمن الثرومبوبلاستين الجزئي المنشّط ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 40.0,
            "text": "APTT is prolonged — possible coagulation factor deficiency.",
            "text_ar": "APTT مطوّل — يُشير إلى نقص عوامل التخثر.",
            "advice": "Consult your doctor for further evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 70.0,
            "text": "APTT is critically prolonged — significant coagulopathy.",
            "text_ar": "APTT مطوّل بشكل خطير — اعتلال تخثر مهم.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    # ─── Cardiac ───────────────────────────────────────────────────────────────
    "troponin": {
        "unit": "ng/mL",
        "normal": {
            "text": "Troponin is within normal range — unlikely cardiac injury.",
            "text_ar": "التروبونين ضمن المعدل الطبيعي — إصابة القلب مستبعدة.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 0.04,
            "text": "Troponin is elevated — possible myocardial injury.",
            "text_ar": "التروبونين مرتفع — يُشير إلى إصابة عضلة القلب المحتملة.",
            "advice": "Consult your doctor immediately.",
            "advice_ar": "راجع طبيبك فوراً.",
        },
        "critical_high": {
            "threshold": 0.4,
            "text": "Troponin is critically elevated — strong evidence of myocardial infarction.",
            "text_ar": "التروبونين مرتفع بشكل خطير — دليل قوي على احتشاء عضلة القلب.",
            "advice": "Seek emergency medical care immediately.",
            "advice_ar": "يرجى مراجعة الطوارئ فوراً.",
        },
    },
    "troponin_i": {
        "unit": "ng/mL",
        "normal": {
            "text": "Troponin I is within normal range — unlikely cardiac injury.",
            "text_ar": "التروبونين I ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 0.04,
            "text": "Troponin I is elevated — possible myocardial injury.",
            "text_ar": "التروبونين I مرتفع — يُشير إلى إصابة عضلة القلب.",
            "advice": "Consult your doctor immediately.",
            "advice_ar": "راجع طبيبك فوراً.",
        },
        "critical_high": {
            "threshold": 0.4,
            "text": "Troponin I is critically elevated — strong evidence of acute MI.",
            "text_ar": "التروبونين I مرتفع بشكل خطير — دليل قوي على نوبة قلبية.",
            "advice": "Seek emergency medical care immediately.",
            "advice_ar": "يرجى مراجعة الطوارئ فوراً.",
        },
    },
    "ldh": {
        "unit": "U/L",
        "normal": {
            "text": "LDH is within normal range.",
            "text_ar": "إنزيم LDH ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 250,
            "text": "LDH is elevated — possible tissue damage, hemolysis, or liver disease.",
            "text_ar": "إنزيم LDH مرتفع — يُشير إلى تلف أنسجة أو انحلال دم أو أمراض الكبد.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 1000,
            "text": "LDH is markedly elevated — severe tissue injury.",
            "text_ar": "إنزيم LDH مرتفع بشكل ملحوظ — تلف أنسجة شديد.",
            "advice": "Medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية.",
        },
    },
    "ck": {
        "unit": "U/L",
        "normal": {
            "text": "Creatine kinase (CK) is within normal range.",
            "text_ar": "الكرياتين كيناز (CK) ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 200,
            "text": "CK is elevated — possible muscle damage or cardiac injury.",
            "text_ar": "الكرياتين كيناز مرتفع — يُشير إلى تلف العضلات أو القلب.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 1000,
            "text": "CK is critically elevated — risk of rhabdomyolysis.",
            "text_ar": "الكرياتين كيناز مرتفع بشكل خطير — خطر انحلال عضلي.",
            "advice": "Urgent medical evaluation required.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    # ─── Hormones ──────────────────────────────────────────────────────────────
    "psa": {
        "unit": "ng/mL",
        "normal": {
            "text": "PSA is within normal range.",
            "text_ar": "مستضد البروستات النوعي (PSA) ضمن المعدل الطبيعي.",
            "advice": "Annual monitoring recommended for men over 50.",
            "advice_ar": "يُنصح بالفحص السنوي للرجال فوق 50 عاماً.",
        },
        "high": {
            "threshold": 4.0,
            "text": "PSA is elevated — possible prostate enlargement or cancer.",
            "text_ar": "PSA مرتفع — يُشير إلى تضخم البروستات أو خطر السرطان.",
            "advice": "Urologist consultation recommended.",
            "advice_ar": "يُنصح بمراجعة طبيب المسالك البولية.",
        },
        "critical_high": {
            "threshold": 10.0,
            "text": "PSA is significantly elevated — high suspicion of prostate pathology.",
            "text_ar": "PSA مرتفع بشكل ملحوظ — شك مرتفع في اعتلال البروستات.",
            "advice": "Prompt urologist consultation required.",
            "advice_ar": "تلزم مراجعة عاجلة لطبيب المسالك البولية.",
        },
    },
    "cortisol": {
        "unit": "µg/dL",
        "low": {
            "threshold": 5.0,
            "text": "Cortisol is below normal — possible adrenal insufficiency.",
            "text_ar": "الكورتيزول أقل من الطبيعي — قصور الغدة الكظرية المحتمل.",
            "advice": "Consult your doctor for adrenal evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الكظرية.",
        },
        "normal": {
            "text": "Cortisol level is within normal range.",
            "text_ar": "مستوى الكورتيزول ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 25.0,
            "text": "Cortisol is elevated — possible Cushing's syndrome or stress.",
            "text_ar": "الكورتيزول مرتفع — يُشير إلى متلازمة كوشينغ أو الإجهاد.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
    },
    "t3": {
        "unit": "ng/dL",
        "low": {
            "threshold": 80,
            "text": "T3 (triiodothyronine) is below normal — possible hypothyroidism.",
            "text_ar": "هرمون T3 أقل من الطبيعي — قصور الغدة الدرقية المحتمل.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
        "normal": {
            "text": "T3 level is within normal range.",
            "text_ar": "مستوى هرمون T3 ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 200,
            "text": "T3 is elevated — possible hyperthyroidism.",
            "text_ar": "هرمون T3 مرتفع — فرط نشاط الغدة الدرقية المحتمل.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
    },
    "t4": {
        "unit": "µg/dL",
        "low": {
            "threshold": 5.0,
            "text": "T4 (thyroxine) is below normal — possible hypothyroidism.",
            "text_ar": "هرمون T4 أقل من الطبيعي — قصور الغدة الدرقية المحتمل.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
        "normal": {
            "text": "T4 level is within normal range.",
            "text_ar": "مستوى هرمون T4 ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 12.5,
            "text": "T4 is elevated — possible hyperthyroidism.",
            "text_ar": "هرمون T4 مرتفع — فرط نشاط الغدة الدرقية المحتمل.",
            "advice": "Consult your doctor for thyroid evaluation.",
            "advice_ar": "راجع طبيبك لتقييم الغدة الدرقية.",
        },
    },
    # ─── Urinalysis ────────────────────────────────────────────────────────────
    "albumin_urine": {
        "unit": "mg/g",
        "normal": {
            "text": "Urine albumin is within normal range — no significant proteinuria.",
            "text_ar": "ألبومين البول ضمن المعدل الطبيعي — لا بروتينية مهمة.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 30,
            "text": "Microalbuminuria detected — early sign of kidney stress.",
            "text_ar": "بيلة ألبومين دقيقة — علامة مبكرة لضغط الكلى.",
            "advice": "Consult your doctor, especially if diabetic or hypertensive.",
            "advice_ar": "راجع طبيبك، خاصة إذا كنت مصاباً بالسكري أو ضغط الدم.",
        },
        "critical_high": {
            "threshold": 300,
            "text": "Macroalbuminuria detected — significant kidney disease.",
            "text_ar": "بيلة ألبومين كبيرة — أمراض الكلى المهمة.",
            "advice": "Nephrology referral recommended.",
            "advice_ar": "يُنصح بالإحالة لأمراض الكلى.",
        },
    },
    # ─── Pancreas ──────────────────────────────────────────────────────────────
    "amylase": {
        "unit": "U/L",
        "normal": {
            "text": "Amylase is within normal range.",
            "text_ar": "الأميليز ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 100,
            "text": "Amylase is elevated — possible pancreatitis or salivary gland disease.",
            "text_ar": "الأميليز مرتفع — يُشير إلى التهاب البنكرياس أو الغدد اللعابية.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 300,
            "text": "Amylase is markedly elevated — significant pancreatitis risk.",
            "text_ar": "الأميليز مرتفع بشكل واضح — خطر مرتفع لالتهاب البنكرياس.",
            "advice": "Medical evaluation required urgently.",
            "advice_ar": "تلزم مراجعة طبية عاجلة.",
        },
    },
    "lipase": {
        "unit": "U/L",
        "normal": {
            "text": "Lipase is within normal range.",
            "text_ar": "الليباز ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 60,
            "text": "Lipase is elevated — possible pancreatitis.",
            "text_ar": "الليباز مرتفع — يُشير إلى التهاب البنكرياس.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "critical_high": {
            "threshold": 200,
            "text": "Lipase is markedly elevated — acute pancreatitis likely.",
            "text_ar": "الليباز مرتفع بشكل واضح — التهاب البنكرياس الحاد مرجّح.",
            "advice": "Urgent medical care required.",
            "advice_ar": "تلزم رعاية طبية عاجلة.",
        },
    },
    # ─── Protein ───────────────────────────────────────────────────────────────
    "total_protein": {
        "unit": "g/dL",
        "low": {
            "threshold": 6.0,
            "text": "Total protein is below normal — possible malnutrition or liver disease.",
            "text_ar": "البروتين الكلي أقل من الطبيعي — يُشير إلى سوء التغذية أو أمراض الكبد.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "normal": {
            "text": "Total protein is within normal range.",
            "text_ar": "البروتين الكلي ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 8.5,
            "text": "Total protein is elevated — possible dehydration or dysproteinemia.",
            "text_ar": "البروتين الكلي مرتفع — يُشير إلى جفاف أو اضطراب البروتين.",
            "advice": "Consult your doctor.",
            "advice_ar": "راجع طبيبك.",
        },
    },
    "albumin": {
        "unit": "g/dL",
        "low": {
            "threshold": 3.4,
            "text": "Albumin is below normal — possible malnutrition, liver disease, or nephrotic syndrome.",
            "text_ar": "الألبومين أقل من الطبيعي — يُشير إلى سوء التغذية أو أمراض الكبد أو المتلازمة الكلائية.",
            "advice": "Consult your doctor for evaluation.",
            "advice_ar": "راجع طبيبك للتقييم.",
        },
        "normal": {
            "text": "Albumin is within normal range.",
            "text_ar": "الألبومين ضمن المعدل الطبيعي.",
            "advice": "No action needed.",
            "advice_ar": "لا حاجة لإجراء.",
        },
        "high": {
            "threshold": 5.4,
            "text": "Albumin is elevated — possible dehydration.",
            "text_ar": "الألبومين مرتفع — يُشير إلى جفاف.",
            "advice": "Ensure adequate fluid intake.",
            "advice_ar": "احرص على شرب كميات كافية من الماء.",
        },
    },
}


def interpret_result(
    test_name: str, value: float, normal_low: float | None = None, normal_high: float | None = None
) -> dict:
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


def _interpret_generic(
    value: float, normal_low: float | None = None, normal_high: float | None = None
) -> dict:
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
        if value > normal_high:
            return {
                "status": "high",
                "interpretation": "The result is above the normal range.",
                "interpretation_ar": "النتيجة أعلى من المعدل الطبيعي.",
                "advice": "Consult your doctor for evaluation.",
                "advice_ar": "راجع طبيبك للتقييم.",
            }
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


def get_flag(
    value: float,
    normal_low: float | None = None,
    normal_high: float | None = None,
    test_name: str | None = None,
) -> str:
    """Return flag for result: H, L, normal, or critical.

    Uses medical critical thresholds from critical_alerts when available,
    falls back to 2x normal range for unknown tests.
    """
    if normal_low is None or normal_high is None:
        return "unknown"

    # Check critical thresholds from the medical database first
    if test_name:
        from ..services.critical_alerts import check_critical

        alert = check_critical(test_name, value)
        if alert:
            return "critical"

    if value < normal_low:
        # Check critically low (below 50% of normal_low for unknown tests)
        if normal_low > 0 and value <= normal_low * 0.5:
            return "critical"
        return "L"
    if value > normal_high:
        # Check critically high (above 2x normal_high for unknown tests)
        if value >= normal_high * 2:
            return "critical"
        return "H"
    return "normal"
