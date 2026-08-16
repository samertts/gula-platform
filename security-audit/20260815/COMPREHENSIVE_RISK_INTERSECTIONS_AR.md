# تحليل التناقضات والتقاطعات والعلاقات السببية

## نطاق التحليل

هذا الملف يربط الأدلة المستخرجة من ملفات المصادقة والـmiddleware والـroutes والتكاملات والواجهة وCI. لا يُعد اختبار اختراق خارجياً، ولا يثبت قابلية استغلال كل مسار؛ لكنه يحدد أين تتضاعف المخاطر عندما تتفاعل عدة قرارات صحيحة جزئياً أو حدود مختلفة داخل التطبيق.

## مصفوفة التقاطعات الحرجة

| ID | التقاطع | السلسلة السببية | الأثر | الأولوية |
|---|---|---|---|---|
| X-001 | CSRF middleware × CORS allowlist × Frontend interceptor | الواجهة ترسل `X-CSRF-Token`، لكن `factory.py` لا يضيفه إلى `allow_headers`؛ عند اختلاف origin يفشل preflight أو لا يصل header إلى middleware | فشل login/refresh/logout أو سلوك متباين بين local وstaging، وقد يدفع فرق التشغيل إلى تعطيل الحماية | P0 |
| X-002 | Refresh cookie × CSRF شرط access cookie | middleware يفرض CSRF عندما توجد `access_token`، بينما refresh قد يعتمد `refresh_token` وحده؛ انتهاء access لا يلغي الحاجة لحماية refresh mutation | احتمال تدوير refresh من cross-site إذا غاب شرط إضافي، أو تناقض بين مسارات cookie | P0 |
| X-003 | Non-blocking startup × partial readiness × health allowlist | factory يبدأ runtime في الخلفية، startup guard قد يقبل `partial_startup_timeout`، والـReadinessMiddleware يعتمد حالة واحدة؛ health paths لا تمر بالحاجز | احتمال اختلاف بين liveness/ready/traffic، أو قبول traffic قبل اكتمال DB/Redis/kernel إذا حدثت حالة race أو bypass | P0 |
| X-004 | Public diagnostics × staging verifier | `/health/deep` و`/health/status` و`/health/kernel` عامة، وworkflow staging يعتمد deep-health؛ ما هو مطلوب للبوابة يصبح متاحاً للمهاجمين | تسريب queue/memory/circuit/auto-repair/errors، وتثبيت عقد تشغيلية عامة يصعب إغلاقها لاحقاً | P1 |
| X-005 | Production `ALLOW_DEGRADED_REDIS` × revocation/rate-limit | السماح بـmemory fallback يجعل كل worker يملك حالة مختلفة؛ token blacklist وperm-version وrate-limit لا تعود مشتركة | replay بعد logout، brute-force عبر workers، وفشل tenant/session safety رغم readiness ظاهري | P0 |
| X-006 | Generic auth × AI Fabric clinical operations | router يتطلب `get_current_user` فقط، وتبقى clinical analyze/drug interaction/lab/public-health/chat/RAG بلا permission/purpose/tenant check | أي حساب مصادق قد يرسل PHI أو يحصل على تحليل/قدرات تشغيلية خارج workspace | P0 |
| X-007 | Coarse `system:admin` × health-data/document/ecosystem surfaces | permission واحدة تغطي event-store raw replay، warehouse، ingestion، document access، dynamic connectors، API-key issuance | تضخم blast radius؛ اختراق أو إساءة استخدام admin واحد يتحول إلى قراءة/تغيير عابر للأنظمة | P0/P1 |
| X-008 | Dynamic connector registration × simulated success × TLS verify flag | admin يسجل connector ديناميكياً، library مفقودة تعيد نجاحاً وهمياً، و`verify=false` قد يسمح TLS غير موثق | أحداث/إشعارات أو معاملات تظهر ناجحة دون تسليم، أو outbound integration غير موثوق/قابل للاعتراض | P0 |
| X-009 | Public bearer result token × token logging × in-process cache | token سريري يكفي للوصول، prefix يُسجل في logs/audit، cache غير مشترك بين workers | confidentiality/linkability، سلوك مختلف بين workers، وصعوبة إبطال/تدقيق الرابط | P0 |
| X-010 | Legacy AuthContext × NIAM pilot × CSRF migration window | التطبيق الفعلي legacy، pilot NIAM منفصل، والجلسات القديمة لها سياسة CSRF انتقالية | إصلاح مسار لا يصل للمستخدم الفعلي، أو اختلاف logout/refresh/permissions بين clients | P1 |
| X-011 | Public certification/contracts × source introspection | release evaluation وmetrics وcontract schemas عامة؛ generated output قد يعكس مكونات/إصدارات وعمليات داخلية | reconnaissance وresource exhaustion، مع صعوبة تمييز public contract من internal operations | P1/P2 |
| X-012 | Local file/in-memory health data × multi-worker/production | `LocalStorageBackend` الافتراضي يستخدم `/tmp`، وevent/policy/SDK caches module-level؛ لا يوجد إثبات durable/shared/encrypted | فقد بيانات، اختلاف نتائج، تسريب عبر filesystem أو عدم اتساق offline/integration | P1 |
| X-013 | Public health endpoints × HSTS/security headers/cache policy | health endpoints allowlisted وتُعطى public cache لمدة 10 ثوانٍ؛ diagnostics لا تحمل auth أو tenant context | cache أو proxy قد يعرض حالة تشغيلية قديمة لمستخدم غير مقصود | P1 |
| X-014 | Mobile CI success claim × unavailable local SDK × no staging parity gate | CI يبني Android/Flutter، لكن البيئة المحلية لا تستطيع تشغيل SDK، وstaging workflow لا يختبر mobile contracts/offline/SQLCipher | لا يمكن إعلان parity أو WCAG/secure offline completion بناءً على backend/frontend فقط | P1 |
| X-015 | Public self-registration gate × provider-not-connected × account lifecycle | التسجيل العام مغلق، provider الرسمي غير متصل، لكن وجود routes/flags متعددة قد يخلق مساراً غير متسق بين legacy وNIAM | حسابات معلقة أو status transitions غير قابلة للإتمام، أو ضغط تشغيل لتفعيل bypass | P0 governance |
| X-016 | Health-number/governance reads × identity mapping | endpoints governance تعيد health number/history/worker/node بيانات بلا boundary واضح، بينما identity parity يمنع fallback فقط داخل NIAM | قراءة سجل حكومي خارج workspace حتى مع سلامة NIAM mapping | P0/P1 |
| X-017 | Audit logging × PII/token fields × broad admin read | audit/critical alert قد يحمل token prefix وIP وdetails؛ ecosystem audit يعيد details وIP؛ health/data routes تعيد metadata | تضخم سطح البيانات الحساسة داخل logs وresponses، وارتفاع أثر أي تسريب صلاحية | P1 |
| X-018 | `system_ready` boolean × multiple dependency classes | DB/Redis/migrations/kernel/background/async engine لها lifecycles مختلفة، لكن readiness النهائي يمثلها بعلم واحد | false positive/negative readiness وصعوبة معرفة أي contract مُثبت فعلاً | P1 |

