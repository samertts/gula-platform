# دليل تحويل UTC في metadata لـDocument Intelligence

**الفرع:** `fix/document-intelligence-utc-metadata`
**التزام التنفيذ:** `1c7b8f475fa658de6911881f4dda60b250ae2829`
**الحالة:** خفضت الدفعة تحذيرات محددة في metadata غير المخزنة؛ لا تغير قرار الإطلاق، ولا تعالج كل دين التواريخ.

## النطاق المنفذ

استبدلت هذه الدفعة خمسة استعمالات `datetime.utcnow().isoformat()` في وحدتي `observability.py` و`security.py` بـ`datetime.now(UTC).isoformat()`. تنتج الآن صحة الخدمة والسجل المنظم والتنبيهات وسجل التدقيق داخل الذاكرة وسجل integrity طابع ISO 8601 يحمل UTC offset صريحاً.

| الوحدة | الاستعمالات المعدلة | طبيعة البيانات |
|---|---:|---|
| `observability.py` | 3 | health/log/alert metadata غير مخزنة في قاعدة بيانات. |
| `security.py` | 2 | audit/integrity metadata داخلية في الذاكرة. |

## الاستبعادات المتعمدة

لم تلمس الدفعة `domain/entities.py` أو `infrastructure/repository.py` أو `infrastructure/services.py` أو `backup_dr.py`. تحتوي هذه المسارات طوابع تُسند إلى كيانات أو استعلامات أو نسخ احتياطية أو أعمال احتفاظ، وقد يتطلب تحويلها مراجعة schema وtimezone وmigration وrestore منفصلة. لم يجر تعديل حذف أو retention أو archive أو scheduler.

## التحقق

| التحقق | النتيجة |
|---|---|
| اختبارات UTC الجديدة | تثبت UTC offset في health/alert/audit/integrity وأن integrity chain ما زالت صحيحة. |
| `tests/test_document_intelligence.py` مع الاختبارات الجديدة | 68 ناجحاً؛ بقيت 63 تحذيراً من مسارات خارج هذا النطاق. |
| Ruff | ناجح للملفين والاختبار الجديد. |
| MyPy للاختبار الجديد | ناجح. |
| بوابة changed-files مقابل RC1 | **PASS**: Ruff `0→0` وMyPy `38→38` للملفات المتغيرة؛ الدين الحرج لم يتغير. |

لا تنسب التحذيرات المتبقية إلى هذه الدفعة ولا تخفها. يجب أن يعالج كل تحويل لاحق بوصفه دفعة منفصلة تتضمن أثر التخزين والتوافق وtest evidence.
