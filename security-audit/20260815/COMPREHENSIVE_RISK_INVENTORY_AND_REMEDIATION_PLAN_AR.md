# GULA Platform — الجرد الشامل للمخاطر وخطة الإصلاح والمعالجة

**المشروع:** GULA Platform

**نطاق التدقيق:** Backend، NIAM، المصادقة والجلسات، RBAC والعزل، Redis وAsyncSession، CSRF/CORS، الواجهات، AI، البيانات الصحية، التكاملات، الحوكمة، CI/staging، Android وFlutter، migrations، التشغيل والمراقبة.

**الفرع:** `security/p0-bootstrap-alembic`

**HEAD عند الجرد:** `0db96cc2 fix(identity): close command 05 boundary blockers`

**working tree عند بداية الجرد:** نظيف. أُنشئت خلال التدقيق ملفات تقارير فقط، ولم تُعدّل ملفات source أو database أو deployment.

**Alembic:** رأس واحد `20260815_0025`.

**القرار الحالي:** `AUTHENTICATION_RUNTIME_PARTIAL` مع `SAFE_STOP`.

> هذا الجرد static/contract audit مدعوم بقراءة source وتشغيل بوابات محلية. لا يُعد Pentest خارجياً، ولا يثبت سلامة PostgreSQL/Redis staging أو المتصفحات أو Android/Flutter. أي بند مصنف “يتطلب staging” يبقى مفتوحاً حتى تُنتج بيئة معزولة دليلاً قابلاً لإعادة التشغيل.

## 1. ملخص تنفيذي

أظهر الجرد أن الإصلاحات السابقة حسّنت NIAM وrefresh rotation وRedis fail-closed محلياً، لكن توجد **مخاطر مركبة** ناتجة عن تداخل طبقات مستقلة: middleware وCORS/CSRF، readiness وstartup، legacy وNIAM، generic authentication وAI/health-data، وcoarse admin permissions مع التكاملات الديناميكية.

أعلى المخاطر ليست في فشل اختبار الوحدة؛ فالاختبارات الحالية ناجحة، لكن بعض المسارات الحساسة تعتمد على تفويض عام أو endpoints عامة أو fallbacks يمكن أن تعيد نجاحاً وهمياً. لذلك لا يجوز إعلان اكتمال المصادقة أو تفعيل التكاملات الحكومية أو التحصيل أو التسجيل العام قبل إغلاق بنود P0 وإثباتها في staging.

| المؤشر | النتيجة الحالية |
|---|---:|
| Backend non-integration | **2649 passed**, 42 deselected، و252 warning |
| Frontend Vitest | **51 passed** ضمن 15 ملف اختبار |
| Frontend typecheck/build | ناجحان |
| Alembic | `20260815_0025`، رأس واحد |
| Flutter/ADB محلياً | غير متاحان في البيئة الحالية |
| Redis staging بعد الفحص | متوقف؛ لا توجد خدمة خلفية مستمرة |
| production/staging deployment | لم يُنفذ |
| push/merge | لم يُنفذ |

## 2. سجل المخاطر والعوائق الكامل

### 2.1 أولويات P0 — يجب إغلاقها قبل أي تفعيل تشغيلي

