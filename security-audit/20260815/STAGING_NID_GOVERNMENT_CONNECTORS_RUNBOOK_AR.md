# Runbook إعداد Staging لاختبار NID والموصلات الحكومية

**المشروع:** GULA Platform
**الهدف:** اختبار موفر الهوية الوطني NID والموصلات الحكومية في بيئة معزولة قبل أي تفعيل تشغيلي.
**الحالة الابتدائية:** `SAFE_STOP`؛ لا تُستخدم بيانات اعتماد الإنتاج ولا بيانات مواطنين حقيقية.
**النطاق:** NID، Redis، PostgreSQL، API، frontend، بوابة egress، TLS/mTLS، الموصلات الحكومية، التدقيق، المراقبة، التراجع.

## 1. مبادئ إلزامية قبل البدء

يجب إنشاء staging كمجال مستقل تماماً عن production: نطاق DNS مختلف، قاعدة بيانات مختلفة، Redis مختلف، مفاتيح توقيع وتشفير مختلفة، bucket مختلف، Sentry project مختلف، وموصلات حكومية sandbox مختلفة. يمنع تماماً أن تشير واجهة develop أو preview إلى API الإنتاج، ويجب أن يكون ذلك مثبتاً باختبار CI وبفحص runtime عند الإقلاع.

لا يجوز استعمال أرقام وطنية أو سجلات صحية حقيقية في الاختبارات العامة. تستخدم بيانات اصطناعية، أو بيانات sandbox صادرة رسمياً من موفر NID، أو سجلات anonymized بعد موافقة الجهة المالكة للبيانات. يجب وسم كل سجل اختبار بوضوح بأنه `STAGING_ONLY`، ومنع انتقاله إلى أي production database أو backup.

موفر NID في الكود الحالي يعمل بثلاثة أوضاع: `stub` و`shadow` و`live`. الوضع `stub` لا يجري اتصالاً خارجياً، والوضع `shadow` يجري الاتصال لكنه يعيد بيانات stub إلى المستدعي، أما `live` فيعيد نتيجة الموفر بعد التحقق من شكلها. يتطلب `shadow` و`live` متغيري `MOI_NID_API_URL` و`MOI_NID_API_KEY`، ويجب عدم اعتبار التشغيل ناجحاً إذا خُفّض الوضع فعلياً إلى `stub` بسبب غياب الأسرار [1] [2].

> **قاعدة أمان:** لا يُسمح لنتيجة NID الخارجية بأن تقود قراراً سريرياً. في بنية GULA الحالية يصنف NID كمصدر `NON_CRITICAL` للإثراء، بينما تبقى القرارات السريرية والسجلات الداخلية معتمدة على البيانات الداخلية الموثقة [1].

## 2. تحديد الملكية والموافقات

قبل إنشاء البيئة، يجب تسمية مالك تقني ومالك أمني ومالك بيانات ومالك تكامل من الجهة الحكومية. يوقع مالك البيانات على نوع البيانات المسموح بها، ويوافق المالك الأمني على قواعد الشبكة والأسرار، ويؤكد مالك التكامل endpoints وTLS وschema وlimits، بينما يوافق مالك المنتج على حالات الاستخدام المسموح اختبارها.

| القرار | المالك المطلوب | دليل القبول |
|---|---|---|
| السماح بالاتصال إلى NID sandbox | مالك التكامل + الأمن | خطاب أو ticket رسمي ونطاقات allowlist |
| نوع البيانات | مالك البيانات والخصوصية | data classification وretention period |
| إدارة الأسرار | SRE/الأمن | Vault path وrotation owner |
| تفعيل `shadow` | الأمن + مالك التكامل | change approval ووقت الانتهاء |
| تفعيل `live` في staging | المالك الحكومي + الأمن | sandbox contract evidence |
| الخروج من SAFE_STOP | لجنة المراجعة البشرية | تقرير اختبارات وrollback evidence |

## 3. إنشاء بيئة Staging معزولة

ينبغي إنشاء بيئة باسم واضح مثل `gula-staging-nid` أو `staging-gula-government`. يجب أن تحتوي على API وworker وfrontend وPostgreSQL وRedis وobject storage وobservability منفصلة. لا يكفي تغيير قيمة `ENV` داخل نفس موارد الإنتاج؛ العزل يجب أن يكون على مستوى الحساب أو المشروع أو namespace أو VPC بحسب منصة الاستضافة.

يكون المسار المنطقي كما يلي:

```text
Test browser / CI runner
        |
        | HTTPS only
        v
Staging WAF / API gateway
        |
        +--> GULA API + workers
        |       |
        |       +--> PostgreSQL staging
        |       +--> Redis staging TLS/ACL
        |       +--> encrypted object storage staging
        |       +--> audit/metrics staging
        |
        +--> Egress proxy / allowlist
                |
                +--> NID sandbox
                +--> Government connector sandboxes
```

يجب منع الاتصالات الصادرة الافتراضية من API وworkers. لا يسمح إلا بالمضيفات والمنافذ التالية بعد اعتمادها: PostgreSQL، Redis، NID sandbox، كل موصل حكومي sandbox، وobservability endpoint. يمنع الوصول المباشر إلى عناوين IP عامة غير مدرجة، ويمنع DNS rebinding وprivate-address SSRF، ويجب تسجيل كل محاولة egress مرفوضة دون تسجيل الأسرار أو أرقام الهوية.

## 4. DNS وTLS وmTLS

ينشأ نطاق staging مستقل، مثل `staging.gula-platform.example` و`staging-api.gula-platform.example`. يصدر certificate مستقل له، ولا يعاد استخدام certificate أو private key الإنتاج. يجب فرض TLS 1.2 كحد أدنى، ويفضل TLS 1.3، مع HSTS مناسب لبيئة staging وعدم تعطيل التحقق من الشهادة.

إذا طلب موفر NID أو موصل حكومي mTLS، يُنشأ client certificate خاص بـstaging فقط، ويُحفظ private key في secret manager، ويُربط بالمضيف والبيئة والمدة. يجب تسجيل تاريخ الانتهاء والتنبيه قبل 30 يوماً، واختبار فشل الاتصال عند certificate منتهية أو غير موثوقة. يمنع استخدام `verify=false` أو `CERT_NONE` خارج اختبارات unit المعزولة.

| العنصر | Staging | Production |
|---|---|---|
| DNS | نطاق مستقل | نطاق إنتاج مستقل |
| API key | sandbox key | production key منفصل تماماً |
| TLS certificate | staging certificate | production certificate |
| mTLS client cert | staging identity | production identity |
| CA trust store | CA المطلوبة للـsandbox | CA المعتمدة للإنتاج |
| egress allowlist | sandbox hosts فقط | production hosts فقط |

## 5. تجهيز الأسرار والإعدادات

تُحفظ الأسرار في Vault أو secret manager يدعم versioning وrotation وaudit. لا توضع الأسرار في GitHub repository أو `.env` المرفوع أو logs أو Docker image أو frontend bundle. يجب أن تكون GitHub Environment باسم `staging` محمية بمراجعة بشرية، وأن تكون secrets متاحة للـdeployment والاختبارات التي تحتاجها فقط.

يجب تجهيز المتغيرات التالية بأسماء staging فعلية، مع إبقاء القيم السرية خارج هذا الملف:

```dotenv
ENV=staging
GULA_ADAPTER_MODE=stub
GULA_ADAPTER_MODE_NID=shadow
MOI_NID_API_URL=https://<nid-sandbox-host>
MOI_NID_API_KEY=<stored-in-secret-manager>

DATABASE_URL=postgresql+asyncpg://<staging-user>@<staging-db>/<staging-db-name>
REDIS_URL=rediss://<staging-user>:<password>@<staging-redis>:6380/0
REDIS_TLS_VERIFY=true

CORS_ALLOWED_ORIGINS=https://staging.gula-platform.example
CSRF_COOKIE_SECURE=true
SESSION_COOKIE_SECURE=true

ENCRYPTION_KEY=<staging-only-key>
NID_HMAC_KEY=<staging-only-key>
REFRESH_TOKEN_SECRET=<staging-only-secret>
AUDIT_ANCHOR_KEY=<staging-only-secret>

SENTRY_ENVIRONMENT=staging
ALLOW_DEGRADED_REDIS=false
```

يجب إضافة preflight deployment يمنع الإقلاع إذا كانت `ENV` غير صحيحة، أو كان `ENV=staging` مع `REDIS_URL` غير مشفر، أو كان NID في `shadow/live` دون credentials، أو كان endpoint خارج allowlist، أو كان `ALLOW_DEGRADED_REDIS=true`. كذلك يجب فحص **effective mode** بعد الإقلاع؛ لأن وجود `GULA_ADAPTER_MODE_NID=shadow` مع secret مفقود قد يؤدي في التطبيق الحالي إلى downgrade إلى `stub` [2].

