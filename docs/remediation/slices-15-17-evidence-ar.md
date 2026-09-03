# أدلة Slices 15–17 — الأشعة، المستشفى، والطوارئ

## النطاق المنفذ والقائم

كان المستودع يحتوي مسبقاً على canonical domains للأشعة والتصوير، المستشفى والرعاية الداخلية، والطوارئ والإسعاف. تم تدقيقها بدلاً من إنشاء مالكين ثانويين. تشمل هذه المجالات نماذج ومسارات ومigrations واختبارات للطلبات والدراسات والتقارير، الأسرة والقبول والتمريض وeMAR، والحوادث والفرز والإرسال والتسليم وePCR.

أضيف في هذه الموجة مسار **Emergency Break-Glass** canonical مستقل عن الدور الوظيفي، مع طلب مسبب ومحدد المريض ونطاق الموارد ومدة لا تتجاوز 60 دقيقة. يتبع المسار `REQUESTED → ACTIVE → EXPIRED/REVOKED`، ويستخدم authorization وIdempotency-Key وIf-Match وrow lock وaudit append-only. لا يوجد وصول شامل للنظام ولا صلاحية دائمة.

## إثبات الاختبارات

| الدليل | النتيجة |
|---|---|
| Radiology/Hospital/Emergency/read gates/ICU/OR/tenant tests | **65 اختباراً ناجحاً، تحذير واحد** |
| Break-Glass lifecycle | request، activation، stale If-Match rejection، revoke ناجحة |
| Contract registry | عقد `emergency-break-glass` وانتقالاته مثبتة |
| compile/Ruff | ناجحان على الملفات المعدلة |
| PostgreSQL 16 disposable | upgrade إلى `20260828_0020`، downgrade إلى `0019`، ثم re-upgrade ناجح |
| schema gate | `core_emergency_break_glass` و`core_emergency_break_glass_events` موجودان |

## حدود صادقة

المرفق الخاص بـSlice 16 ينتهي عند السطر 1372 وسط بند الأمن، والمرفق الخاص بـSlice 17 ينتهي عند السطر 1306 وسط بند conflict؛ لذلك لا يمكن الادعاء بأن محتوى غير موجود قد نُفذ. كما لم تتم إضافة واجهات Frontend أو Mobile أو Desktop في هذه الموجة لأن المطلوب الآمن كان تثبيت backend/domain evidence أولاً، ولا توجد أجهزة أو GPS أو DICOM/PACS أو EMS providers حية.

تبقى القيم `production_ready=false` و`golden_path_passed=false` حتى تكتمل مراجعة المتطلبات الناقصة، full suite بعد هذه التغييرات، اختبارات التزامن الخاصة بموارد المستشفى/الدم، وتحقق CI/staging مستقل.

> لا يُستخدم Break-Glass لتجاوز التدقيق أو منح all-system access؛ هو تفويض استثنائي مؤقت ومقيد بالمريض والموارد والغرض والمدة.