| المعرّف | المشكلة أو الثغرة أو التناقض | الدليل الحالي | الأثر المحتمل | شرط الإغلاق |
|---|---|---|---|---|
| P0-01 | **حالة partial readiness قد تقبل traffic قبل اكتمال الاعتمادات.** | `startup_guard.py` يصف `partial_startup_timeout`، و`factory.py` يسمح بـ`NON_BLOCKING_STARTUP=true` في production/staging. | قبول طلبات أثناء عدم اكتمال DB/Redis/kernel أو اختلاف liveness عن readiness. | جعل `system_ready` لا يصبح true بعد timeout، وإرجاع 503 لكل المسارات غير probe حتى تكتمل DB وRedis وmigrations وasync engine؛ اختبار timeout/race على staging. |
| P0-02 | **تعارض CSRF مع CORS.** | Frontend يرسل `X-CSRF-Token`، لكن `factory.py` لا يضمنه إلى `allow_headers`. | فشل preflight أو تعطّل login/refresh/logout عبر origin منفصل؛ احتمال دفع التشغيل لتعطيل CSRF. | إضافة header إلى allowlist، اختبار browser حقيقي مع credentials، واختبار رفض origin/header غير المطابق. |
| P0-03 | **refresh cookie قد لا يدخل شرط CSRF عند غياب access cookie.** | middleware يتحقق من CSRF عند وجود `access_token`، بينما refresh يستخدم `refresh_token` أيضاً. | تدوير refresh عبر cross-site أو اختلاف contract بين الجلسات الجديدة والقديمة. | اعتبار كل mutation تحمل refresh cookie cookie-authenticated، وفرض double-submit على refresh/logout/rotate، مع اختبار access منتهٍ وrefresh صالح. |
| P0-04 | **Redis degraded fallback قابل للتفعيل في staging/production.** | `ALLOW_DEGRADED_REDIS=true` يسمح بالـmemory store رغم أن revocation/rate-limit مشتركان. | replay بعد logout، rate-limit مختلف بين workers، وعدم اتساق session security. | منع fallback في production وstaging منعاً قاطعاً، أو جعله emergency mode بتوقيع تشغيل وانتهاء زمني ورفض كل auth-sensitive traffic؛ اختبار Redis outage متعدد العمال. |
| P0-05 | **عمليات kernel/runtime الحساسة محمية بـgeneric authentication فقط.** | `/kernel/runtime` يعتمد `get_current_user` حتى لـoptimize وvalidation/run وAI infer وpolicies. | أي حساب مصادق قد يطلق عمليات تشغيلية أو AI أو يقرأ metrics داخلية. | إضافة permissions منفصلة مثل `runtime:read`, `runtime:operate`, `ai:infer` وworkspace/tenant scope، ثم اختبارات deny-by-default وcross-tenant. |
| P0-06 | **AI Fabric السريري يعتمد على auth عام دون purpose/role/tenant scope.** | router يضع `get_current_user`، بينما chat/embed/RAG/clinical/lab/public-health endpoints بلا permission إضافية. | إرسال أو تحليل PHI من حساب عام، أو استخدام قدرات AI خارج مساحة العمل. | فصل public/non-clinical عن clinical AI، فرض role + workspace + purpose + audit، تحديد limits، ومنع تمرير patient data خارج policy. |
| P0-07 | **رابط نتائج AI العام bearer-token سريري.** | `/api/ai/interpret/{token}` يقرأ نتائج مختبر وسياقاً محدوداً، مع cache محلي وتسجيل token prefix. | تسريب PHI، linkability عبر logs، اختلاف بين workers، صعوبة الإبطال والـenumeration. | استخدام token hash غير قابل للعكس في التخزين، TTL قصير، one-time أو revocable link، shared durable store، عدم تسجيل token أو prefix، rate-limit ومراجعة response minimization. |
| P0-08 | **التكاملات الديناميكية قابلة لإعادة success وهمي.** | MQTT/AMQP يعيدان `True` من `_simulated_publish` عند غياب المكتبة، وTLS يسمح `verify=false`/`CERT_NONE`. | إيصال مالي/إشعار/رسالة يظهر ناجحاً دون تسليم، أو اتصال غير موثوق. | fail-closed في staging/production، منع simulated success، جعل missing dependency فشلاً واضحاً، منع `CERT_NONE` خارج test، وإضافة delivery receipt/idempotency/audit. |
| P0-09 | **سطح ecosystem عالي الأثر تحت permission واحدة.** | system:admin يستطيع register/send/receive connectors وissue API keys؛ responses تعيد `api_key` وaudit details/IP. | outbound abuse، credential exposure، SSRF/egress، وتضخم blast radius. | فصل `integration:register`, `integration:send`, `credential:issue`, `audit:read`، allowlist للوجهات، SSRF protection، عدم إعادة المفتاح إلا مرة واحدة، redaction واختبارات egress. |
| P0-10 | **قراءات/كتابات governance حساسة بلا boundary واضح.** | get health-number/history، worker/node reads وبعض training/competency/productivity/audit-events بلا dependency محلية في `governance_routes.py`. | كشف هوية حكومية وبيانات موظفين أو تعديل سجلات خارج المؤسسة/الوحدة الإدارية. | route-level effective dependency + ownership/workspace scope + field minimization، واختبارات anonymous/cross-organization/role matrix. |
| P0-11 | **مسارات certification الإدارية مكشوفة بلا auth.** | `/certification` بلا router dependency، وتشمل evaluate/report/release/check/validate. | reconnaissance، تشغيل فحوصات ثقيلة، كشف تفاصيل source/release أو DoS. | جعلها internal/admin-only، rate-limit، عدم تشغيل file/system scans من HTTP العام، وإثبات deny-by-default. |
| P0-12 | **تسرب محتمل من nested router composition.** | document-intelligence routers للـobservability/access/semantic/lifecycle تُنشأ بلا dependency ثم تُضمّن إلى router إداري؛ الحماية تعتمد على inheritance غير صريح. | grant/revoke/access-check أو semantic/lifecycle data قد لا تكون محمية كما يتوقع التصميم. | بناء app فعلياً وفحص effective dependencies لكل route، ثم وضع dependency صريحة على كل nested router واختبارها. |
| P0-13 | **single-write/registration lifecycle غير قابل للتفعيل بأمان.** | provider الرسمي غير متصل، وAuthContext الأساسي legacy، والتسجيل العام مغلق. | ضغط تشغيلي لتفعيل bypass أو إنشاء حسابات بحالات معلقة؛ كسر lifecycle أو ازدواج هوية. | إبقاء public registration/provider integrations مغلقة، cohort parity اصطناعي، مراجعة بشرية، rollback، ثم NIAM single-write فقط بعد كل P0. |

