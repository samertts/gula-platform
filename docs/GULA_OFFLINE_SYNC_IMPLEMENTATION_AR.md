# تنفيذ Offline Sync وConflict Resolution وRealtime Clinical Notifications

## نطاق التنفيذ

أضيفت إلى فرع التنفيذ طبقة خادمية موحدة لمسار مزامنة سجلات الطوارئ بعد انقطاع الشبكة، مع تخزين عمليات المزامنة والتعارضات والأقفال المؤقتة وأحداث Outbox والإشعارات السريرية. كما أضيفت واجهة تشغيل Offline إلى مسار `/patient-flow` ومركز مراجعة التعارضات إلى `/sync/conflicts`.

لا تُعد هذه الإضافة بديلًا عن اعتماد المؤسسة الحكومية أو اختبار القبول السريري الميداني. الترحيل `20260817_0025` موجود في المستودع، لكنه لم يُطبق على قاعدة إنتاج.

## التغييرات الخلفية

| المكوّن | التنفيذ |
|---|---|
| `NationalSyncOperationModel` | عملية مزامنة بنطاق المؤسسة والجهاز، `operation_id`، `idempotency_key`، البصمة، النسخة، الأولوية، وحالة المعالجة. |
| `NationalSyncConflictModel` | حفظ التعارض المحلي والخادمي ونوعه وخطورته وحالة المراجعة وسبب الحل. |
| `NationalRecordLockModel` | قفل Lease قصير بمالك وجهاز ورمز منقوص البصمة ووقت انتهاء وتجديد. |
| `NationalSyncOutboxModel` | تخزين الأحداث داخل المعاملة قبل إرسالها إلى العامل الخلفي. |
| `NationalClinicalNotificationModel` | صندوق إشعارات سريرية لكل مستخدم مع `dedupe_key` والإقرار والتصعيد. |
| `NationalDeviceSessionModel` | جلسة جهاز محدودة المؤسسة والمدة والعمليات المسموحة في وضع Offline. |
| `sync_conflict_service.py` | التحقق من النطاق، منع التكرار، تطبيق انتقالات Encounter، إنشاء التعارض، Outbox، التنبيه، الإقرار، وحجز القفل. |
| `sync.py` | مسارات FastAPI الفعلية للمزامنة والتعارضات والأقفال والإشعارات وSSE. |
| `sync_outbox.py` | معالج عامل خلفي يستهلك Outbox دون تغيير حالة سريرية أو تجاوز المراجعة، مع retry لكل حدث وتأخير exponential backoff وحد أقصى 8 محاولات ثم `dead_letter`. |

## مسارات API الموصولة

تظهر جميع المسارات تحت البادئة `/national/sync`:

```text
POST   /devices/session
GET    /status
POST   /operations:batch
GET    /changes
GET    /conflicts
GET    /conflicts/{conflict_id}
POST   /conflicts/{conflict_id}:resolve
GET    /notifications
POST   /notifications/{notification_id}:acknowledge
POST   /notifications/{notification_id}:escalate
GET    /notifications/stream
POST   /records/{resource_type}/{resource_id}:lock
POST   /records/{resource_type}/{resource_id}:lock-heartbeat
DELETE /records/{resource_type}/{resource_id}:lock
```

تستخدم الكتابة صلاحية `hospital:flow:write` والقراءة `hospital:flow:read`. ويستخرج `lab_id` من المستخدم المصادق عليه ولا يثق بقيمة النطاق المرسلة من العميل. بعد `POST /devices/session` يعيد الخادم `device_session_token` مرة واحدة، ويخزن SHA-256 للرمز فقط. ويجب إرسال الرمز في رأس `X-Device-Session` إلى `/status` و`/operations:batch`؛ لا يكفي `device_id` وحده، كما لا يدخل الرمز في payload السريري أو سجل العملية.

## قواعد السلامة المطبقة

لا تستخدم طبقة المزامنة قاعدة `last-write-wins`. تكرار العملية يعيد نتيجة العملية السابقة بدل إنشاء أثر ثانٍ، أما اختلاف البصمة مع نفس مفتاح idempotency فيُرفض. انتقالات Encounter تمر عبر آلة الحالات وفحص النسخة، وتم تعزيز خدمة الانتقال بقفل صف قاعدة بيانات قصير عبر `with_for_update` مع استمرار فحص `expected_version` وعزل `lab_id`.

