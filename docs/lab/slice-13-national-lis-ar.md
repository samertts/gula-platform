# Slice 13 — National LIS/Lab Core Remediation

## الملكية والحدود

يعيد التنفيذ استخدام `CoreLabOrder` و`CoreSpecimen` و`CoreLabResult` و`CoreCriticalResultEvent` كمالكين canonical. أضيفت فقط catalog versions وanalyzer registry وmessage metadata/hash وQC records. لا يُحفظ raw analyzer payload ولا تُكتب نتيجة سريرية مباشرة من adapter.

يوجد `AnalyzerAdapter` protocol و`SyntheticAnalyzerAdapter` فقط. لا توجد ASTM/HL7/FHIR live connection أو PACS/LIS/RIS/HIS integration. الرسائل الاصطناعية محكومة بـpayload hash وmessage time window وnonce/idempotency، وتُرفض الأجهزة غير `ACTIVE` أو غير المطابقة للمختبر والعينة.

## سلامة النتائج

لا يمكن release لنتيجة provenance من `ANALYZER` أو `IMPORTED_SYNTHETIC` قبل وجود QC `PASS` أو `OVERRIDDEN` مصرح به. تصحيح النتيجة النهائية يتم عبر amendment/version canonical بدلاً من تعديل القيمة المنشورة. QC وanalyzer transitions تستخدم authorization وIf-Match وrow locks وaudit.

## أدلة قابلة لإعادة التشغيل

| الدليل | النتيجة |
|---|---|
| `tests/test_lis_advanced_api.py` | اختبار ناجح لمسار analyzer state، mapping/quarantine، message replay/conflict، catalog versioning وQC gate/If-Match |
| `tests/test_core_lab_result_access_api.py` | 5 اختبارات ناجحة بعد ربط QC بالعقد الجديد |
| PostgreSQL 16 disposable | migration 0018 طُبقت ضمن upgrade إلى head وrollback/re-upgrade نجح |
| quality | compileall وRuff للملفات المعدلة ناجحان |

## الحدود المتبقية

لا توجد أجهزة أو مختبرات وطنية حقيقية متصلة، ولا notification delivery خارجي. أي critical notification يجب أن يبقى internal/synthetic intent إلى أن توجد بوابة معتمدة وسياسة تشغيلية مستقلة. لا تكفي هذه الأدلة لإعلان production readiness أو interoperability readiness.