### 2.2 أولويات P1 — يجب إغلاقها قبل release حكومي أو توسيع الاستخدام

| المعرّف | المجال | المشكلة | الأثر | المعالجة المطلوبة |
|---|---|---|---|---|
| P1-01 | Health diagnostics | `/health/status`, `/health/deep`, `/health/kernel` عامة ضمن allowlist؛ deep يعرض queue/memory/circuits/auto-repair وkernel يعيد exception string. | reconnaissance وتسريب أخطاء وتشخيص داخلي. | إبقاء `/health/live` minimal public، جعل readiness داخلياً أو network-restricted، حذف exception strings، فصل deep-authenticated. |
| P1-02 | Staging gate | workflow لا يختبر إلا health/ready/deep. | لا يثبت CSRF/CORS/tenant/replay/Redis TLS/authz/mobile. | إضافة browser security، PostgreSQL race، Redis TLS/ACL/outage، tenant matrix، synthetic clinical data، وrollback check. |
| P1-03 | Legacy/NIAM drift | AuthContext المنشور يستخدم legacy session/login/logout وmembership reflection؛ NIAM pilot مغلق افتراضياً. | إصلاح غير مستخدم في التطبيق الأساسي وتناقض refresh/logout/permissions. | dual-read parity، feature-flagged cutover، telemetry، forced re-auth window عند الحاجة، ثم إزالة fallback بعد human approval. |
| P1-04 | Docs authentication | DocsAuth يتحقق من legacy JWT role `admin/master_admin` فقط. | NIAM admin مصرح قد يُرفض، أو legacy role قد يفتح docs دون governance context. | اعتماد NIAM server-side governance context، أو عقد انتقال صريح مع deny-by-default. |
| P1-05 | Financial engine | routes تعتمد get_current_user وlab scope، بينما read/write/billing/pricing تحت module واحد؛ flag مغلق افتراضياً. | عند التفعيل قد يغيب فصل ticket/cashier/reconcile/refund/finance roles. | permissions منفصلة، shift ownership، idempotency، reconciliation، cash/electronic segregation، واختبارات عدم قدرة الطبيب/المختبر على التحصيل. |
| P1-06 | Health-data admin breadth | `system:admin` الواحد يصل إلى raw event store وtenant_id وmetadata وwarehouse/ingestion/canonical mapping. | least privilege غير كافٍ وتسريب عابر للمؤسسات. | scopes للقراءة/الإدخال/warehouse/lineage، tenant/workspace filters server-side، redaction، access audit. |
| P1-07 | AI provider discovery | `/api/ai/operations` و/providers عامة وتعرض provider/fallback/base URL/configuration. | reconnaissance ومعلومات بنية وتكاليف. | auth أو response minimization، وعدم إعادة URLs أو fallback chain خارج admin/ops. |
| P1-08 | Data storage durability | `LocalStorageBackend` الافتراضي يستخدم `/tmp`، وعدد من stores/caches module-level. | فقد بيانات عند restart، اختلاف multi-worker، وعدم إثبات encryption/durability. | S3/object storage مشفر أو volume موثق، DB-backed event/policy state، tenant prefix، key management، backup/restore test. |
| P1-09 | Connector transport defaults | defaults داخلية HTTP لـntfy/Ollama/vLLM/PACS/search services، وخيار TLS verification configurable. | misconfiguration قد يخرج traffic غير مشفر أو يضع credentials على endpoint غير موثوق. | production allowlist للـscheme/host، منع HTTP الخارجي، TLS verification immutable، egress policy. |
| P1-10 | Governance/health-number reads | عقد parity read-only لا يحمي وحده كل governance routes العامة أو legacy routes. | mapping آمن لا يمنع endpoint آخر من كشف السجل. | catalog موحد للـPII/PHI endpoint، scope tests، field minimization، DLP/log redaction. |
| P1-11 | Broad route registration | factory يضم عشرات domains في app واحد مع legacy/NIAM/auth models مختلفة. | attack surface كبير وتعارض middleware/contracts وصعوبة إثبات deny-by-default. | route inventory generated from built app، classification public/auth/permission/admin/internal، ownership لكل module، ومنع route غير مصنف في CI. |
| P1-12 | Audit/PII retention | token prefix وIP وdetails قد تدخل logs/audit/responses في AI/ecosystem/health-data. | ارتفاع أثر تسريب السجلات وصعوبة طلبات الحذف/الاحتفاظ. | redaction policy مركزية، structured allowlist، retention/crypto-at-rest، واختبار no-secret/no-token/no-PHI logs. |
| P1-13 | Mobile parity | Flutter وADB غير متاحين محلياً؛ CI workflows موجودة لكن لا تثبت runtime/offline/SQLCipher في هذه البيئة. | لا يمكن إعلان parity أو سلامة offline-first/reader/WCAG. | تشغيل CI instrumented وعلى SDK الأصلية، contract tests، SQLCipher migration/restore/conflict tests، TalkBack/Orca evidence. |
| P1-14 | Public contract/certification exposure | contracts وmetadata قد تكون مقصودة، لكن contract generation وcertification العامة تحتاج policy واضحة. | reconnaissance أو resource exhaustion. | public allowlist موثق، rate limits، caching آمن، وإخراج لا يحتوي internal routes/secrets. |
| P1-15 | Readiness model | DB/Redis/migrations/kernel/async engine لها lifecycles مختلفة لكن readiness يمثلها بعلم واحد. | false positive/negative وصعوبة تشخيص السبب. | readiness component schema منفصل، reason codes ثابتة، وعدم التحول إلى ready إلا بعد جميع invariants. |
| P1-16 | Official integrations | NID/professional/organization/government registries وOCR/NFC/biometrics غير مفعلة أو غير متصلة. | `PARTIAL` صحيح؛ لا يجوز استخدام stub أو fallback لإعلان verified. | provider contracts، signed evidence، timeout/retry/idempotency، secrets rotation، sandbox contract tests، ثم activation بموافقة بشرية. |