كما عُدّل محرك Offline العام بحيث يرفض `LAST_WRITE_WINS` و`TIMESTAMP_MERGE` و`CRDT_MERGE` للتعارضات، ولا يقبل إلا `MANUAL` مع `merged_data` وقرار مراجع صريح. وهذا يمنع الدمج الصامت للبيانات السريرية.

## واجهة Offline

تستخدم صفحة `RapidPatientFlowPage` طابور IndexedDB باسم `gula-emergency-offline`. عند انقطاع الشبكة، تحفظ عملية الوصول أو الانتقال محليًا مع `operation_id` و`idempotency_key` و`base_version`، وتشفّر payload باستخدام AES-GCM بمفتاح CryptoKey غير قابل للاستخراج محفوظ في مخزن metadata مستقل. إصدار قاعدة البيانات هو `2` مع ترقية تلقائية من الإصدار السابق. الحد التشغيلي للطابور هو 5000 عملية؛ وعند امتلائه تظهر رسالة عربية تمنع الإيحاء بأن العملية اعتمدت وتطلب تفعيل الإجراء المؤسسي البديل وإبلاغ المشرف.

عند عودة الاتصال، تسجل الشاشة جلسة الجهاز عند الحاجة ثم ترسل العمليات إلى `/national/sync/operations:batch` مع رأس الجلسة. العمليات المقبولة أو المكررة تُزال من الطابور، بينما تبقى العمليات المتعارضة أو الفاشلة معلّمة للمراجعة. وتعرض الشاشة حالة الاتصال وعدد العمليات المحلية وعدد التنبيهات الحرجة، وتستقبل إشعارات SSE عبر `/national/sync/notifications/stream`. جميع انتقالات Offline تستخدم المعرف نفسه لـ`operation_id` و`idempotency_key`.

أضيفت شاشة `/sync/conflicts` لعرض النسخة المحلية ونسخة الخادم، وإقرار التنبيهات، واعتماد نسخة الخادم أو رفض العملية المحلية بسبب موثق. الإقرار منفصل عن حل التعارض، ولا يُعد حلًا سريريًا.

## الترحيل

يضيف `20260817_0025_sync_conflict_lock_notifications.py` ستة جداول وفهارس وقيود idempotency. يجب تطبيقه في بيئة اختبار مماثلة للإنتاج أولًا، ثم إجراء نسخة احتياطية واختبار رجوع وخطة ترحيل معتمدة قبل الإنتاج.

## الاختبارات والتحقق

| التحقق | النتيجة |
|---|---|
| اختبارات Offline وPatient Flow وجلسة الجهاز وOutbox والتصعيد | 29 اختبارًا ناجحًا في المجموعة المستهدفة. |
| مجموعة backend الأساسية بعد استبعاد اختبارات `services/device_bridge` غير المرتبطة | 2665 ناجحًا، 4 متجاوزة، 252 تحذيرًا. |
| TypeScript للواجهة | ناجح. |
| Vite build وPWA service worker | ناجح، وتظهر حزم `RapidPatientFlowPage` و`ConflictInboxPage`. |
| Python compileall للملفات الجديدة والمعدلة | ناجح. |
| Vitest للواجهة، بما في ذلك عقد حد IndexedDB | 54 اختبارًا ناجحًا. |
| `git diff --check` | ناجح قبل الإضافة. |
| المجموعة الكاملة دون استبعاد | متوقفة عند 12 خطأ تجميع قديم في `services/device_bridge` بسبب imports/مسارات غير موجودة، وليست من الملفات المعدلة في هذا التنفيذ. |

## حدود الجاهزية

ما يزال يلزم قبل اعتبار Offline Mode جاهزًا لبيئة حكومية فعلية: ربط مفتاح AES-GCM بمخزن مفاتيح مؤسسي أو إدارة أجهزة محمولة، تسجيل الأجهزة وشهاداتها في بيئة التشغيل، عامل دائم متعدد العقد أو Redis موثوق، سياسة مستلمين مرتبطة بجدول المناوبات، اختبارات ضغط وChaos على بنية مماثلة للإنتاج، اختبار المزامنة الموزعة بين جهازين، تكامل Push مؤسسي، ومراجعة قبول سريرية وأمنية. الآلية الحالية لا تدّعي أن مفتاح المتصفح يعادل HSM أو MDM.

لا ينبغي إطلاق الترحيل أو ميزة Offline على قاعدة إنتاج قبل إغلاق هذه النقاط واعتماد بروتوكول الطوارئ البديل عند امتلاء التخزين أو فشل المزامنة.
