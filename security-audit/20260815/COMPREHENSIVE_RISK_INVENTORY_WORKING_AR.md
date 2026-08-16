# جرد المخاطر الشامل — ملاحظات عمل

## Baseline

الفرع `security/p0-bootstrap-alembic`، HEAD `0db96cc2`، working tree نظيف، Alembic head واحد `20260815_0025`. آخر قرار موثق: `AUTHENTICATION_RUNTIME_PARTIAL` مع `SAFE_STOP`.

## أدلة أولية مثبتة

| ID | المجال | الدليل | التصنيف الأولي |
|---|---|---|---|
| R-001 | Startup/Readiness | `startup_guard.py` يرفع `system_ready=True` بعد timeout ويذكر قبول traffic في حالة `partial-readiness`؛ `factory.py` يسمح بـ`NON_BLOCKING_STARTUP=true` في staging/production | P0 تشغيلي/أمني يحتاج إثبات أن ReadinessMiddleware يمنع كل traffic غير الصحي، ومنع حالة partial التي تسمح بمسار خاطئ |
| R-002 | Health exposure | `main.py` يتيح `/health/status`, `/health/deep`, `/health/kernel` دون auth ضمن allowlist؛ deep يعرض DB/Redis latency وqueue backlog وmemory/circuits/auto-repair، وkernel يعيد `str(e)` عند الخطأ | P1/P0 معلومات تشخيصية وتسريب exception محتمل |
| R-003 | CORS/CSRF intersection | `factory.py` allow_headers لا يتضمن `X-CSRF-Token` رغم أن frontend يرسله وmiddleware يتحقق منه | P0 متصفحياً: preflight قد يفشل عندما يكون frontend وAPI على origins مختلفة |
| R-004 | CSRF refresh gap | `CSRFMiddleware` يشترط وجود `access_token` cookie قبل فرض CSRF، بينما `/auth/refresh` قد يستخدم `refresh_token` وحده | P1/P0 حسب cookie deployment: refresh mutation قد لا يمر double-submit |
| R-005 | Production degraded Redis | `config.py` يسمح `ALLOW_DEGRADED_REDIS=true` في staging/production مع warning وmemory fallback | P0 policy: fallback محلي يخرق shared revocation/rate limiting حتى مع acknowledgement |
| R-006 | Legacy/NIAM drift | `AuthContext.tsx` المنشور يستخدم `/login`, `/session`, `/logout` وmembership reflection؛ NIAM pilot مستقل ومغلق افتراضياً | P1 migration/parity blocker، وليس ثغرة مباشرة ما دام server auth authoritative |
| R-007 | Runtime operational surface | `kernel/runtime_routes.py` جميع endpoints تعتمد `get_current_user` فقط؛ تشمل optimize وvalidation/run وAI infer وrules/policies | P0/P1 authorization boundary: generic authenticated user قد يصل إلى عمليات تشغيلية حساسة |
| R-008 | Governance read/write split | `governance_routes.py` يحمي بعض writes بـ`require_role` لكنه يترك GETs وأحداث audit/training/competency/productivity وبعض endpoints بلا dependency | P0/P1 احتمال تسريب أو تعديل غير محمي، يحتاج route-by-route verification |
| R-009 | Governance health-number exposure | `get_health_number` وhistory بلا dependency؛ `get_node` وغيرها read بلا dependency | P1: identity/governance data exposure |
| R-010 | Financial engine authorization | `financial/routes.py` يعتمد `get_current_user` وlab scope فقط، دون role/permission separation داخل module؛ feature flag مغلق افتراضياً | P1 latent: إذا فُعل flag، read/write/refund/billing قد لا يحقق فصل الأدوار |
| R-011 | Docs auth mismatch | `DocsAuthMiddleware` يقبل legacy JWT role `admin/master_admin` فقط، ولا يثبت NIAM account/membership/governance context | P1 contract drift، وقد يمنع authorized NIAM admins أو يفتح legacy role غير مقصود |
| R-012 | Public diagnostic/config endpoints | `/health*`, `/mobile/app-info`, `/app-updates`, OAuth metadata/SAML metadata وبعض AI public endpoints عامة | P1 inventory required; بعضها مقصود وبعضها يفضح معلومات أو يحتاج rate limiting/contract review |
| R-013 | Public AI result sharing | `routes/ai.py` `interpret_result_public` يستخدم result token وin-process cache/provider fallback؛ token prefix يظهر في logs حسب overview | P0/P1: bearer-link confidentiality، cache multi-worker inconsistency، logging sensitivity |
| R-014 | Connector/adapters | external adapters default `stub`; live/shadow and credentials are environment-controlled; absence of staging/provider proof remains | P1 integration blocker; no activation without contract, timeout, retry, audit, tenant and secret-rotation proof |
| R-015 | Mobile parity | Android/Flutter SDKs unavailable; offline-first/security parity unverified | P1/P0 release blocker for mobile claims |
| R-016 | Secrets fallback | development generates random JWT/refresh keys and aliases NID/Audit keys; acceptable only non-production but can cause restart/session loss and key separation ambiguity | P1 operational/cryptographic drift; require explicit dev-only mode and secret separation tests |
| R-017 | Health response caching | Security headers cache allowlisted health paths public for 10s; diagnostic endpoints may expose stale but sensitive operational data | P1 response policy inconsistency |
| R-018 | Route surface size | `factory.py` registers a very large cross-domain route surface into one app with mixed legacy/NIAM and mixed auth models | P1 governance/attack surface; needs route catalog and deny-by-default classification |