### 2.3 أولويات P2 — جودة واعتمادية ومخاطر تراكمية

| المعرّف | المجال | المشكلة | المعالجة |
|---|---|---|---|
| P2-01 | Python/SQLAlchemy time | 252 warning منها `datetime.utcnow` وdeprecated adapters/setex. | توحيد timezone-aware UTC، تحديث APIs، وتشغيل warnings-as-errors تدريجياً. |
| P2-02 | DB teardown cycle | تحذير unresolvable FK cycle بين `national_encounters` و`national_referrals`. | مراجعة ForeignKey/use_alter/ondelete، اختبار create/drop وmigration على PostgreSQL. |
| P2-03 | Test weak key | SecurityWarning عن key size في test fixture. | استخدام test secrets بطول آمن مع إبقاء production validation منفصلاً. |
| P2-04 | Test environment semantics | bypass CSRF محصور بـENV=test، لكن أي mis-set للـENV قد يغيّر security behavior. | fail-fast على unknown ENV، منع test flags في image production، وطباعة non-secret runtime policy في startup. |
| P2-05 | Security headers | middleware يتجاوز asset paths، ويستخدم `X-XSS-Protection` القديم، وhealth cache public. | اختبار headers على HTML/API/assets، CSP report-only ثم enforcement، وno-store للdiagnostics. |
| P2-06 | Docs/contracts | contract generator يستخدم defaults localhost في بعض metadata. | توليد base URLs من config validated وعدم نشر localhost في production schemas. |
| P2-07 | Connector observability | simulated/subscription failure قد لا يميز between unavailable وdelivered. | status enum موحد: unavailable/simulated/delivered/failed، metrics وdead-letter durable. |
| P2-08 | Route ownership | modules كثيرة وroute-level policies غير موحدة. | CODEOWNERS/route owners، security review لكل domain، وCI route coverage. |
| P2-09 | Deprecated broad roles | legacy role names وNIAM assurance/permissions قد تتعايش دون mapping واحد. | permission registry canonical وmigration matrix وdeny unknown roles. |
| P2-10 | Operational documentation | تقارير Commands ممتازة لكنها لا تكفي كrunbook staging. | runbook قابل للتنفيذ مع evidence paths، rollback، owner، expiry، وapproval record. |