## التناقضات التصميمية الرئيسية

### التناقض بين الأمن النظري والعقد التشغيلي

التقارير السابقة تثبت fail-closed في local strict tests، لكن config يسمح صراحةً بـ`ALLOW_DEGRADED_REDIS=true` في staging/production. لذلك فإن كلمة “fail-closed” ليست invariant مطلقة؛ بل policy قابلة للتجاوز بواسطة متغير بيئة. يجب تحويلها إلى منع production/staging غير القابل للتجاوز إلا بتوقيع تشغيل موثق ومحدود زمنياً، أو إزالة fallback تماماً من runtime الحساس.

### التناقض بين الحماية على مستوى router والحماية على مستوى الوظيفة

وجود `dependencies=[Depends(require_permission("system:admin"))]` يثبت authentication/permission عامة، لكنه لا يثبت tenant isolation أو purpose limitation أو separation of duties. وبالمقابل، وجود dependency داخل endpoint لا يضمن أن nested router يحتفظ بالحماية المقصودة بعد `include_router`. يلزم route catalog آلي يقيّم effective dependencies بعد بناء FastAPI app، لا AST فقط.

### التناقض بين public health وsecurity observability

الـhealth endpoints مصممة للمراقبة بلا مصادقة، لكن `health/deep` يعرض queue وmemory وcircuits وauto-repair وlatency، و`health/kernel` يعرض error string. هذا يتجاوز الحد الأدنى اللازم لـliveness/readiness. الأفضل فصل probe داخلي authenticated أو network-restricted عن liveness العام، وإرجاع schema ثابتة بلا تفاصيل داخلية.

### التناقض بين “server-authoritative” وواجهة legacy

الواجهة لا تمنح authorization محلياً، وهذا صحيح، لكنها ما زالت تستخدم legacy AuthContext بينما canonical NIAM pilot منفصل. النتيجة أن مصدر session UX ليس هو مسار NIAM الذي تدقيقه Commands 04–06. لا يمكن اعتبار التكامل منجزاً قبل dual-read parity موثق، ثم cutover feature-flagged، ثم إزالة fallback من client بعد نافذة rollback.

## العناصر التي لا يجوز تصنيفها كثغرة دون تحقق إضافي

بعض المسارات العامة مقصودة: `app-updates`، OAuth/SAML metadata، FHIR terminology links، وcontract schemas العامة قد تكون جزءاً من التوافق. كذلك `contracts/export` لا يثبت arbitrary path write لأن generator يستخدم server-owned temporary directory. ويجب عدم اعتبار كل `http://` في source ضعف TLS؛ جزء منها namespaces/terminology أو internal Docker defaults. هذه العناصر تبقى ضمن review/defense-in-depth إلى أن يثبت exposure فعلي في staging.