هذه الملاحظات ليست التقرير النهائي بعد؛ يلزم استكمال static/route/config/test evidence ثم تحديد priority وشرط الإغلاق لكل عنصر.

## أدلة إضافية من route/static/mobile audit

| ID | المجال | الدليل | التصنيف الأولي |
|---|---|---|---|
| R-019 | AI Fabric | router محمي فقط بـ`get_current_user`؛ chat/embed/RAG/clinical analysis/drug interaction/lab analysis/public-health surveillance لا تحمل permission/doctor/tenant scope داخل module | P0: مستخدم مصادق عام قد يستدعي عمليات AI/سريرية أو يمرر بيانات مرضى |
| R-020 | Certification | `/certification` router بلا auth؛ evaluate/report/metrics/release/check/validate مكشوفة، وبعضها يشغّل فحوصات وملفات وتقارير PDF | P0/P1: surface إداري/تشغيلي غير محمي وDoS/معلومات داخلية محتمل |
| R-021 | Contracts | `/contracts` عام عمداً، و`POST /contracts/export` عام؛ generator يقيّد الكتابة إلى temp safe-root، لذلك ليس arbitrary path write، لكنه introspection/file-generation عام يحتاج قرار exposure/rate-limit | P2/P1 حسب سياسة OpenAPI العامة |
| R-022 | Health-data | router محمي بـ`system:admin` واحد فقط ويعرض event-store raw data وtenant_id وmetadata وwarehouse/query وcanonical patient mapping وingestion/policies | P1: least privilege وtenant/workspace scope غير مثبتين؛ P0 إذا كان admin role واسعاً أو متعدد المستأجرين |
| R-023 | Document intelligence nested routers | `obs_router`, `access_router`, `semantic_router`, `lifecycle_router` تُنشأ بلا dependency ثم تُضمّن إلى router admin؛ الامتداد يحتاج اختبار FastAPI فعلي، لأن route composition قد تجعل الحماية غير واضحة أو تعتمد على inheritance غير مقصود | P1: authorization composition risk |
| R-024 | Ecosystem connectors | system:admin واحد يسمح dynamic connector registration، outbound send/receive، schema registration، partner management، API-key issuance وإرجاع `api_key` وaudit details/IP | P0/P1: high-impact integration control، secret exposure، outbound SSRF/abuse review، وleast privilege |
| R-025 | Messaging simulation | غياب paho/aio-pika يعيد `True` من `_simulated_publish`، وsubscription يفشل بصمت/يحاكي؛ `tls.verify=false` يسمح `CERT_NONE` | P0 للتكاملات المالية/الإشعارات: نجاح وهمي وTLS bypass محتمل |
| R-026 | Health diagnostics | `/health/deep` يعرض queue backlog، memory RSS، circuits، auto-repair stats، DB/Redis latency بلا auth؛ `/health/kernel` يعيد exception string | P1: معلومات تشغيلية وتسريب خطأ؛ P0 إذا تعرضت الشبكة العامة |
| R-027 | AI public result | `/api/ai/interpret/{token}` يحمل bearer-link سريري، cache in-process غير مشترك، ويسجل token prefix في audit/log/critical alerts | P0: confidentiality، multi-worker consistency، وقابلية enumeration/log correlation |
| R-028 | Staging verification | workflow يتحقق `/health`, `/health/ready`, `/health/deep` فقط عبر curl ولا يختبر cookie/CSRF/CORS/tenant isolation/refresh replay/authz/Redis TLS/ACL أو بيانات سريرية اصطناعية | P1/P0: gate لا يثبت معايير SAFE_STOP الفعلية |
| R-029 | Mobile environment | `flutter` و`adb` غير متاحين محلياً، مع وجود CI workflows؛ parity/instrumented/offline/SQLCipher لا يمكن إثباته في sandbox | P1 release blocker |
| R-030 | Database warnings | baseline `2649 passed` لكنه أصدر 252 warning؛ منها `datetime.utcnow` واسع، deprecated SQLAlchemy/Python adapters، weak test JWT key warning، وunresolvable FK cycle بين `national_encounters` و`national_referrals` في test teardown | P2/P1: technical debt؛ FK cycle يحتاج schema/migration review |
| R-031 | Connector TLS/default endpoints | defaults داخلية HTTP لـntfy/Ollama/vLLM/PACS و`tls.verify` configurable؛ ليست كلها production paths لكنها تحتاج environment allowlist وعدم السماح بالـHTTP الخارجي في staging/production | P1 defense-in-depth |
| R-032 | Public health allowlist | `/health/status`, `/health/deep`, `/health/kernel` ضمن `_ALWAYS_ALLOWED_PATHS` وتجاوز readiness/auth؛ `/health/status` يعلن environment/version وcomponent states | P1 exposure policy |
| R-033 | Public web auth drift | `AuthContext.tsx` الفعلي يعتمد legacy auth API وdemo markers وsessionStorage؛ NIAM pilot منفصل ومغلق | P1 migration blocker؛ خطر contract divergence وليس bypass حالياً |