## 3. خريطة الإصلاح المرحلية

### المرحلة صفر: الاحتواء ومنع التفعيل

يجب إبقاء التسجيل العام، provider الرسمي، OCR/NFC/biometrics، government adapters، financial engine، وsingle-write NIAM مغلقة. يجب منع `ALLOW_DEGRADED_REDIS=true` في staging/production، ووضع `NON_BLOCKING_STARTUP=false` إلى حين إثبات أن readiness لا يسمح بأي traffic حساس قبل اكتمال الاعتمادات. كما يجب تقييد deep/kernel health إلى network داخلي أو إزالة التفاصيل منهما، وإيقاف public AI result مؤقتاً إذا تعذر إصلاح token policy قبل release.

### المرحلة الأولى: إصلاح P0 الأمني

يبدأ التنفيذ بإضافة `X-CSRF-Token` إلى CORS allowlist وفرض CSRF على refresh cookie، ثم تحويل readiness إلى fail-closed حقيقي. بعدها تُغلق صلاحيات kernel/runtime وAI Fabric وgovernance والـnested document routers عبر permissions صريحة وtenant/workspace checks. بالتوازي يُمنع simulated success وTLS verification bypass في التكاملات، ويُعاد تصميم public result links بمخزن مشترك وtoken hashing وعدم التسجيل.

**بوابة المرحلة:** جميع P0 tests الجديدة يجب أن تشمل anonymous، authenticated wrong-role، cross-tenant، Redis unavailable، concurrent refresh، CSRF preflight، وconnector dependency missing. أي فشل في tenant isolation أو Redis fail-closed يعيد الحالة إلى SAFE_STOP.

### المرحلة الثانية: عزل البيانات والتكاملات

ينبغي فصل `system:admin` إلى scopes عملية، وإضافة server-side filters لكل organization/facility/workspace. تُنقل health-data/event-store/local storage إلى backing durable مشفر، وتُمنع responses من إعادة API keys أو PII أو PHI. يُعتمد egress allowlist وSSRF protection لكل connector، وتُدار الأسرار عبر secret manager مع rotation وexpiry.

**بوابة المرحلة:** اختبار access matrix موثق لكل دور، data retention/redaction test، backup/restore، PostgreSQL transaction/race، وRedis TLS/ACL على workerين على الأقل.

### المرحلة الثالثة: مواءمة الويب وNIAM

يُنفذ dual-read parity read-only بين legacy وNIAM على بيانات اصطناعية، ثم يُفعّل NIAM AuthContext خلف feature flag في staging فقط. تُقارن login/refresh/logout/logout-all وworkspace selection وpermissions، مع telemetry لا تحتوي PII. بعد نجاح نافذة rollback ومراجعة بشرية، يُنفذ single-write NIAM، ثم تزال legacy refresh fallback تدريجياً.

**بوابة المرحلة:** لا فرق غير مفسر في session state أو permission decision، ولا fallback صامت، ونجاح browser tests مع origins وcookies الفعلية.

### المرحلة الرابعة: تكافؤ الهاتف وOffline-first

