# GULA R3 — Queue Contract and Build Error Inventory

**التاريخ:** 2026-08-12

## الهدف وحدود السلامة

تهدف R3 إلى توحيد envelope الخاص بالعمليات غير المتصلة، وإضافة مفاتيح idempotency ومرجع version/conflict دون تخزين credentials أو تجاوز validation/audit/state machine في backend. لا تدمج هذه الموجة نماذج `User` و`LabUser`، ولا تُنفذ backfill أو dual-write أو تغيير deployment، ولا تحذف clinical caches أو drafts.

## الحالة الحالية للـqueues

| التطبيق | المخزن/المسار | الحالة الحالية | فجوة R3 |
|---|---|---|---|
| Citizen | `gula-citizen-offline.requests` | request URL/method/headers/body/retry metadata | لا يوجد envelope موحد أو idempotency key أو expected version |
| Doctor | `gula-doctor-offline` داخل API + `gula-doctor-offline-sync.pending` | مساران مختلفان للطلبات والعناصر المعلقة | لا يوجد contract موحد، ومسار API replay لا يربط mutation بـconflict semantics |
| Laboratory | `gula-lab-offline-queue` داخل API + `gula-lab-offline-store.pending` + `OfflineContext` | ثلاثة مسارات متوازية؛ أحدها يحفظ `entityType/entityId/action` والآخر لا يحفظها | خطر اختلاف retry/result/conflict behavior بين المسارات |
| Nurse | `gula-nurse-offline.queue` | `id/type/action/payload/createdAt/synced` | ينقصه request fingerprint وexpected version وconflict status/reason |
| Pharmacy | `gula-pharmacy-offline.pending_dispenses` | dispense payload مع status/timestamps | لا يوجد idempotency key أو expected version أو conflict result؛ لا تُمسح caches السريرية |
| Workbox SW | queues مولدة سابقاً | تم تعطيل config العام في R2 | يجب أن يبقى purge للـ`workbox-background-sync` فقط، دون حذف application caches |

## Backend contract الموجود

يملك backend حالياً idempotency جزئياً في `order_service.create_order` عبر Redis key، كما توجد معالجة `Idempotency-Key` لمسار النتائج وworkflow citizen relationships. يملك `LabOrder` حقلاً `version` وتعريفاً للتغييرات المتفائلة، وتستخدم عملية validation قفل الحالة وترجع `409` عند السباق، لكن لا توجد طبقة frontend موحدة تضيف key/fingerprint/version إلى كل queue mutation.

القرار في R3 هو **إضافة envelope client-side مشترك ومتوافق مع backend الحالي**. لا يغيّر هذا القرار endpoint semantics تلقائياً؛ عند عدم دعم endpoint لـ`Idempotency-Key` أو `If-Match` سيظل الخادم هو مصدر القرار، ويجب تسجيل `409` كـconflict وعدم حذف السجل أو إعادة إرساله بلا تغيير.

## أخطاء البناء المؤكدة قبل R3

| التطبيق | الخطأ المؤكد | السبب | الإصلاح الآمن المقترح |
|---|---|---|---|
| Nurse | 11 `MISSING_EXPORT` | `App.tsx` يستورد خمس صفحات كـdefault بينما الصفحات تصدّر named functions | توحيد الصفحات الخمس إلى default export مع إبقاء الأسماء الداخلية والسلوك |
| Ministry | `statisticsService`, `surveillanceService`, `alertsService` غير مصدّرة | ملفات services تحوي pure helpers فقط، بينما الصفحات تتوقع facades لجلب API | إضافة thin typed facades فوق `api` الحقيقي، دون mocks أو تجاوز Demo gate |
| Radiology | `./src/styles/theme.css` و`./src/styles/components.css` غير محلولين | `main.tsx` داخل `src` ويستخدم مساراً نسبياً مكرراً؛ الملفات موجودة في `src/styles` | تصحيح imports إلى `./styles/theme.css` و`./styles/components.css` |

## R3 non-negotiable rules

كل queue mutation يجب أن يحمل `operationId` ثابتاً، و`idempotencyKey` مشتقاً/محفوظاً مع السجل، و`requestFingerprint` لحماية إعادة استخدام المفتاح مع payload مختلف، و`expectedVersion` عندما يكون المصدر معروف الإصدار. يجب أن تكون الحالات صريحة: `pending`, `syncing`, `synced`, `conflict`, `rejected`, `failed`. استجابة `409` أو تعارض version تنقل السجل إلى `conflict` مع metadata فقط؛ لا تُحذف البيانات ولا يُعاد تشغيل العملية تلقائياً. أما أخطاء الشبكة المؤقتة فتبقى `pending` مع backoff محدود، ولا تتجاوز حد المحاولات.

