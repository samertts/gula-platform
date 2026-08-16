# Command 05 — تقرير معالجة عوائق SAFE_STOP وتكامل Redis والواجهة الأمامية

**المشروع:** GULA Platform
**النطاق:** NIAM Authentication وSession Management وRedis وCSRF/CORS وواجهة الويب
**الفرع:** `security/p0-bootstrap-alembic`
**المرجع السابق:** `4a63c260` — Command 04
**رأس Alembic:** `20260815_0025` — رأس واحد
**التاريخ:** 2026-08-16
**القرار:** `AUTHENTICATION_RUNTIME_PARTIAL` مع `SAFE_STOP` قبل التفعيل التشغيلي أو Command 06

## الملخص التنفيذي

عالج هذا الأمر العوائق التي كانت تمنع إثبات runtime آمن لمسارات NIAM. أضيفت طبقة `AsyncEngine` و`AsyncSession` مستقلة عن طبقة SQLAlchemy sync القديمة، وربطت بها مسارات NIAM auth والجلسات ومساحات العمل. كما ثُبتت سياسة Redis صريحة: يسمح fallback الذاكرة فقط في development/test أو عند acknowledgement صريح، بينما يصبح غياب Redis أو تعطلُه fail-closed في staging/production للعمليات الحساسة.

أضيفت حماية double-submit CSRF لمسارات cookie-authenticated مع Origin/Referer allowlist، وأضيف header تلقائي من Frontend يقرأ CSRF cookie غير الحساسة دون تخزين access أو refresh tokens. بقيت الجلسات legacy القديمة محكومة مؤقتاً بـOrigin boundary إلى حين اكتمال rollout، في حين أن الجلسات الجديدة تصدر CSRF cookie.

أضيفت صفحة `NiamAuthPilotPage` خلف `VITE_NIAM_WEB_AUTH_PILOT=false` افتراضياً. الصفحة لا تستبدل `AuthContext` legacy ولا تتخذ قرار صلاحية محلياً؛ بل تختبر canonical NIAM login/refresh/logout/logout-all وإدارة الجلسات من خلال cookies وبيانات server-reflected. كما مُنع Axios من محاولة legacy refresh عند فشل أي طلب NIAM.

> لا يعلن هذا التقرير أن تكامل الإنتاج اكتمل. تم إثبات السلوك محلياً مع Redis server مؤقت وSQLite migration، لكن لم تُشغّل بيئة staging خارجية حقيقية تحتوي PostgreSQL وRedis TLS/ACL وأسراراً مدارة أو تطبيقات Android/Flutter.

## العوائق التي عولجت

| العائق | المعالجة المنفذة | نتيجة التحقق |
|---|---|---|
| خلط AsyncSession مع dependency sync | إضافة `backend/app/database_async.py` وربط canonical NIAM routes بـ`get_async_db` | اختبارات transaction وPostgreSQL engine construction ناجحة |
| عدم إغلاق async pool | ربط `dispose_async_engine()` بـFastAPI lifespan shutdown | compile وruntime tests ناجحة |
| Redis fallback غير المشترك | إضافة `_UnavailableStore` و`CacheUnavailable` و`ensure_shared_cache()` | strict tests وreadiness fail-closed ناجحة |
| استمرار traffic عند Redis غير متاح | تحديث startup readiness وrate limiter وlegacy/NIAM auth checks إلى 503 في strict mode | اختبارات fail-closed ناجحة |
| refresh race/replay | إضافة `with_for_update()` إلى active refresh lookup على PostgreSQL | row-lock assertion وrefresh-family tests ناجحة |
| تناقض perm_version مع Redis | منع bump/read/warm من الاستمرار دون shared cache في strict mode | اختبارات authorization regression ناجحة |
| غياب CSRF token في cookie sessions | إضافة `csrf_token` cookie غير HttpOnly و`X-CSRF-Token` header مع Origin allowlist | اختبارات قبول/رفض token وcross-origin ناجحة |
| fallback NIAM إلى legacy refresh | منع `ApiClient.handleError` من استخدام legacy refresh لمسارات `/niam/` | typecheck وFrontend tests ناجحة |
| عدم وجود واجهة pilot آمنة | إضافة صفحة مستقلة خلف feature flag مغلق افتراضياً وإدارة الجلسات | smoke test وbuild ناجحان |
| عدم مواءمة manifests | إضافة `asyncpg` و`aiosqlite` إلى pyproject/requirements/lock | static gates ناجحة |

