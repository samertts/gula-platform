# تقرير تدقيق الأعطال والفجوات في منصة GULA

**التاريخ:** 19 أغسطس 2026

**المستودع:** `samertts/gula-platform`

**الفرع المفحوص:** `main`

**Commit المفحوص:** `deb7f04814a56d7892fe5fbbee56989882a529e5`

**المؤلف:** Manus AI

## 1. الخلاصة التنفيذية

أُجري تدقيق عملي متعدد الطبقات لمنصة GULA شمل كود Python/FastAPI، واجهات API، توليد OpenAPI، Alembic، اختبارات backend، واجهة React/TypeScript، اختبارات Playwright، بوابات CI، التبعيات، وتهيئة التشغيل. النتيجة ليست أن كل أجزاء النظام معطلة؛ بل إن هناك مجموعة من **الأعطال المؤكدة القابلة لإعادة الإنتاج**، إضافة إلى خدمات معلنة لكنها ما زالت Stub أو No-op، ومخاطر تشغيل وامتثال تمنع اعتبار المنصة جاهزة لبيانات صحية حقيقية.

أخطر نتيجة تقنية مؤكدة هي أن توليد `/openapi.json` يفشل بسبب مسار FHIR Bundle، ما يعطل وثيقة API والعملاء الذين يعتمدون على OpenAPI. كما أن مسارات Research تفشل عند التنفيذ بسبب غياب وحدة النماذج، وتعيد خدمات Clinical AI مخرجات Stub، بينما تعرض منصة البحث الوطني عمليات نجاح كاذب رغم أن بعض عمليات الفهرسة وإعادة البناء لا تنفذ شيئاً. وتوجد مشكلة عزل مؤسسات محتملة في نماذج البحث المحفوظ ونتائج البحث، وهي **حاجز أمني لا يجوز تجاوزه** قبل إدخال بيانات مؤسسات متعددة.

نجحت اختبارات backend الحالية، لكن هذا النجاح لا ينفي الأعطال أعلاه لأن الاختبارات الحالية لا تغطي توليد OpenAPI، بيئة PostgreSQL/Redis متعددة العمال، تدفقات Research الفعلية، حدود tenant isolation في البحث الوطني، أو تدفقات E2E المتصلة بـbackend حقيقي. كما نجحت اختبارات الوحدة وبناء الواجهة، لكن Playwright أثبت فشل اختبارين في شاشة الهاتف، وسجل E2E محاولات اتصال مرفوضة لأن workflow يشغل Vite فقط دون backend أو خدمة API اختبارية.

> **قرار السلامة المقترح:** لا تُطلق المنصة لبيانات صحية حقيقية أو قرارات علاجية آلية قبل إغلاق أعطال P0/P1 أدناه، وإجراء اختبار PostgreSQL وRedis وE2E متصل فعلياً بالbackend، ومراجعة بشرية للتغييرات السريرية والأمنية.

## 2. حدود التدقيق وطريقة التحقق

تم الاعتماد على الفحص الساكن، وتشغيل `compileall`، وفحص Alembic، وتشغيل مجموعة backend، وتشغيل pipeline الواجهة، وتشغيل Playwright بعد تثبيت متصفح Chromium، واختبارات startup وhealth وOpenAPI، وأدوات إعادة إنتاج صغيرة محفوظة مؤقتاً. عُدّت النتيجة **عطلاً مؤكداً** فقط إذا ظهر خطأ تنفيذي أو فشل اختبار أو كان التنفيذ في المصدر يعيد Stub/No-op لمسار HTTP معلن.

لم يُعتبر فشل GitHub Actions وحده دليلاً على سبب محدد، لأن بعض سجلات الوظائف لم تكن قابلة للاستخراج من GitHub CLI. لذلك يرد هذا التقرير بحالتين منفصلتين: فشل workflow مؤكد، وسبب جذري مؤكد عند توفر إعادة إنتاج محلية أو سجل مباشر. كما لم يُجرَ أي تعديل على كود المنتج خلال مرحلة التدقيق، باستثناء إنشاء أدوات تشخيص غير متتبعة وسجل التقرير.

## 3. مصفوفة الأعطال المؤكدة والأولوية

