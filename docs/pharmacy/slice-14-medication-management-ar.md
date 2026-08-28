# Slice 14 — Pharmacy وMedication Management

## الملكية والضوابط

يعتمد التنفيذ على `MedicationCatalog` و`Prescription` و`MedicationBatch` و`Dispense` و`CoreMedicationStockLedger` canonical، ولا ينشئ نظام وصفة أو eMAR ثانياً. dispensing لا يساوي administration؛ مالك eMAR المستشفى مستقل. كما أن التأمين والدفع لا يوقفان الرعاية الطارئة.

يحافظ catalog على `is_controlled` ولا يمحوه عند الموافقة. approval أصبح حالة ودليلًا منفصلين (`APPROVED_BY_POLICY` مع approver وtime وreason/evidence)، مع فصل مهام policy signer عن المنشئ/الصارف. تستخدم عمليات recall وstock adjustment If-Match وrow locks وidempotency. يسجل recall حدثاً append-only مرتبطاً بالـbatch canonical، ويمنع batch recalled أو expired أو quarantined من التحضير.

يختار FEFO أقرب expiry ضمن الصفوف المقفلة، ويمنع negative stock وover-dispense. تصحيحات المخزون لا تعدل السجل التاريخي بل تنشئ ledger reversal/adjustment جديداً.

## أدلة قابلة لإعادة التشغيل

| الدليل | النتيجة |
|---|---|
| `tests/test_pharmacy_safety_extensions.py` | اختبار ناجح لـpolicy SoD، FEFO، recall quarantine/event، If-Match وledger waste |
| `tests/test_core_pharmacy_api.py` | اختبارا regression ناجحان للـcanonical pharmacy |
| PostgreSQL 16 disposable | migration 0019 طبقت recall event وFKs وchecks وrollback/re-upgrade نجح |
| quality | compileall وRuff للملفات المعدلة و`git diff --check` ناجحة |

## الحدود المتبقية

لا توجد صيدليات أو مرضى حقيقيون أو provider خارجيون. لم تُثبت بعد منافسة آخر مخزون عبر PostgreSQL probe مخصص ولا full backend suite بعد آخر تغييرات. لذلك تبقى `production_ready=false`، ويجب إكمال security/concurrency evidence وremote CI/staging قبل أي تشغيل فعلي.