## 6. تهيئة PostgreSQL وRedis

يُنشأ PostgreSQL staging من migration baseline مع مستخدم محدود الصلاحيات. يمنع استخدام superuser من التطبيق. تُفعّل SSL، وتُنشأ schemas أو قواعد منفصلة عند الحاجة، وتُفعل audit logs للعمليات الإدارية. تُحمّل فقط fixtures اصطناعية: مرضى اصطناعيون، أطباء اصطناعيون، سجلات صرف اصطناعية، وتذاكر اختبارية.

يُنشأ Redis staging منفصل مع TLS وACL، ويُختبر أن التطبيق يفشل مغلقاً عند انقطاعه بدلاً من التحول إلى memory store. يجب تشغيل API بأكثر من worker في اختبار منفصل، ثم تنفيذ logout/revocation وrefresh rotation وrate-limit من worker مختلف. يسجل الاختبار correlation ID والنتيجة فقط، ولا يسجل tokens أو raw national IDs.

## 7. تهيئة NID بالتدرج الآمن

### المرحلة الأولى: STUB contract gate

قبل أي اتصال خارجي، تُشغّل اختبارات العقد محلياً وعلى staging باستخدام `GULA_ADAPTER_MODE_NID=stub`. يجب التأكد من أن invalid ID length يرفض بشكل صحيح، وأن response envelope يحتوي provenance و`requires_verification`، وأن NID لا يظهر في cache key أو logs بصيغته الخام. لا تُستخدم هذه المرحلة لإثبات الاتصال الحكومي؛ هي فقط تثبت أن حدود التطبيق سليمة.

### المرحلة الثانية: SHADOW

بعد اعتماد endpoint وcredentials sandbox، يُفعل `GULA_ADAPTER_MODE_NID=shadow`. في هذا الوضع تُجرى المكالمة الحقيقية ويُسجل الفرق المراقب، لكن التطبيق يعيد نتيجة stub إلى المستدعي. يجب إخفاء raw NID من logs، وإخفاء response payload الحساس، وتسجيل hash أو correlation ID فقط. تستمر المرحلة مدة محددة، مثلاً 24–72 ساعة أو عدد معاملات متفق عليه، مع مراقبة latency، error rate، schema mismatches، timeout، circuit breaker، rate-limit، ونتائج المقارنة.

يجب اختبار الحالات التالية في SHADOW:

| الحالة | النتيجة المتوقعة |
|---|---|
| ID sandbox صحيح | external success مسجل، والـcaller يستلم stub contract فقط |
| ID غير صحيح | response validation مضبوط، دون كشف تفاصيل حساسة |
| 401/403 من NID | لا fallback صامت إلى verified؛ يسجل failure ويُرفع alert |
| 429 | احترام retry/backoff وrate limit وعدم التكرار غير المحدود |
| timeout | circuit breaker ونتيجة degraded واضحة |
| schema ناقص أو زائد | رفض validation وعدم تمرير response إلى domain |
| شهادة غير صالحة | فشل TLS صريح وعدم تعطيل verification |
| NID متوقف | لا يحدث success وهمي، وتبقى الحالة requires verification |
| تكرار request | correlation/idempotency behavior موثق |

### المرحلة الثالثة: LIVE محدود

لا ينتقل staging إلى `live` إلا بعد نجاح SHADOW وتوقيع التقرير. يكون LIVE محدوداً على test cohort أو service account أو endpoint محدد، وبـfeature flag قابل للتراجع. يمنع أن تتحول نتيجة NID إلى قرار سريري أو إنشاء هوية نهائية دون قواعد NIAM والمراجعة المطلوبة. يجب أن تظهر في كل response provenance وsource وtimestamp و`requires_verification` عند الحاجة.

## 8. إعداد الموصلات الحكومية

يجب إنشاء سجل موصلات يحدد لكل موصل: الغرض، مالك البيانات، نوع البروتوكول، endpoint sandbox، TLS/mTLS، scopes، حدود المعدل، schema، retry policy، idempotency key، retention، وطريقة إيقافه. لا يُسمح بتفعيل موصل لمجرد تسجيله في registry؛ يلزم اختبار contract وegress وauthorization.