| المعرّف | الشدة | المجال | الحالة والأثر | الدليل المباشر | الإجراء المطلوب |
|---|---|---|---|---|---|
| F-01 | P0 | OpenAPI/FHIR | `GET /openapi.json` يفشل بـ`UnboundLocalError` أثناء توليد المخطط؛ وثيقة API والعملاء المولّدون متعطلون | المسار `/lims/orders/{order_id}/fhir-bundle` يحمل `response_class=FHIRJSONResponse` دون `status_code` رقمي، كما هو موثق في `backend/app/lims/routes.py` وسجل `scripts/trace_openapi_route_failure.py` | إضافة `status_code=200` أو عقد استجابة متوافق، ثم اختبار `/openapi.json` ووجود مسار FHIR في المخطط |
| F-02 | P1 | Research API | إنشاء Registry/Cohort يفشل عند التنفيذ بسبب `ImportError` لوحدة `app.clinical.research.models` المفقودة؛ القوائم ليست تنفيذاً صالحاً | إعادة الإنتاج في `/tmp/gula_research_repro_test3.txt`؛ `backend/app/clinical/research/__init__.py` لا يصدّر `models` | إنشاء نماذج SQLAlchemy وهجراتها ومستودعاتها، أو تعطيل المسارات بوضوح؛ إضافة اختبارات POST/GET مع tenant scoping |
| F-03 | P1 | Clinical AI | مسارات `/ai/copilot` و`/ai/risk-prediction` و`/ai/care-gaps` و`/ai/diagnostic-assistant` و`/ai/explain` تعيد Stub أو نتائج فارغة/غير معروفة | `ClinicalAIService` في `backend/app/services/clinical_service.py` يعيد `status: stub` ورسائل placeholder | تعطيل المسارات أو وسمها صراحةً كتجريبية، وإضافة `advisory_only: true` باستمرار؛ لا تُفتح سريرياً قبل نموذج معتمد واختبارات أمان |
| F-04 | P1 أمن/خصوصية | Clinical AI care gaps | `detect_care_gaps` يقرأ توصيات نشطة دون ربط واضح بالمريض أو المؤسسة ثم يعيدها لمسار API | `backend/app/services/clinical_service.py` و`backend/app/routes/clinical.py` | فرض patient/tenant filters، اختبارات cross-tenant، وتسجيل رفض أي سياق ناقص |
| F-05 | P1 | National Search | `get_facets()` يعيد قائمة فارغة، و`index_document()` و`remove_document()` عمليات No-op، و`rebuild_index()` يعيد 0 دون إعادة بناء | `backend/app/national/search_platform/application/interfaces.py` و`infrastructure/repository.py` | إما تنفيذ adapter حقيقي مع نتائج قابلة للتحقق، أو إزالة المسارات من واجهة الإنتاج وإرجاع 501/503 صريح بدلاً من نجاح كاذب |
| F-06 | P1 أمن/عزل | National Search | مستودعات SavedSearch/SearchResult والنماذج المقابلة لا تحمل `lab_id`/tenant scope؛ الاستعلامات والإحصاءات عالمية | `backend/app/national/search_platform/infrastructure/models.py` و`repository.py` و`backend/app/national/base.py` | إضافة tenant key وفهارس مركبة، تمرير السياق في كل repository method، واختبارات عزل مؤسستين |
| F-07 | P1 | Frontend Mobile | اختبارا Playwright عند 320px و390px يفشلان لأن محدد `فتح جميع الأقسام` يطابق زرين | `DashboardLayout.tsx` و`MobileBottomNav.tsx` يعرّفان نفس الاسم الوصولي؛ النتيجة 51 ناجحة و2 فاشلة | إبقاء زر واحد أو إعطاء كل زر اسماً وصولياً ودوراً مختلفين، ثم إضافة اختبار تركيب layout كامل |
| F-08 | P1 | Frontend E2E/CI | workflow E2E يشغل Vite preview ولا يشغل backend أو seed fixtures أو mock API؛ ظهرت `ECONNREFUSED` في طلبات الواجهة | `.github/workflows/frontend-e2e.yml` وسجل Playwright المحلي | تشغيل backend test stack مع Postgres/Redis أو mock API معزول، الانتظار على health endpoint، وإتاحة بيانات اختبار غير حقيقية |
| F-09 | P1 | CI gating | فشل التنسيق قد لا يوقف pipeline لأن workflow يستخدم `|| echo`؛ هذا يخلق نجاحاً ظاهرياً | `.github/workflows/formatting.yml`؛ Prettier وجد 173 ملفاً، وRuff format وجد 1008 ملفات تحتاج إعادة تنسيق | إزالة `|| echo`، استعمال `prettier --check` و`ruff format --check` على نطاقات محددة، ثم إصلاح الانحراف في PR مستقل |
| F-10 | P2 | OpenAPI contract | تحذير Duplicate Operation ID للمعرّف `change_password_auth_change_password_post` يجعل العملاء المولّدين عرضة للغموض | تحذير FastAPI في `password_reset.py` | تحديد `operation_id` فريد، والتحقق آلياً من uniqueness في CI |
| F-11 | P2 | Runtime dependencies | بدون `DATABASE_URL` يبدأ التطبيق بقاعدة محلية افتراضية، ويفشل sync الحوكمة عند غياب PostgreSQL | سجل startup في `/tmp/gula_openapi_failed_route.txt` يظهر `connection refused` على localhost:5432 | منع أي وضع يشبه الإنتاج من استخدام default محلي، وتشغيل smoke test بقاعدة PostgreSQL حقيقية |
| F-12 | P1 | Runtime security | غياب `SECRET_KEY` و`REFRESH_TOKEN_SECRET` و`ENCRYPTION_KEY` و`NID_HMAC_KEY` و`AUDIT_ANCHOR_KEY` يؤدي إلى مفاتيح عشوائية أو وضع غير صالح للاستمرارية | سجلات startup و`backend/app/core/startup_guard.py` | جعل التحقق fail-closed قبل تشغيل أي instance إنتاجي، وإدارة الأسرار عبر secret manager واختبار rotation |
| F-13 | P1 | Runtime consistency | غياب `REDIS_URL` يحول rate limiting، إبطال الجلسات، وtask queue إلى in-memory غير مشترك بين العمال | سجل startup يذكر in-memory fallback صراحةً | منع multi-worker production بدون Redis، واختبار idempotency/rate-limit/session invalidation عبر عاملين أو أكثر |
| F-14 | P1 سريري | AI governance | مزود AI غير مهيأ يؤدي إلى Stub mode، وبعض مخرجات Clinical AI لا تحمل باستمرار `advisory_only=true` | سجلات startup و`clinical_service.py` و`clinical.py` | إما تعطيل المسارات، أو فرض schema موحد يرفض أي نتيجة دون advisory marker، ومنع أي treatment action تلقائي |
| F-15 | P1 | Financial Engine | عند غياب prerequisites/configuration يسجل النظام `Financial Engine disabled — routes not registered`؛ أي أن الوظيفة غير متاحة في تلك البيئة | سجل startup | تحديد هل التعطيل مقصود، وإظهاره في capability registry، وإضافة health/readiness signal بدلاً من ترك الواجهة توحي بأن الخدمة متاحة |
| F-16 | P2 | FHIR completeness | مرجع FHIR يعلن `Procedure` و`Bundle` بحالة `stub`؛ وجود مسار Bundle لا يثبت اكتمال التصدير المعياري | `backend/app/fhir/_reference.py` و`backend/app/lims/routes.py` | تحديد موارد FHIR المدعومة رسمياً، عقد Bundle وvalidation، واختبارات round-trip وFHIR validator |
| F-17 | P2 | Search adapters | Elasticsearch وFHIR Search adapters تعيد نتائج/عدادات فارغة وتبلغ عن `status: stub` | `backend/app/national/search_platform/application/interfaces.py` | عدم تسجيلها كجاهزة، وإرجاع حالة unavailable/501 أو تنفيذ adapters مع contract tests |
| F-18 | P2 | Local audit tooling | أداة flake8 غير موجودة محلياً؛ هذا ليس عطل منتج مؤكداً لكنه يجعل نتيجة التدقيق المحلي غير مكافئة لـCI | `/tmp/gula_flake8.txt` | توحيد الأدوات في `requirements-dev` أو حاوية CI قابلة للتشغيل محلياً |
| F-19 | P2 | Pydantic compatibility | تحذير deprecation حول `Field` وextra keyword `finite` في `backend/app/devices/schemas.py:513` | ملخص pytest: 253 تحذيراً، ومنه تحذير Pydantic المذكور | نقل التحقق إلى validator/constraint مدعوم في الإصدار الحالي وإضافة اختبار schema |
| F-20 | P2 | CI observability | تشغيلات GitHub على commit/تاريخ main أظهرت فشل عدة workflows، لكن سجلات بعض الوظائف غير متاحة عبر CLI؛ سبب الجذر غير مثبت لكل workflow | `gh run list` وملفات `/tmp/gula_*runs*` | مراجعة السجلات من واجهة مالك المستودع، ثم فصل أخطاء بنية workflow عن أخطاء الكود قبل أي إصلاح شامل |