تشغّل CI Android وFlutter على SDK الأصلية، ثم تُضاف اختبارات contract مشتركة للمصادقة، SQLCipher، sync queue، conflict resolution، clock skew، logout/revocation، وnotification delivery. لا تُعلن parity بناءً على compile فقط؛ يلزم instrumented test وTalkBack/Orca evidence وWCAG result.

### المرحلة الخامسة: إثبات staging والمراجعة البشرية

تُنشأ بيئة staging معزولة ببيانات اصطناعية فقط، PostgreSQL وRedis TLS/ACL وsecret manager وworkerين على الأقل. يُشغّل runbook يشمل migrations roundtrip، race/replay، CORS/CSRF browser، tenant isolation، audit redaction، connector outage، backup/restore، mobile contracts، وrollback.

لا ينتقل القرار إلى `AUTHENTICATION_COMPLETE` أو `COMPLETE` إلا بعد مرور كل بوابات P0/P1 ومراجعة بشرية موثقة. فشل أي security gate أو tenant isolation أو provider verification يعيد القرار إلى SAFE_STOP.

## 4. مصفوفة الأولوية والملكية المقترحة

| المسار | المسؤول المقترح | الأولوية | المخرج |
|---|---|---|---|
| Startup/readiness/Redis/CSRF | Backend security/platform | P0 | invariant tests + staging proof |
| Runtime/AI/governance authorization | IAM + domain owners | P0 | permission/tenant matrix |
| Public result links/logging | Clinical privacy + backend | P0 | token privacy design + DLP tests |
| Connectors/egress/secrets | Integration/SRE/security | P0 | allowlist + TLS/secret rotation |
| Health-data/document storage | Data platform/security | P1 | durable encrypted storage + access audit |
| Legacy/NIAM web cutover | IAM + frontend | P1 | parity report + rollback |
| Android/Flutter/offline | Mobile teams | P1 | instrumented/contract/WCAG evidence |
| Warnings/FK/deprecations | Backend maintainers | P2 | warning-free targeted gates |

## 5. معايير “مغلق” و“غير مغلق”

لا يُغلق العائق لأن unit test محلياً نجح فقط. الإغلاق يتطلب source fix، regression test، static gate، effective route/authz evidence، وstaging evidence عندما يكون العائق متعلقاً بتعدد العمال أو TLS أو browser أو PostgreSQL أو mobile. يجب أن يحتوي كل إغلاق على commit، test log، owner، تاريخ، وrollback path.

> **قاعدة SAFE_STOP:** أي فشل في Redis fail-closed، refresh replay serialization، CSRF/CORS browser gate، effective tenant isolation، أو verification provider boundary يمنع الانتقال إلى release أو production، حتى لو بقيت بقية الاختبارات خضراء.

## 6. القرار النهائي

تم تحديد **39 بنداً رئيسياً** ضمن سجل الإصلاح التفصيلي: 13 بند P0، و16 بند P1، و10 بنود P2. بعض البنود متداخلة في أكثر من مجال، لذلك لا تُفهم الأعداد كعدد ثغرات مستقلة قابلة للجمع بين الملفات؛ الرقم يمثل بنود معالجة/تحقق.

النتائج المحلية الحالية جيدة من حيث الاختبارات، لكنها لا تكفي لإزالة SAFE_STOP. الحالة الصحيحة هي `AUTHENTICATION_RUNTIME_PARTIAL` مع إبقاء كل التفعيلات الحساسة مغلقة إلى أن تُنفذ مراحل P0 ثم P1 في staging معزول وبمراجعة بشرية.

لم يتم أثناء هذا الجرد تنفيذ push أو merge أو deployment أو production migration أو تغيير source code. الملفات التي أُنشئت هي تقارير جرد وتحليل وخطة فقط.

## المراجع

[1]: `../security-audit/20260815/P0_IDENTITY_ACCOUNT_LIFECYCLE_COMMAND05_AR.md` — تقرير Command 05 وتكامل Redis والواجهة.

[2]: `../security-audit/20260815/COMMAND06_REMEDIATION_AR.md` — تقرير معالجة Command 06 وحدود SAFE_STOP.

[3]: `../backend/app/core/startup_guard.py` — startup validation وpartial-readiness behavior.

[4]: `../backend/app/factory.py` — middleware، CORS، route registration، وlifespan.

[5]: `../backend/app/middleware.py` — readiness وsecurity headers وhealth allowlist.

