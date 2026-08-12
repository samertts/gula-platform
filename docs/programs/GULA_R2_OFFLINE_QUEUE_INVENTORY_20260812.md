# GULA R2 Offline Queue Inventory — 2026-08-12

## Purpose and safety boundary

تهدف موجة R2 إلى إزالة أي access/refresh token أو Authorization header من الطوابير غير المتصلة القديمة، ومنع إعادة تشغيل سجل موروث خارج جلسة HttpOnly الحالية. لا تسمح هذه الموجة بحذف البيانات السريرية أو المسودات أو cache لمجرد التبسيط، ولا تغيّر deployment أو الفروع أو release. أي سجل يحتوي credential لا يُعاد إرساله؛ تُنظف حقول الاعتماد أو يُحذف سجل الطلب نفسه إذا لم يمكن فصله بأمان عن payload.

## Confirmed queue surfaces

| التطبيق | مخزن/مسار | نوع السجل | الخطر المؤكد | قرار R2 |
|---|---|---|---|---|
| Citizen | `gula-citizen-offline.requests` | request + headers + body | قاعدة التطبيق القديمة قد تحتوي Authorization، وservice worker القديم يخزن headers في `gula-offline`/`gula-offline-queue` | تنظيف headers، إعادة الإرسال بـcredentials فقط، حذف/تجاهل legacy SW records، وترقية DB دون مسح clinical stores |
| Doctor | `gula-doctor-offline.requests` | request + headers + body | records أنشئت قبل R1، و`public/sw.js` يخزن queue في Cache Storage مع headers ويعيد replay | purge/redaction للـIndexedDB، إزالة SW queue/cache legacy، وsession-cookie replay فقط |
| Doctor | `gula-doctor-offline-sync.pending` | generic pending payload | مسار ثانٍ غير موحد مع API queue | لا يُعاد تشغيل record غير موثوق؛ تنظيف auth-bearing payloads مع إبقاء records الآمنة فقط |
| Laboratory | `gula-lab-cache.requests` | request + headers + body | API queue القديمة | purge/redaction وإعادة التشغيل بـcredentials فقط |
| Laboratory | `gula-lab-offline.requests` | request + body | OfflineContext duplicate queue | ترقية/تنظيف requests القديمة دون حذف cache، وإضافة credentials في replay |
| Laboratory | `gula-lab-offline-store.pending` | generic pending payload | `syncAll` يعيد body بلا session credentials | sanitizer، credentials، ورفض payload auth-bearing؛ إبقاء drafts وcache |
| Nurse | `gula-nurse-offline.queue` | domain payload only | لا توجد headers في النوع الحالي، لكن payload غير مقيد وقد يحمل fields موروثة | schema scrub للحقول الحساسة في payload؛ لا تُمسح cache |
| Pharmacy | `gula-pharmacy-offline.pending_dispenses` | generic dispense payload | generic record قد يحتوي fields حساسة، ولا يوجد session-bound scrub | scrub للحقول الحساسة في pending records؛ لا تُمسح inventory/prescriptions/patients |
| Pharmacy | `public/service-worker.js` | GET cache only | لا يوجد mutation replay أو IndexedDB queue | لا تغيير وظيفي مطلوب في هذا المسار |
| Workbox configs | citizen/doctor/hospital/laboratory/ministry/nurse | generated Background Sync | قواعد API عامة قد تنشئ queues غير مرئية للـapplication clients، وقد تعيد request خارج session contract | تعطيل Background Sync العام لمسارات API في R2؛ الإبقاء على queues التطبيقية المراجعة فقط |

## R2 invariants

1. لا يُخزّن أي `Authorization`, `authorization`, `Bearer`, `access_token`, `refresh_token`, `id_token`, `jwt`, أو password/secret داخل queue record أو replay headers.
2. كل replay متبقٍ يستخدم `credentials: 'include'`، ولا يحمل token body أو Authorization header.
3. سجل الطلب الذي يحتوي credential في header يُحذف أو يُنقل إلى حالة رفض محلية؛ لا يُعاد إرساله بعد إزالة header إذا كان body غير قابل للتحقق.
4. تنظيف R2 يكون idempotent، ويُنفذ عند فتح قاعدة البيانات أو قبل أول sync، ولا يحذف stores الخاصة بالمسودات أو cache أو clinical data.
5. Service Worker القديم الذي يخزن queue في Cache Storage أو IndexedDB لا يُسمح له بالاستمرار في replay؛ upgrade/activate يمسح queue names المعروفة ويترك static/API GET caches وفق حدودها.
6. فشل cleanup لا يتحول إلى نجاح صامت: sync يتوقف أو يرفض record ويحتفظ بحالة خطأ قابلة للمراجعة.

