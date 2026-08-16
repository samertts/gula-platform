# Command 05 — جرد عوائق SAFE_STOP والتقاطعات

## Baseline

الفرع الحالي هو `security/p0-bootstrap-alembic`، والـHEAD قبل Command 05 هو `4a63c260`، مع رأس Alembic واحد هو `20260815_0025`. الهدف التشغيلي لهذا الأمر هو إثبات runtime على staging محلي فقط، وليس تشغيل production أو تفعيل أي تكامل حكومي.

## العوائق المثبتة

| العائق | الدليل | الأثر | المعالجة المخططة |
|---|---|---|---|
| عدم وجود AsyncEngine/async_sessionmaker في `app/database.py` | `get_db()` ينشئ SQLAlchemy sync `SessionLocal` | مسارات NIAM async ليست runtime-proven | إضافة dependency async منفصلة لا تستبدل legacy، مع driver SQLite/PostgreSQL مناسب للبيئة |
| Redis يملك in-memory fallback | `redis_client._build_cache()` يعيد `_MemoryStore` عند الغياب/الفشل | revocation وrate limits غير مشتركة بين workers | fail-closed للعمليات الحساسة، health/readiness صريح، واختبارات Redis adapter |
| تناقض readiness/runtime | `startup_guard.is_system_ready()` يعيد `degraded_redis` ويمرر traffic بعد فشل Redis | قد يستمر logout/revocation بشكل غير آمن | فصل العمليات التي تحتاج Redis عن العمليات غير الحساسة، ورفض auth mutations الحساسة عند فقد Redis |
| `check_redis()` يعتمد `REDIS_URL` حتى عند غيابه | startup policy تختلف عن runtime cache construction | سلوك غير موحد بين test/dev/staging | توحيد policy مع explicit degraded mode للتطوير فقط |
| لا يوجد NIAM web rollout flag | `AuthContext` يستعمل legacy `/login`, `/session`, `/logout` | استبدال auth مباشرة يكسر clinical routes | feature flag staging-only وdual-read دون fallback امتيازي |
| legacy/NIAM identity mapping غير معتمد | `UserInfo` مختلف عن `Account/Identity/Membership` | لا يمكن نقل الواجهة بأمان | عقد mapping read-only واختبارات parity قبل single-write |
| CSRF موجود origin-boundary فقط | `CSRFMiddleware` يتحقق من Origin/Referer ولا يملك token مستقل | الحماية تعتمد على browser headers وCORS | إبقاء origin allowlist صارماً وإضافة contract tests؛ عدم فتح wildcard/credentials |
| canonical Session API غير مثبت HTTP | service async لكن dependency العامة sync | لا يمكن إعلان COMPLETE | اختبار staging HTTP بعد async dependency |
| Android/Flutter SDK غير متاحة | لا يمكن تشغيل build/instrumentation محلياً | parity غير مثبتة | توثيق blocker وعدم ادعاء النجاح |

## التقاطعات الخطرة

توجد ثلاثة تقاطعات يجب ألا تُحل بحلول fallback: legacy logout global `perm_version` مقابل NIAM current/all-session semantics، Redis revocation مقابل in-memory fallback، وFrontend membership reflection مقابل authorization server-side. أي تعديل يخلط هذه الطبقات سيُرفض حتى لو نجحت اختبارات الوحدة.

## قواعد التنفيذ

لا push ولا merge ولا production deployment ولا production migration. لا تفعيل public registration أو government identity أو OCR/NFC/biometrics. كل migration تُختبر على SQLite/PostgreSQL staging clone فقط. فشل Redis fail-closed أو tenant isolation يعيد القرار فوراً إلى `SAFE_STOP`.