| الموصل | اختبارات إلزامية |
|---|---|
| NID | identity verification، schema، rate-limit، timeout، circuit، provenance |
| السجل الصحي أو وزارة الصحة | tenant scope، PHI minimization، consent، audit، replay protection |
| LIS/RIS/PACS | HL7/FHIR/DICOM validation، duplicate message، delivery receipt، retry |
| الدفع الحكومي | authorization، idempotency، success/failure، refund/reconcile، cash/electronic segregation |
| SMS/notifications | template allowlist، عدم تضمين PHI، rate-limit، delivery status |
| التوقيع الرقمي | certificate chain، timestamp، invalid signature، key rotation |
| GIS/السجل الإداري | allowlist، data minimization، cross-administrative-unit denial |

كل outbound request يجب أن يمر عبر egress proxy أو connector service مركزي، لا عبر HTTP client عشوائي داخل route. يجب أن يضيف request correlation ID وidempotency key، ويزيل credentials من error messages، ويمنع إعادة raw response إلى المستخدم. كل inbound webhook يجب أن يتحقق من signature أو mTLS، وtimestamp/nonce، وreplay window، وschema، ثم يسجل audit event محدوداً.

## 9. CI/CD وGitHub Environment

يُنشأ GitHub Environment باسم `staging` مع required reviewers، ويمنع workflow من الوصول إلى production secrets. يضاف workflow مستقل يتدرج في مراحل: build، unit/security tests، deploy staging، preflight configuration، health/readiness، connector contract tests، browser tests، smoke tests، ثم artifact upload.

الـworkflow الحالي يفحص `/health` و`/health/ready` و`/health/deep` فقط [3]. يجب توسيعه ليشمل:

1. التحقق من أن health URL يستخدم HTTPS ولا يحتوي credentials أو query أو fragment.
2. التحقق من أن `/health` و`/health/ready` يعيدان الحالة الصحيحة، وأن deep health لا يكشف أسراراً.
3. التحقق من effective NID mode وعدم قبول `stub` عندما تكون المرحلة shadow/live مطلوبة.
4. تشغيل connector contract tests ضد sandbox أو mock server معتمد.
5. تشغيل browser CSRF/CORS وrefresh rotation.
6. تشغيل tenant-isolation وRBAC matrix.
7. نشر summary لا يحتوي tokens أو PII أو response payloads.

## 10. بيانات الاختبار ومصفوفة الصلاحيات

تُنشأ مجموعة test cohort معروفة مسبقاً: هوية ناجحة، هوية غير صالحة، هوية منتهية أو محظورة، response ناقص، provider timeout، provider 429، ومستخدم غير مخول. كل معرف يرتبط بـtest case ID وليس باسم مواطن.

| الدور | NID read | NID manage/config | connector send | connector receive | financial write |
|---|---:|---:|---:|---:|---:|
| المواطن | لا | لا | لا | لا | لا |
| الطبيب | وفق حاجة العمل فقط | لا | لا | لا | لا |
| المختبري | لا، إلا ضمن workflow محدد | لا | حسب LIS contract | حسب LIS contract | لا |
| قاطع التذاكر | لا | لا | لا | لا | وفق ticket/payment scope فقط |
| مشغل التكامل | نعم ببيانات محدودة | لا | نعم لموصلات مخصصة | نعم لموصلات مخصصة | لا |
| مدقق أمني | metadata/audit فقط | لا | لا | لا | لا |
| مدير التكامل | نعم | نعم ضمن staging | نعم | نعم | لا |
| master admin | وفق break-glass موثق | وفق موافقة وتسجيل | وفق policy | وفق policy | لا يتجاوز فصل المهام |

يجب اختبار كل خلية تقريباً بحالات allow وdeny، مع حساب صحيح لكن tenant خاطئ، token منتهي، role صحيح بلا scope، وscope صحيح على workspace خاطئ.

## 11. الاختبارات الأمنية والتشغيلية

تنفذ اختبارات API وbrowser وload في ترتيب لا يسبب تلوثاً للبيانات. يبدأ الاختبار بـanonymous وwrong-role، ثم valid role، ثم cross-tenant، ثم provider failure. يجب التحقق من عدم وجود raw NID أو API key أو access token أو PHI في application logs، Sentry events، traces، audit details، cache keys، أو GitHub summaries.

يجب إجراء اختبار fault injection لكل موصل: DNS failure، TCP refusal، TLS mismatch، 401، 403، 404، 409 duplicate، 429، 5xx، slow response، malformed JSON، oversized response، replayed webhook، وresponse schema drift. يجب أن تكون النتيجة fail-closed أو `requires_verification=true`، لا success وهمياً.