## Evidence to collect

سيُشغّل R2 اختبارات sanitizer وmigration على records تحتوي headers حساسة وpayloads آمنة، ثم typecheck/build للتطبيقات المتأثرة، وBackend full suite للتأكد من عدم وجود regression. ستوثق النتيجة أعداد السجلات المنظفة أو المرفوضة في اختبارات deterministic، دون ادعاء معرفة محتوى IndexedDB الحقيقي لدى مستخدمين لم تُفتح متصفحاتهم.

## R2 implementation evidence — 2026-08-12

تم تنفيذ الحماية على queues الخاصة بـCitizen وDoctor وLaboratory وNurse وPharmacy، وإزالة مسارات replay من Citizen وDoctor service workers، وتعطيل Workbox Background Sync العام في Citizen وDoctor وHospital وLaboratory وMinistry وNurse. أضيفت دالة purge لقاعدة Workbox `workbox-background-sync` عند startup للتطبيقات الستة، كما رُفعت إصدارات IndexedDB ذات الصلة وأضيفت stores `queue_rejections` لتسجيل السجلات المرفوضة محلياً دون إعادة إرسالها.

| الفحص | النتيجة | الملاحظات |
|---|---|---|
| اختبار `offlineQueueSecurity` | **passed** | يغطي Authorization/refresh token/Bearer، payload JSON، والتمييز بين `secretaryName` والحقل السري الحقيقي |
| TypeScript helper check | **passed** | direct no-emit على `platform/ui/utils/offlineQueueSecurity.ts` باستخدام TypeScript 5.9.3 |
| Vite build | **passed** | citizen وdoctor وhospital وlaboratory وpharmacy |
| Nurse Vite build | **R2 code transformed successfully** | توقف بعد 705 modules بسبب 11 default exports مفقودة في صفحات Nurse الموجودة قبل R2، وليس بسبب sanitizer أو queue import |
| Ministry Vite build | **blocked سابقاً** | `statisticsService` و`surveillanceService` exports مفقودة في services الحالية |
| Radiology Vite build | **blocked سابقاً** | `src/styles/theme.css` و`src/styles/components.css` غير موجودين |
| TypeScript project checks | **blocked بيئياً/إعدادياً** | TypeScript 7 يرفض `baseUrl` legacy، وبعض التطبيقات تشير إلى UI project غير composite؛ لم تُعدّل هذه الإعدادات العامة ضمن R2 |
| Backend full suite | **2305 passed** | 251 warnings، لا regression في Wave 3/C1/C2 |
| Static scan | **pass with reviewed sanitized references** | لا Background Sync config ولا worker replay ولا local token persistence؛ المراجع الثلاثة التي تكتب `headers` تحفظ فقط ناتج sanitizer بعد إزالة الحقول الحساسة |

### Data-preservation boundary

يحافظ cleanup على `cache` و`drafts` وclinical stores. يستهدف فقط request/pending queue stores، وينقل metadata الخاصة بالسجل المرفوض إلى `queue_rejections` أو `sync_log` دون الاحتفاظ بقيمة credential نفسها. لا يمكن لهذا التغيير وحده معرفة أو تنظيف IndexedDB في متصفح لم يفتح النسخة الجديدة من التطبيق؛ لذلك يوجد startup purge للـWorkbox DB وترقية lazy عند أول فتح لكل application DB.

## Known follow-up work

تحتاج R3 إلى توحيد queue contract بين التطبيقين وservice workers وإضافة conflict/idempotency semantics موحدة للعمليات السريرية. كما يجب إصلاح exports المفقودة وملفات CSS في التطبيقات المتوقفة قبل اعتماد build شامل. لا تزال مراجعة Dependabot والـdefault branch ودمج Wave 3 خارج R2 وتحتاج اعتماداً مستقلاً.