## 4. وظائف موجودة في الواجهة لكنها ليست جاهزة فعلياً

توجد واجهات أو capability pages لا يكفي ظهورها في الـfrontend لإثبات أن backend المقابل يعمل. جرد الإنتاج أظهر حالات `status: stub` في Clinical AI والبحث الوطني والتصدير منزوعة التعريف، إضافة إلى مراجع FHIR غير المكتملة. كما توجد `NotImplementedError` داخل classes مجردة وواجهات repositories؛ هذه لا تُعد أعطالاً مستقلة إذا لم تُستدعَ مباشرة، لكنها تصبح أعطالاً عند تسجيل implementation ناقص كـadapter إنتاجي.

| الوظيفة | حالتها الحالية | قرار الإطلاق |
|---|---|---|
| تصدير dataset منزوع التعريف | Stub يعيد حجمًا غير معروف ولا ينشئ artifact | ممنوع الإنتاج حتى تنفيذ de-identification وconsent وaudit |
| Clinical Copilot/Risk/Diagnostic Assistant | Stub أو نتائج placeholder | تعطيل أو simulation-only مع advisory-only إلزامي |
| National Search indexing/facets/rebuild | No-op/نجاح كاذب | إرجاع 501/503 أو تنفيذ فعلي |
| Elasticsearch/FHIR Search | Adapter stub | غير جاهز |
| Research registry/cohort | نماذج ومسارات ناقصة | غير جاهز |
| FHIR Procedure/Bundle reference | حالة stub | غير جاهز كادعاء توافق شامل |
| Chronic-care package | منطق داخلي بلا router مستقل | مقبول فقط إذا كان العقد المعتمد هو wearable baseline؛ غير مقبول إذا وعدت الواجهة بواجهة chronic-care مستقلة |

