# تقرير المراجعة الخارجية وإصلاحات Phase 10-B

## نطاق التنفيذ

تمت مراجعة الشيفرة الفعلية في `gula-platform`، وليس تقارير سابقة فقط، مع التركيز على canonical clinical read gateway، frontend-v3، حدود التكامل، العقود، الواجهة المتجاوبة، dark mode، والأدلة الآلية. بقيت قاعدة أساسية سارية: لا merge ولا deployment ولا تفعيل rollout سريري تلقائي.

## إصلاحات مؤكدة

| المجال | المشكلة المثبتة | المعالجة |
|---|---|---|
| Fixtures التفويض السريري | اختبارات قديمة لم توفر `niam_organization_id` و`niam_facility_id` بعد جعل reviewed mapping شرطًا للقراءة | تحديث fixtures لتثبت mapping المراجع، مع بقاء غياب mapping محجوبًا آمنًا |
| Refresh session test | الاختبار مرر raw JTI بينما الخدمة تقبل refresh JWT وتفككه | عزل decode/blacklist في الاختبار وتمرير token contract صالح |
| Kernel observability test | `get_kernel_health()` يقرأ integration singleton مختلفًا عن Kernel الذي أنشأه الاختبار | ربط instance بالـintegration singleton عبر monkeypatch مع عزل الحالة |
| Transport failures | ECONNREFUSED وHTTP 4xx/5xx غير المترجمة كانت تظهر كخطأ نقل خام في صفحات القراءة | تحويل network/429/server errors إلى `WorkspaceReadBlockedError(service_unavailable)`؛ لا يوجد fallback إلى REST legacy |
| Responsive header/sidebar | overflow مثبت عند 320px و768px بسبب ازدحام header وdesktop sidebar قبل توفر العرض | تخفيف controls غير الفعالة تحت 640px، واعتماد `lg` للـdesktop sidebar/header profile، مع بقاء drawer للهاتف واللوحي |
| Dark mode | `src/styles/index.css` المستورد فعليًا كان يعرّف `@theme inline` دون semantic light/dark tokens | إضافة palette رمادية مزرقة متسقة للـbackground/card/foreground/border/sidebar/chart مع contrast واضح، دون استخدام أسود كامل كخلفية أساسية |
| Governance verifiers | ضوابط التوحيد والعقود وحدود التكامل ما زالت تبحث عن `authz/me` و`authz/check` وcolon permissions القديمة | تحديث الضوابط لتثبت canonical gateway paths، versioned envelope، `WorkspaceReadBlockedError`، وحظر legacy fallback |
| Contract registry | سجل العقود كان يربط `patients.read` و`orders.read` بالمسارات legacy والصلاحيات colon | تحديثه إلى `/api/v1/clinical/patients` و`/api/v1/clinical/orders` و`patients.read`/`orders.read` ومصدر gateway الفعلي |

## أدلة الاختبار

نجح backend non-integration suite في **2497 اختبارًا** مع **41 اختبارًا مستبعدًا** باعتبارها integration. نجحت اختبارات إصلاح baseline المستهدفة وعددها **7 اختبارات**، كما نجحت Ruff على ملفات الاختبارات المعدلة.

نجحت frontend unit tests في **42 اختبارًا**، وTypeScript typecheck، وESLint، وproduction build. نجح `npm run check` كاملًا، ويشمل اختبارات الوحدة، lint، ضوابط التوحيد والعقود وحدود التكامل، جرد مصادر البيانات، route gate، audit artifacts، ثم build.

نجح frontend E2E في **48 اختبارًا**، ويشمل login/navigation/FHIR/safe-empty surfaces، canonical patients/orders blocked state، واتجاه RTL وعدم overflow على العروض `320، 360، 375، 390، 412، 768، 1024، 1280، 1440`. أضيف regression مستقل يثبت dark mode عند 390px:

| الفحص | النتيجة المثبتة |
|---|---|
| dark class | موجود على `html` |
| RTL | `dir="rtl"` |
| dark background | `rgb(16, 32, 43)` |
| dark foreground | `rgb(230, 240, 244)` |
| horizontal overflow | غير موجود |

كما نجحت governance gates في توثيق **88 سطح بيانات**، وتوليد خريطة **83 مدخل مسار**، والتحقق من **309 مسارًا خلفيًا** و83 مدخل واجهة وسبعة مجالات وقرارات البوابة والتفويض والتكامل.

## حدود التفعيل

تظل P1/P2/P3 التنفيذية محجوبة حتى تصبح سلسلة P0 مقبولة بالمراجعة البشرية؛ PRs الخاصة بـP0 ما زالت مفتوحة. لم تُفتح `results.read` أو `samples.read` أو `reports.read` كقراءات canonical عامة، ولم تُفتح أي كتابة أو اعتماد نتائج. بقي `GULA_CLINICAL_GATEWAY_MODE=OFF` هو الوضع الافتراضي، ولم تُنشأ role assignments أو reviewed mappings تلقائيًا.

وجود legacy endpoints في backend لا يعني أنها canonical أو مسموحة للواجهة؛ frontend-v3 يستخدم مساري gateway فقط، ويحوّل عدم توفر الخادم أو فشل العقد إلى safe blocked state.

## عناصر تحتاج قرارًا بشريًا

| العنصر | الحالة |
|---|---|
| قبول ومراجعة سلسلة P0 | REVIEW_REQUIRED |
| تعبئة NIAM↔operational reviewed mappings | GOVERNED_PROCESS_REQUIRED |
| تفعيل rollout الداخلي أو التجريبي | HUMAN_APPROVAL_REQUIRED؛ لا تفعيل تلقائي |
| contracts لـresults/samples/reports | CONTRACT_REVIEW_REQUIRED |
| write governance وstate machines وidempotency | DEFERRED حتى اكتمال P0/P1/P2 |
| RPO/RTO والاحتفاظ القانوني | DECISION_REQUIRED / LEGAL_REVIEW_REQUIRED |

## نتيجة المراجعة

الإصلاحات المؤكدة في نطاق المراجعة الخارجية جاهزة لفرع مستقل وPull Request مستقل. لا يوجد في هذه الدفعة ادعاء امتثال تنظيمي أو اعتماد حكومي أو موافقة من وزارة الصحة، ولا يوجد deployment أو merge تلقائي.
