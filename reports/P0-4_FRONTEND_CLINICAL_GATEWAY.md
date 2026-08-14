# P0-4 — frontend-v3 Canonical Clinical Gateway Adapter

## الربط

يستخدم frontend-v3 المسارين versioned `/api/v1/clinical/patients` و`/api/v1/clinical/orders` فقط. أضيفت المسارات إلى GET allowlist الضيقة في API client، ولم تُفتح أي قراءة عامة أو legacy path. القرار النهائي للـrollout والتفويض يبقى في backend؛ المتصفح لا يقرر capability أو workspace.

## typed response

يتحقق adapter من `contract_version=1.0`، و`request_id`، و`correlation_id`، وworkspace context، وpagination، ثم يحول إلى `ClinicalPatientRead` و`ClinicalOrderRead`. لا ينشئ قيمًا افتراضية لـ`lab_id` أو phone أو patient IDs، ولا يعرض أعمدة غير موجودة في العقد.

Patient page تعرض display name والجنس وتاريخ الميلاد فقط. Orders page تعرض order ID وpatient/practitioner display names والحالة وعدد الفحوصات وتاريخ الإنشاء. لا يعاد إظهار national identifiers أو phone أو results عبر view-model مزيف.

## fail-closed

إذا أعاد الخادم `401` أو `403` أو `503` يحول adapter الحالة إلى blocked UI state دون retry صامت أو fallback إلى `/patients` أو `/orders`. وإذا خالف response العقد أو احتوى حقولًا legacy حساسة، يرفضه adapter بـ`invalid_response`.

يبقى `DIRECT_REST_SCOPED_READS_BLOCKED=true` كضابط صريح يثبت أن المسارات القديمة محجوبة، بينما canonical path هو الاستثناء الوحيد المسموح في allowlist.

## الاختبارات

تشمل Vitest التحقق من path، version، workspace context، رفض الحقول الحساسة، minimal order DTO، وعدم وجود fallback. نجحت اختبارات frontend-v3 والـtypecheck والlint بعد التغيير.

## الحدود

هذا الربط لا يفعّل gateway بذاته؛ default server rollout هو `OFF`. ويحتاج أي تشغيل داخلي أو تجريبي إلى إعدادات backend وreviewed mappings وpermissions assignments المعتمدة، ثم مراجعة بشرية منفصلة.