## 5. ما نجح، وما لا ينبغي تفسيره كجاهزية إنتاجية

| الفحص | النتيجة | التفسير الصحيح |
|---|---|---|
| Python compile | ناجح | لا توجد أخطاء syntax في الملفات التي فُحصت؛ لا يثبت صحة التشغيل أو التكامل |
| Alembic heads | رأس واحد | السلسلة متماسكة؛ لا يثبت نجاح migration على PostgreSQL حقيقي |
| Backend pytest | 2683 ناجحة، 4 متجاوزة، 253 تحذيراً | baseline جيد للوحدات، لكنه لا يغطي كل API/runtime/E2E |
| Frontend typecheck/unit/governance/build | ناجح؛ 16 ملف اختبار و55 اختباراً، والبناء ناجح | الواجهة قابلة للبناء؛ لا يلغي فشل Playwright على layout الكامل أو اتصال API |
| Playwright | 51 ناجحة و2 فاشلة | يوجد عطل وصولية/تركيب مؤكد في mobile |
| npm audit/pip-audit السابق | لم تظهر ثغرات محلية في القوائم المفحوصة | لا يغلق تنبيهات GitHub أو يثبت سلامة كل صور Docker وActions |
| Git status | `HEAD` مطابق لـ`origin/main`، لكن توجد ملفات غير متتبعة | لم تُدفع إصلاحات جديدة في هذه الجولة؛ يجب تنظيف artifacts قبل أي commit |

## 6. ترتيب الإصلاح الموصى به

### المرحلة الأولى: حواجز P0 قبل أي تشغيل سريري

يجب إصلاح F-01 أولاً بإضافة status code صريح لمسار FHIR Bundle ثم إضافة اختبار يطلب `/openapi.json` ويتحقق من أن schema يحتوي المسار. بعد ذلك يجب تعطيل أو حماية مسارات F-02 وF-03 وF-05 التي تعيد Stub أو نجاحاً كاذباً؛ لا يكفي تغيير الرسالة، بل يجب أن يكون رد الخدمة صريحاً مثل `501 Not Implemented` أو `503 Service Unavailable` إذا كانت غير جاهزة.