ينفذ اختبار الضغط على بيانات اصطناعية فقط، مع قياس p50/p95/p99، error rate، queue depth، worker memory، Redis latency، PostgreSQL locks، external timeout، وعدد circuit opens. لا ينتقل أي traffic حقيقي إلى الموصلات الحكومية قبل قبول هذه المؤشرات من SRE ومالك التكامل.

## 12. المراقبة والتنبيهات

تنشأ dashboards منفصلة لـstaging تعرض عدد الطلبات، latency، status codes، circuit state، rate-limit rejects، TLS failures، schema validation failures، queue depth، وconnector availability. تمنع dashboards من عرض raw NID أو payloads. تُرسل تنبيهات عند:

| التنبيه | الإجراء |
|---|---|
| محاولة egress إلى host غير مسموح | إيقاف connector وفتح incident |
| ظهور `stub` أثناء shadow/live | فشل deployment gate |
| 401/403 غير متوقع من NID | تعليق الاختبار ومراجعة credential/scope |
| ارتفاع 429 | تخفيض المعدل ومراجعة contract |
| circuit OPEN | منع retry اليدوي العشوائي وفتح incident |
| schema drift | إيقاف قبول الاستجابة |
| raw secret/PII في logs | إيقاف التجربة، تدوير الأسرار، وفتح حادثة |
| cross-tenant denial failure | SAFE_STOP فوري |

## 13. خطة التراجع والإيقاف

يجب أن يكون التراجع قابلاً للتنفيذ خلال دقائق: ضبط `GULA_ADAPTER_MODE_NID=stub`، تعطيل feature flag، إلغاء connector route، سحب staging API key، إلغاء mTLS certificate، وحظر egress إلى endpoint. لا يُستخدم fallback لتصنيف الهوية على أنها verified. بعد التراجع تُحفظ الأدلة غير الحساسة، وتُمسح fixtures إذا كانت سياسة الاحتفاظ تقتضي ذلك، وتُراجع logs للتأكد من عدم وجود تسريب.

تُوقف التجربة فوراً عند فشل TLS verification، أو ظهور raw credentials/PII، أو نجاح cross-tenant request، أو قبول نتيجة provider malformed، أو downgrade غير مقصود إلى stub في اختبار live، أو استمرار Redis degraded fallback، أو فشل replay protection، أو وجود success وهمي عند connector unavailable.

## 14. معايير الخروج من SAFE_STOP

لا يكفي نجاح health checks. يجب استيفاء كل الشروط الآتية:

| الشرط | معيار القبول |
|---|---|
| عزل البيئة | لا يوجد مسار staging إلى production DB/Redis/secrets/buckets |
| الهوية | SHADOW ناجح، ثم LIVE sandbox محدود، مع contract evidence وتوقيع المالك |
| الأسرار | Vault audit وrotation وغياب الأسرار من logs/artifacts |
| TLS | certificate verification وmTLS عند الحاجة دون `verify=false` |
| Redis/PostgreSQL | outage وmulti-worker وrace وtenant matrix ناجحة |
| الصلاحيات | allow/deny matrix ناجحة، ولا توجد صلاحية عامة لمسار حكومي حساس |
| الموصلات | schema، retry، idempotency، replay، egress، delivery evidence ناجحة |
| الخصوصية | لا raw NID/PHI/token في logs أو traces أو summaries |
| التراجع | rollback drill ناجح وموثق |
| المراجعة | موافقة الأمن، مالك البيانات، مالك التكامل، ومالك التشغيل |

حتى بعد استيفاء هذه البنود، يكون الانتقال إلى production منفصلاً عن staging ويحتاج change approval وcanary وmonitoring وrollback. لا يُرفع `SAFE_STOP` تلقائياً من workflow.

## مراجع المشروع

[1]: `../../backend/app/gateways/national_identity_gateway.py` — أوضاع NID، المتطلبات، schema، وحدود الاستخدام السريري.

[2]: `../../backend/app/gateways/mode.py` — resolve_mode وسلوك downgrade عند غياب credentials.

[3]: `../../.github/workflows/staging-verify.yml` — workflow الحالي لفحص health/readiness/deep health.

[4]: `../../backend/app/gateways/base.py` — rate limit، circuit breaker، retry، validation، provenance، shadow mode، وclinical guard.

[5]: `COMPREHENSIVE_RISK_INVENTORY_AND_REMEDIATION_PLAN_AR.md` — سجل المخاطر وشروط SAFE_STOP.

[6]: `COMMAND06_LOCAL_CLOSURE_REPORT_AR.md` — نتائج الاختبارات المحلية وحدودها.