## أدلة الجرد

تم استخراج أخطاء البناء من سجلات `/tmp/gula_r2_builds/{nurse,ministry,radiology}*.log`، وتم فحص مصادر queue في التطبيقات الخمسة ومسارات service worker. نتائج R2 السابقة بقيت سليمة: لا local token persistence، ولا Workbox mutation replay جديد، ولا credentials داخل queue payloads بعد sanitizer.

## تنفيذ R3 والتحقق الفعلي

أضيفت حزمة `platform/ui/utils/offlineQueueContract.ts` بعقد envelope موحد يتضمن `schemaVersion`, `operationId`, `idempotencyKey`, `requestFingerprint`, `entityType`, `entityId`, `action`, `expectedVersion`, `attempt`, `maxAttempts`, وstate صريحاً: `pending`, `syncing`, `synced`, `conflict`, `rejected`, `failed`. يقوم العقد بتطبيع body لحساب fingerprint ثابت، ويرسل `Idempotency-Key` و`X-GULA-Operation-ID` و`X-GULA-Request-Fingerprint`، ويضع `If-Match` عندما يتوفر expected version. لا تُرسل credentials داخل الـenvelope، ويظل sanitizer R2 هو بوابة الإنشاء وإعادة التشغيل.

تم ربط العقد بمسارات Citizen وDoctor وLaboratory (بما فيها Laboratory OfflineContext المستقل)، وبـNurse queue metadata، وPharmacy pending dispenses. عند استجابة `409` أو `412` لا يُحذف السجل ولا يُعاد تشغيله تلقائياً؛ يُحفظ كـ`conflict` مع status وserver body ووقت الاكتشاف. أخطاء 4xx غير الخاصة بالتعارض تُسجل كـ`rejected`، وأخطاء الشبكة تُعيد السجل إلى `pending` بزيادة attempt حتى الحد المسموح.

في backend، يقبل `/orders/{order_id}/validate` الآن `If-Match` رقمياً اختيارياً، ويطبق compare-and-set ذرياً على `LabOrder.version` ويرفع version عند نجاح validation. الإصدار القديم أو السباق يرجع `409` ولا يقفل الطلب ولا يغير version. أضيفت headers الخاصة بالعقد إلى CORS allow-list حتى لا يفشل browser preflight.

| التحقق | النتيجة |
|---|---|
| `offlineQueueContract.test.ts` | ناجح؛ fingerprint ثابت للـpayload المرتب، Idempotency-Key وIf-Match صحيحان، و409/412 يصنفان كتعارض |
| `offlineQueueSecurity.test.ts` | ناجح |
| Clinical safety tests | 33 ناجحاً |
| Backend full suite | **2306 ناجحاً، 251 تحذيراً** خلال 255.70 ثانية |
| UI contract typecheck | ناجح باستخدام TypeScript 7.0.2 مع `--ignoreConfig` |
| Vite builds | citizen وdoctor وlaboratory وnurse وpharmacy وradiology وministry وhospital: **8/8 ناجحة** |
| `git diff --check` | ناجح |

## إصلاح أخطاء البناء

تم توحيد default exports في صفحات Nurse التي كان `App.tsx` يستوردها كـdefault، بما في ذلك Admissions وDischarge وBedsideVerification وBarcodeScanning وQRVerification وOfflineMode، مع إبقاء السلوك الداخلي للصفحات. في Ministry أضيفت facades typed لـstatistics وsurveillance وalerts فوق API الحقيقي، وأزيلت استخدامات `motion/react` غير المثبتة من Login وKPICard وAlertPanel وMapView باستبدالها بعناصر ثابتة لا تغير data flow أو Demo gate. في Radiology صُححت مسارات CSS من `./src/styles/*` إلى `./styles/*`.

## حدود متبقية

العقد المشترك يضمن semantics على مستوى client queue، بينما لا تدعي R3 أن كل endpoint سريري في النظام أصبح يدعم idempotency أو version headers؛ دعم backend يجب أن يُعمم endpoint-by-endpoint بعد جرد API في موجة لاحقة. كما أن `If-Match` في هذه الموجة مطبق على validation الخاص بـLabOrder فقط. لا تشمل R3 backfill أو dual-write أو حذف clinical caches أو تغيير deployment، ولا تشمل دمج Wave 3 في main أو معالجة Dependabot alerts على default branch.