يجب أيضاً معالجة F-04 وF-06 قبل استخدام بيانات مؤسسات متعددة. أي endpoint يعيد نتائج سريرية أو بحثية يجب أن يتطلب سياق المؤسسة والمستخدم والمريض عند الحاجة، ويجب أن يرفض السياق الناقص بدلاً من القراءة العامة. ينبغي إضافة اختبارات مؤسستين مع كائنات متشابهة لإثبات عدم التسرب.

### المرحلة الثانية: إصلاح بوابات الواجهة والتكامل

يُعالج F-07 بتوحيد زر فتح الأقسام في mobile shell، ثم يُعاد تشغيل اختباري 320px و390px. ويُعالج F-08 بإعادة تصميم workflow كي يطلق خدمة API تجريبية حقيقية أو mock contract service، وينتظر `/health/ready` قبل Playwright. يجب أن تكون بيانات E2E اصطناعية، وأن تفشل الاختبارات إذا كان backend غير متاح، لا أن تمر بسبب فشل الشبكة الصامت أو fallback غير معلن.

بعد ذلك تُصلح F-09 في PR مستقل للتنسيق. يجب عدم إعادة تنسيق المستودع كله بلا حدود؛ يُحدد النطاق، ويُسجل عدد الملفات، ويُنفذ formatter مثبت الإصدار، ثم تُزال أوامر إخفاء الفشل من workflow.

### المرحلة الثالثة: جاهزية التشغيل والأمن

يجب اختبار startup في بيئة قريبة من الإنتاج باستخدام PostgreSQL وRedis فعليين، مع secrets تجريبية تُدار خارج المستودع. ينبغي أن يفشل التطبيق قبل قبول الطلبات إذا غاب مفتاح تشفير أو مفتاح جلسات أو Redis المطلوب، وأن تظهر حالة readiness صريحة للخدمات المعطلة. كما يجب اختبار restart وrotation وmulti-worker وidempotency، لا الاكتفاء بتشغيل worker واحد.

### المرحلة الرابعة: إكمال الخدمات أو تقليص الوعود

الخدمات التي لا يوجد لها تنفيذ حقيقي يجب أن تتبع أحد قرارين: تنفيذها مع عقود واختبارات وسجل تدقيق، أو إزالتها من capability registry والواجهة الإنتاجية وإظهارها كـsimulation-only. إبقاء صفحة تبدو جاهزة بينما API يعيد Stub أخطر من إخفاء الوظيفة، لأنه يخلق ثقة زائفة لدى المستخدم السريري.

## 7. خطة اختبار الإغلاق

لا يُغلق أي بند من البنود الحرجة إلا بعد تحقق مستقل من الحالة التالية:

| الحاجز | معيار الإغلاق |
|---|---|
| OpenAPI | `GET /openapi.json` يجيب 200، schema صالح، ولا توجد operation IDs مكررة |
| Research | POST/GET يعملان على PostgreSQL، مع persistence، authorization، وtenant isolation مثبتين باختبارات مؤسستين |
| Clinical AI | لا توجد نتائج علاجية آلية؛ كل رد يحمل `advisory_only=true`، والمسارات غير الجاهزة 501/503 أو غير مسجلة |
| National Search | عمليات index/rebuild/facets إما تعمل فعلياً ببيانات اختبار أو ترفض صراحةً؛ لا توجد false success |
| E2E | Playwright يشغل frontend وbackend وقاعدة بيانات اختبارية، وتنجح سيناريوهات الهاتف وauth والقراءة/الكتابة الأساسية |
| Runtime | startup مع Postgres وRedis وsecrets ثابتة، readiness صحيح، واختبار multi-worker ينجح |
| CI | فشل formatting/security/typecheck/test يمنع الدمج، ولا توجد `|| echo` تخفي فشل بوابة إلزامية |
| Release hygiene | لا توجد أدوات تدقيق أو `test-results` غير مقصودة في commit؛ كل تقرير أو script له قرار تتبع واضح |

## 8. الملفات غير المتتبعة الناتجة عن التدقيق

حالة Git عند نهاية التدقيق نظيفة من ناحية الملفات المتتبعة، لكنها تحتوي ملفات غير متتبعة: `docs/DEPENDABOT_REMEDIATION_RUNBOOK_AR.md`، و`docs/TRANSITIVE_DEPENDENCY_PREVENTION_GUIDE_AR.md`، ومجلد `frontend-v3/test-results/`، وأدوات التشخيص تحت `scripts/audit_*` و`scripts/repro_*` و`scripts/trace_*`. لم تُدفع هذه الملفات ولم تُعتبر إصلاحات للمنتج. يجب على مالك المستودع اختيار ما إذا كانت الوثائق والأدوات ستُحفظ في المستودع، مع استبعاد `test-results` وملفات البيئة والنواتج المؤقتة من الإصدار عادةً.