[6]: `../backend/app/main.py` — health/status/deep/kernel endpoints.

[7]: `../backend/app/kernel/runtime_routes.py` — runtime/AI/policy operational routes.

[8]: `../backend/app/ai_fabric/routes.py` — AI Fabric and clinical/public-health routes.

[9]: `../backend/app/routes/ai.py` — public AI result and provider-discovery routes.

[10]: `../backend/app/health_data/routes.py` — data lake/event store/warehouse routes.

[11]: `../backend/app/national/ecosystem/routes.py` — connector registration, outbound operations, credentials and audit.

[12]: `../backend/app/national/ecosystem/connectors/messaging_connector.py` — simulated publish and TLS verification behavior.

[13]: `../backend/app/governance/routes/governance_routes.py` — governance identity, worker, audit and policy routes.

[14]: `../backend/app/document_intelligence/api/routes.py` — nested router composition.

[15]: `../frontend-v3/src/contexts/AuthContext.tsx` — legacy web auth context.

[16]: `../.github/workflows/staging-verify.yml` — staging health verification workflow.


## 7. ملحق تحقق محلي — 16 آب 2026

يصحح هذا الملحق حالة السجل بعد دفعة المعالجة المحلية الأخيرة. تم تعديل source محلياً على الفرع `security/p0-bootstrap-alembic`، من دون push أو merge أو deployment أو migration إنتاجية. أصبح عدد الاستخدامات النصية لـ`datetime.utcnow` في `backend/app` و`shared` صفراً، مع تحويل callsites وSQLAlchemy `default/onupdate` و`dataclasses` وcode generators إلى UTC-aware callables. كما أضيفت مواءمة frontend-v3 مع scopes المالية والتكاملية الدقيقة، وفُصلت financial routes إلى read/write/orchestration/subscription permissions.

| البند | الحالة المحلية الجديدة | دليل التحقق |
|---|---|---|
| UTC-aware timestamps | **مغلق محلياً**؛ `datetime.utcnow` occurrences = 0 | grep residual scan + `compileall` |
| Financial route authorization | **مغلق محلياً**؛ read/write/orchestration/subscription guards مضافة، والـengine ما زال خلف feature flag | `backend/app/financial/routes.py`، full backend gate |
| Contract exposure | **مغلق محلياً**؛ internal contract metadata export محمي، public allowlist محدود | `backend/app/contracts/routes.py`، contract tests |
| Public lab-result token | **مغلق محلياً ضمن نطاق التصميم الحالي**؛ hash lookup/TTL/error minimization مطبقة، مع بقاء audit staging مطلوباً | `backend/app/models/lab_result.py`، security regression tests |
| Ecosystem authorization/redaction | **مغلق محلياً ضمن static/contract scope**؛ granular scopes وPII redaction مطبقان | `backend/app/national/ecosystem/routes.py`، side-door tests |
| Frontend RBAC alignment | **مغلق محلياً**؛ `runtime:operate` للـedge و`payments:read` للـfinancial، مع role maps محدثة | `frontend-v3/src/permissions/index.ts`، frontend build |
| Backend regression gate | **ناجح**؛ 2654 passed، 42 deselected، 20 warnings | `pytest -q -m 'not integration'` |
| Frontend gate | **ناجح**؛ الاختبارات والبناء/PWA اكتملت بنجاح | `pnpm test -- --run` و`pnpm build` |

لا يزيل هذا الملحق `SAFE_STOP`. تبقى البنود المرتبطة بموفر الهوية الرسمي، Redis/PostgreSQL متعدد العمال في staging، browser CSRF/CORS الحقيقي، TLS/egress للموصلات، Android/Flutter وTalkBack/Orca، وPentest المرخص مفتوحة حتى إنتاج أدلة خارجية قابلة لإعادة التشغيل. كما لا يُعد نجاح الاختبارات المحلية دليلاً على خلو النظام المطلق من الثغرات؛ القرار التشغيلي الصحيح يبقى `AUTHENTICATION_RUNTIME_PARTIAL` إلى حين استيفاء شروط staging والمراجعة البشرية.

تم تصحيح العبارة السابقة التي كانت تفيد بأن الجرد لم يعدل source؛ فهي صحيحة فقط عند بداية الجرد، وليست صحيحة بعد هذا الملحق.
