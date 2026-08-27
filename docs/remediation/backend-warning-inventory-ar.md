# Backend Warning Inventory — Vertical Slice 01B/02

**المصدر:** full backend suite على الشجرة الحالية
**النتيجة:** `2794 passed, 5 skipped, 165 warnings in 309.26s`، `exit code=0`
**السياسة:** التحذير ليس blocker تلقائياً، لكن لا يبقى مجهول السبب.

| التصنيف | الدليل الحالي | القرار |
|---|---|---|
| Legacy application | استعمالات `datetime.utcnow()` في document intelligence وfinancial/pricing paths القديمة، إضافة إلى default datetime في نماذج قديمة | لا تُخلط في Slice 02؛ تُسجل لموجة UTC modernization مع tests regression |
| Third-party deprecation | `StarletteDeprecationWarning` بسبب توافق `httpx`/`starlette`، وتحذير Sentry لرمز HTTP 422 القديم | تحديث dependency/API في موجة compatibility منفصلة بعد مراجعة lockfile وCI |
| SQLAlchemy/Python deprecation | datetime adapter وserver/default wrappers في schema paths القديمة | تحديث تدريجي إلى timezone-aware datetimes مع PostgreSQL/SQLite regression |
| Test-only security warning | `joserfc` يحذر من test key أقل من 112 bits في `test_security_regression.py` | رفع test fixture key إلى حجم آمن في موجة test-hardening؛ لا يعني تسرب secret production |
| Known volume warnings | 40 في `test_financial_phase_b.py`، 30 في `test_pricing_service.py`، 18 في `test_idempotency.py` ناتجة عن defaults/adapter legacy | لا يتم إسكاتها؛ تُقسم إلى owners وتُراقب حتى الإصلاح |
| Slice 02 changed code | لا توجد warnings جديدة مرتبطة بـ`backend/app/clinical/encounters` في run الحالي | لا توجد معالجة إضافية مطلوبة داخل هذه الموجة |

## ما تم إصلاحه الآن

تم الحفاظ على تحذيرات full suite كما هي وعدم استخدام `filterwarnings` لإخفائها. أُصلحت فقط مشاكل lint/compile وfixture/flush وstate contract التي ظهرت بسبب التوسعة الحالية. عدد التحذيرات بقي دليلاً مرئياً على backlog وليس علامة على فشل الاختبارات.

## شرط الإغلاق

يُغلق هذا السجل فقط بعد ربط كل تحذير بمسار وowner واختبار regression، ثم تحديث dependency أو الكود بصورة تدريجية. لا يُسمح بإعلان صفر تحذيرات عبر suppression شامل، ولا يُستخدم هذا السجل لإعلان production readiness.