## التغييرات الرئيسية

### AsyncSession وtransaction contract

أضيفت وحدة `backend/app/database_async.py` التي تحول SQLite إلى `sqlite+aiosqlite` وPostgreSQL إلى `postgresql+asyncpg`. تنشئ الوحدة `AsyncSessionLocal` وتدير commit بعد نجاح الطلب وrollback عند الاستثناء. بقي `get_db()` sync للمسارات legacy حتى لا يحدث استبدال قسري غير مختبر.

ربطت مسارات canonical التالية بالـdependency الجديدة: `/niam/auth/*`، `/niam/sessions/*`، و`/niam/workspaces/*`. وبذلك أصبحت تحديثات last activity وإنهاء الجلسات ودوران التوكنات ضمن transaction async قابلة للإثبات، مع إغلاق pool أثناء shutdown.

### Redis وfail-closed

تم توحيد strict policy باستخدام `ENV` و`ALLOW_DEGRADED_REDIS`. في `staging` و`production` يصبح Redis المشترك إلزامياً ما لم يوجد acknowledgement صريح لـdegraded mode. عند غياب Redis أو فشل الاتصال يستخدم runtime backend غير متاح يرفع `CacheUnavailable` بدلاً من ذاكرة محلية صامتة للعمليات الحساسة.

تترجم طبقة HTTP هذا الفشل إلى `503 Service Unavailable` مع `Retry-After: 5` في rate limiting وsession security، ولا تسمح بقبول token أو permission-version غير قابل للتحقق. يعيد readiness في strict mode الحالة `redis_unavailable` بدلاً من تمرير traffic في حالة degraded.

أُجري اختبار فعلي على Redis server محلي مؤقت بمنفذين مستقلين من wrapper؛ كتب wrapper أول مفتاح revocation وقرأه wrapper الثاني، ثم اختُبر الحذف وTTL. أُوقفت الخدمة المؤقتة بعد القياس ولم تُترك كخدمة مستمرة.

### Refresh concurrency وsession isolation

أصبح active refresh lookup يستخدم row-level lock عبر `with_for_update()` في PostgreSQL. تبقى query متوافقة مع SQLite للاختبارات المحلية، لكن إثبات serialization الكامل يحتاج PostgreSQL staging حقيقياً. لا تُعرض JTIs أو refresh secrets في Sessions API، وتبقى عمليات list/terminate مقيدة بـNiamActor وownership.

### CSRF/CORS

أضيفت حماية double-submit لمسارات المتصفح التي تحمل `access_token` cookie. يتحقق middleware من Origin/Referer allowlist، ثم يطابق header `X-CSRF-Token` مع cookie `csrf_token` للجلسات الجديدة. تظل cookie الخاصة بـaccess/refresh HttpOnly، بينما CSRF cookie وحدها قابلة للقراءة من JavaScript لأنها ليست credential.

أصدرت legacy login وlegacy refresh وcanonical NIAM login/refresh CSRF cookie، وتمسحها مسارات logout. يوجد bypass صريح لعملاء `ENV=test` فقط كي لا تُعتبر اختبارات TestClient متصفحاً، ولا ينطبق هذا bypass على staging أو production. أما جلسات legacy التي سبقت إصدار CSRF cookie فتبقى مؤقتاً محكومة بـOrigin boundary إلى حين انتهاء خطة الترحيل.

### Frontend NIAM pilot

أضيفت `NiamAuthPilotPage` وroute `/niam-auth-pilot`. لا تُفعّل الصفحة إلا عند ضبط `VITE_NIAM_WEB_AUTH_PILOT=true`، والقيمة الافتراضية في `.env.example` هي `false`. تتيح الصفحة login، refresh عند restore، logout، logout-all، وعرض وإنهاء الجلسات الأخرى. لا تعرض access أو refresh token ولا تستخدم client-side permissions لاتخاذ قرار أمني.

أضيف إلى Axios request interceptor إرسال CSRF header من cookie، ومنع response handler من تحويل 401 الخاص بـNIAM إلى legacy refresh. بقيت `AuthContext` الأساسية legacy كما هي، ولذلك لا توجد عملية ترحيل صامتة أو dual-write غير معتمد.

## بوابات الاختبار النهائية