## أدلة البوابات الحالية

Backend non-integration أعاد **2649 passed, 42 deselected, 252 warnings** خلال 208.59 ثانية. Frontend أعاد **15 test files / 51 tests passed**، وtypecheck وbuild ناجحين. هذه نتائج صحة الاختبارات الحالية وليست دليلاً على إغلاق الثغرات المصنفة أعلاه.


## ملحق حالة الإغلاق — 2026-08-16

أصبح working tree غير نظيف بسبب تغييرات source والاختبارات والتقارير المحلية، خلافاً لوصف baseline في بداية الجرد. أُغلقت محلياً دفعات P0/P1 الموضحة في `SECURITY_REMEDIATION_STATUS_AR.md`، لكن لم يُنفذ push أو merge أو deployment أو production migration.

| الحالة | النطاق |
|---|---|
| مغلق محلياً | Redis fail-closed، startup/readiness timeout، CORS/CSRF refresh، kernel/runtime permissions، AI Fabric auth، certification auth، document-intelligence nested guards، connector simulated success/TLS، governance router guards، health diagnostics protection، health-data scopes/tenant filtering، AI provider URL allowlist، targeted UTC/deprecation fixes، frontend gates |
| مغلق جزئياً | public AI bearer-link، ecosystem permission separation، durable storage proof، readiness browser/staging proof، P1 audit/PII retention، contract/certification public exposure |
| مفتوح SAFE_STOP | official identity/government provider، public registration، NIAM single-write cutover، PostgreSQL/Redis staging proof، browser CORS/CSRF proof، Android/Flutter/SQLCipher/TalkBack/Orca evidence، external pentest، financial activation |

النتائج المحلية الأحدث: backend non-integration **2650 passed، 42 deselected، 20 warnings**؛ frontend **51 passed** مع نجاح typecheck/build/bundle budget؛ Alembic head واحد `20260815_0025`؛ و`git diff --check` ناجح. هذه النتائج لا تلغي SAFE_STOP عندما يكون شرط الإغلاق متعلقاً ببيئة خارجية أو مراجعة بشرية.

للتفصيل التنفيذي انظر إلى `SECURITY_REMEDIATION_STATUS_AR.md`.
