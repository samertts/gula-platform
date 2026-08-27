# Appointment Vertical Slice 01B / Slice 02 Baseline

**التاريخ:** 2026-08-27 19:21 UTC
**الفرع:** `feat/citizen-journey-20260827`
**HEAD قبل التعديل:** `3e9f952b6743927885bd2add683bbc35d5cd3d32`

## Baseline evidence

كانت الشجرة نظيفة قبل التعديل، وكان focused suite الخاص بالعقود وAppointment وSynthetic backend وInventory وmigration chain يحقق **27 passed و1 skipped و1 warning خلال 42.99 ثانية**. الاختبار المتجاوز هو PostgreSQL migration gate بسبب غياب `MIGRATION_DATABASE_URL` أو قاعدة PostgreSQL مصرح بها.

| المجال | baseline |
|---|---|
| Appointment API | موجود ومثبت محلياً |
| Identity/Session/Workspace | NIAM القائم، مع contextual authorization |
| PostgreSQL disposable محلياً | غير متوفر؛ Docker غير مثبت في sandbox |
| PostgreSQL CI pattern | موجود في `.github/workflows/iam-hardening.yml` |
| Encounter canonical API | غير موجود قبل هذه الموجة؛ الموجود legacy/placeholder |
| Clinical Note canonical API | غير موجود قبل هذه الموجة؛ الموجود EHR legacy flags |
| national_facilities drift | duplicate ORM owner بين metadata منفصلة |
| Frontend Live writes | غير مفتوحة |
| Production/staging proof | غير مثبت |

## Baseline risks

كان الخطر الرئيسي هو تحويل Appointment المحلي إلى ادعاء production proof دون PostgreSQL فعلي متعدد الاتصالات. كما كان duplicate `national_facilities` يهدد بتضارب ownership وmigration وauthorization. أما Encounter وClinical Note فكانت لديهما نماذج legacy أو commands placeholder لا تضمن contextual authorization وstate machine وidempotency وversioned audit.

## Measurement boundary

لم يُجرَ في baseline benchmark p50/p95/p99، ولا قياس DB query count أو N+1 أو memory/CPU production-like. لذلك لا توجد أرقام أداء يمكن استخدامها كقبول release. تبقى هذه القياسات مرحلة لاحقة بعد تشغيل PostgreSQL وRedis/worker environment معزولة.

## Evidence classification

هذا الملف يسجل **LOCAL BASELINE** فقط. لا يمثل `PRODUCTION-LIKE PROOF` ولا `PRODUCTION PROOF`، ولا يسمح وحده بفتح Live writes أو تغيير `golden_path_passed` أو `production_ready`.