## 9. الخلاصة النهائية

النظام قابل للبناء، ويمتلك قاعدة اختبارات جيدة لبعض الوحدات، لكن التدقيق أثبت أن عدة عقود عامة لا تعمل فعلياً وأن بعض الخدمات تعرض نجاحاً أو قدرة لا يقابلها تنفيذ حقيقي. أهم العوائق قبل staging السريري هي: إصلاح OpenAPI/FHIR، إيقاف أو إكمال Research وClinical AI وNational Search، فرض tenant isolation، إصلاح E2E المتصل بالbackend، إزالة إخفاء فشل CI، وتشغيل اختبار إنتاجي مكافئ باستخدام PostgreSQL وRedis والأسرار المدارة.

بناءً على الأدلة الحالية، تصنيف المنصة المناسب هو **جاهزة للتطوير والاختبار الداخلي المحدود، وغير جاهزة لإطلاق بيانات صحية حقيقية أو استخدام سريري تشغيلي**. هذا التصنيف محافظ ومقصود؛ نجاح اختبارات الوحدات لا يعوض فشل المسارات العامة أو غياب عزل البيانات أو تشغيل الخدمات في Stub mode.

## المراجع والأدلة

[1]: `backend/app/lims/routes.py` — مسار FHIR Bundle و`FHIRJSONResponse`.

[2]: `backend/app/services/clinical_service.py` — ResearchService وClinicalAIService وstubs.

[3]: `backend/app/routes/clinical.py` — مسارات Research وClinical AI والتصدير.

[4]: `backend/app/national/search_platform/application/interfaces.py` — adapters وعمليات البحث No-op.

[5]: `backend/app/national/search_platform/infrastructure/models.py` و`repository.py` — نماذج ومستودعات البحث المحفوظ ونتائج البحث.

[6]: `frontend-v3/src/layouts/DashboardLayout.tsx` و`frontend-v3/src/components/navigation/MobileBottomNav.tsx` — الزران المتطابقان في mobile shell.

[7]: `.github/workflows/frontend-e2e.yml` و`.github/workflows/formatting.yml` — تهيئة E2E وبوابات التنسيق.

[8]: `/tmp/gula_audit_working.md` — سجل الأدلة المركزي الناتج من التدقيق المحلي.

[9]: `/tmp/gula_openapi_failed_route.txt` — إعادة إنتاج فشل OpenAPI وسجل startup.

[10]: `/tmp/gula_research_repro_test3.txt` — إعادة إنتاج ImportError في ResearchService.

[11]: `/tmp/gula_frontend_check.txt` و`/tmp/gula_frontend_e2e_real.txt` — نتائج فحوصات الواجهة وPlaywright.

[12]: `/tmp/gula_stubs_final.txt` — جرد stubs وNotImplemented في كود الإنتاج.

[13]: `https://github.com/samertts/gula-platform/actions` — تشغيلات GitHub Actions للمستودع، وتحتاج صلاحية مالك/مشرف لقراءة بعض سجلات الوظائف.

[14]: `https://fastapi.tiangolo.com/advanced/response-change-status-code/` — توثيق FastAPI المتعلق بتحديد status code والاستجابات.

[15]: `https://owasp.org/www-project-api-security/` — مرجع OWASP لأمن واجهات API، بما في ذلك التفويض والعزل والتحقق.

[16]: `https://www.hl7.org/fhir/` — المرجع الرسمي لمواصفات FHIR عند إكمال Bundle وموارد FHIR.

## ملاحظة منهجية

هذا التقرير يثبت ما أمكن تشغيله أو ربطه مباشرةً بالمصدر. عبارة «اكتشاف كل ما لا يعمل» لا يمكن ضمانها حرفياً دون تشغيل بيئة الإنتاج الحقيقية، وقاعدة البيانات الفعلية، Redis متعدد العمال، كل مزودي التكامل، وكل workflows بصلاحيات مالك المستودع. لذلك فالقائمة الحالية هي **أعطال مؤكدة وفجوات عالية الاحتمال موثقة**، وليست شهادة خلو من عيوب إضافية.