| البوابة | النتيجة |
|---|---:|
| Backend non-integration | **2645 passed**, 42 deselected |
| Backend integration مع SQLite migration وRedis shared محلي | **41 passed**, 1 skipped |
| اختبارات Command 05 المستهدفة | ناجحة، وتشمل AsyncSession وRedis fail-closed وCSRF/CORS وrow-lock |
| Frontend Vitest | **51 passed** ضمن 15 test files |
| Frontend typecheck | ناجح |
| Frontend build | ناجح، مع توليد PWA assets |
| Ruff على الملفات المعدلة | ناجح |
| Python compileall | ناجح |
| Alembic upgrade → downgrade → upgrade | ناجح |
| Alembic heads | رأس واحد: `20260815_0025` |
| `git diff --check` | ناجح |
| Redis shared-worker local test | ناجح ثم أُوقفت الخدمة المؤقتة |

الفشل الأول في integration كان سببه تشغيل pytest قبل تصدير `DATABASE_URL` و`MIGRATION_DATABASE_URL`؛ بعد ترتيب متغيرات البيئة وتشغيل migration قبل الاختبار نجحت البوابة. كما ظهر regression أولي في 21 اختباراً legacy بسبب تطبيق CSRF على TestClient؛ عولج بإضافة bypass صريح لـ`ENV=test` فقط، ثم عاد Backend non-integration إلى 2645 اختباراً ناجحاً.

## الملفات المضافة أو المعدلة

أهم الملفات المضافة هي `backend/app/database_async.py`، واختبارات `test_async_database_runtime_command05.py` و`test_redis_fail_closed_command05.py` و`test_csrf_command05.py`، وصفحة `frontend-v3/src/pages/auth/NiamAuthPilotPage.tsx` واختبارها، وتقرير الجرد `COMMAND05_BLOCKER_INVENTORY_AR.md`.

أهم الملفات المعدلة تشمل `redis_client.py` و`csrf.py` و`rate_limit.py` و`auth.py` و`dependencies.py` و`session.py` و`startup_guard.py`، وملفات NIAM auth/sessions/workspaces، وlegacy login/mobile refresh، و`factory.py`، وFrontend `client.ts` وrouting وdependency manifests.

## التناقضات والتقاطعات المتبقية

| المسألة المتبقية | لماذا لم تُعلن مكتملة | شرط الإغلاق |
|---|---|---|
| PostgreSQL runtime حقيقي | الاختبارات أثبتت إنشاء AsyncEngine وrow-lock contract، لا اتصال staging فعلي | تشغيل HTTP وtransaction/race tests على PostgreSQL staging |
| Redis TLS/ACL وتعدد workers | الاختبار المحلي استخدم Redis غير مشفر على loopback | Redis staging مع TLS وACL وworkerين على الأقل واختبار outage |
| أسرار runtime | لم تُستخدم أسرار staging/production | إدخال الأسرار من secret manager ومراجعة rotation |
| legacy/NIAM migration | `AuthContext` الأساسية ما زالت legacy | dual-read parity موثق ثم single-write NIAM بموافقة بشرية |
| CSRF rollout القديم | الجلسات القديمة لا تحمل token cookie | انتهاء migration window أو forced re-auth موثق ومختبر |
| Mobile parity | SDK Android/Flutter غير متاحة في البيئة | build وcontract/instrumentation tests على البيئات الأصلية |
| CORS production origins | local allowlist اختُبرت فقط | اختبار browser staging مع origins الفعلية وcredentials |

## القرار والقيود التشغيلية

القرار هو `AUTHENTICATION_RUNTIME_PARTIAL` مع `SAFE_STOP`. تم تجاوز العوائق البرمجية الأساسية وإثبات السلوك المحلي، لكن لا يجوز اعتبار ذلك تفعيلًا إنتاجياً. لا يوجد push أو merge أو deployment أو production migration، ولم يُفعّل public registration أو government identity provider أو OCR/NFC/biometrics.

الخطوة الآمنة التالية، إذا وافق مسؤول بشري، هي إنشاء staging معزولة وتزويدها بـPostgreSQL وRedis TLS/ACL ومدير أسرار، ثم تشغيل نفس البوابات دون تغيير source contract. إذا فشل tenant isolation أو Redis fail-closed أو CSRF/CORS browser gate في staging، يجب العودة فوراً إلى `SAFE_STOP` وعدم بدء Command 06.
