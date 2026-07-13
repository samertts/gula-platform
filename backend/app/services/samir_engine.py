"""
Samir Contextual Help Engine — GULA Platform
=============================================
Returns Arabic page-context tips for the in-app guide.

samir.py previously duplicated this with shorter strings and a different
function name (samir_help vs samir).  That file now delegates here.
"""

_TIPS: dict[str, str] = {
    "dashboard": "هذه لوحة التحكم في منصة GULA — تعرض ملخص نشاط المختبر وآخر الطلبات.",
    "worklist": "هنا تظهر العينات التي تحتاج إلى معالجة — يمكنك ترتيبها حسب الأولوية.",
    "results": "يمكنك مراجعة النتائج الطبية وإرسالها للمريض عبر واتساب أو رسالة نصية.",
    "identity": "يمكنك التحقق من الهوية الصحية للمريض ومطابقة الرقم الوطني.",
    "patients": "سجّل المرضى أو ابحث عن سجلاتهم السابقة في هذه الصفحة.",
    "orders": "أنشئ طلبات فحص جديدة أو تابع حالة الطلبات الحالية.",
    "qc": "تتبع نتائج ضبط الجودة وتنبيهات قواعد ويستغارد هنا.",
    "reports": "أنشئ وطبع تقارير PDF للنتائج الطبية من هذه الصفحة.",
    "settings": "اضبط إعدادات المختبر وإدارة المستخدمين من هنا.",
}

_DEFAULT = "مرحباً أنا سامر مرشدك في منصة GULA — كيف يمكنني مساعدتك؟"


def samir(page: str) -> str:
    """Return a contextual Arabic tip for the given UI page.

    Args:
        page: Page identifier (e.g. "dashboard", "results").

    Returns:
        Arabic help string.  Returns a generic greeting for unknown pages.
    """
    if not page or not isinstance(page, str):
        return _DEFAULT
    return _TIPS.get(page.strip().lower(), _DEFAULT)


# Backward-compat alias used by samir.py
samir_help = samir
