# ADR: توحيد نموذج الموعد ومسار التوافق

**الحالة:** مقترح للمراجعة — لا يغيّر قاعدة البيانات أو واجهات API في هذه الموجة  
**التاريخ:** 2026-08-27  
**النطاق:** Core Clinical Golden Path، من طلب الموعد حتى Check-in وEncounter  
**القرار:** اعتماد نموذج Appointment خاص بالـCore ذي حالات العقد المستهدفة، مع إبقاء National Scheduling كـlegacy adapter مؤقتاً وقراءة فقط من منظور الترحيل، ومنع إنشاء state machine ثالثة.

## السياق

يحتوي المستودع حالياً على نموذجين مستقلين للمواعيد. الأول هو `NationalAppointment` وخدمة `SchedulingPlatformService` تحت `backend/app/national/scheduling_platform/`، وهو نموذج إداري عام يضم المريض والممارس والمنشأة والمورد ووقت البداية والنهاية، ويستخدم الحالات `PROPOSED`, `PENDING`, `BOOKED`, `ARRIVED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`, و`ENTERED_IN_ERROR`. مساره الحالي مركب على `/national/scheduling` ومحمى بصلاحية `system:admin`، ويستعمل payloads من نوع `dict` بدلاً من عقد طلب/استجابة سريري typed.

النموذج الثاني موجود في `shared/domain/booking.py` ويستخدم الحالات `PENDING`, `CONFIRMED`, `CHECKED_IN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, و`NO_SHOW`. أما عقد الـCore المعلن في `frontend-v3/src/contracts/clinicalContracts.ts` فيضيف `REQUESTED`, `CONFIRMED`, `CHECKED_IN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`, `RESCHEDULED`, و`EXPIRED`. وجود هذه القوائم الثلاث لا يثبت أن أياً منها جاهز للإنتاج؛ لكنه يثبت خطر التناقض إذا رُبطت الواجهة مباشرة بالمسار الإداري القديم أو أُنشئ مسار رابع.

## الأدلة التي بُني عليها القرار

| الدليل | الواقع الحالي | الأثر على القرار |
|---|---|---|
| `backend/app/national/scheduling_platform/api/routes.py` | router إداري عام، parsing يدوي، وعمليات كتابة متعددة للمواعيد والموارد والجداول | لا يُعتمد كـCore Clinical API للمواطن أو الطبيب |
| `backend/app/national/scheduling_platform/infrastructure/models.py` | جدول قديم فيه `version` وفهارس وقتية، دون مفاتيح workspace/tenant أو قيد slot متين | يلزم migration غير مدمرة وقيود قاعدة بيانات قبل الإنتاج |
| `backend/app/national/scheduling_platform/infrastructure/repository.py` | `save()` يقرأ ثم يكتب ثم ينفذ `commit()` لكل عملية؛ لا يظهر Compare-and-Swap أو `with_for_update` أو idempotency persistence | يوجد خطر lost update وdouble booking تحت التزامن؛ لا يعاد استخدامه دون hardening |
| `backend/app/national/scheduling_platform/application/service.py` | توجد انتقالات محلية وفحص تعارض قبل الحفظ، لكن ليست معاملة واحدة مع الحجز والتدقيق والتفويض | لا يكفي كدليل ACID أو object authorization أو audit immutable |
| `shared/domain/booking.py` | state machine أبسط، لكنها لا تحمل workspace/organization/purpose/version أو authorization context | مرجع مفاهيمي فقط، وليست canonical persistence model |
| `frontend-v3/src/contracts/clinicalContracts.ts` | عقد واجهة مرجعي يطلب حالات Core واضحة وكتابات آمنة | يُستخدم كهدف توافق، لا كسلطة تفويض backend |
| `backend/app/factory.py` | router القديم مركب عالمياً ضمن factory | يجب أن يبقى adapter محصوراً ومراقباً، ولا تُفتح له allowlists الواجهة |

## القرار المعتمد

سيكون **Core Appointment** هو النموذج canonical الوحيد لمسار الـGolden Path. ويجب أن يمثل الموعد سياقاً قابلاً للتفويض، لا مجرد فترة زمنية؛ لذلك يشمل العقد النهائي، بعد تصميمه وتنفيذه، هوية الحساب/الجلسة، workspace، organization/facility، patient، practitioner أو care team، الغرض والأساس القانوني عند اللزوم، المورد والزمن والمنطقة الزمنية، الإصدار، مفتاح idempotency، وسجل الأحداث والتدقيق.

ستكون حالات الـCore canonical هي: `REQUESTED`, `CONFIRMED`, `CHECKED_IN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`, `RESCHEDULED`, و`EXPIRED`. لا تعني إضافة هذه القائمة إلى ADR أو إلى typed contract أن API أو migration أو authorization أصبحت جاهزة. يجب أن يملك backend state machine واحدة قابلة للاختبار، وأن تُعامل الواجهة كعميل يعرض الحالات التي يرسلها backend فقط.

لن يُعتمد `shared/domain/booking.py` كما هو، ولن يُعاد استخدام `NationalAppointment` كما هو. يمكن الاستفادة من قواعدهما بعد توحيدها في domain model واحد، مع إبقاء أسماء legacy في compatibility layer أو migration metadata فقط. لا يجوز أن تتخذ واجهة المواطن والعيادة والطبيب قرارات بناءً على تحويل محلي للحالات.

## خريطة التوافق المقترحة

الخريطة التالية للـbackfill والتوافق **اقتراح تصميمي غير منفذ**. كل تحويل يجب أن يحتفظ بالحالة الأصلية وسبب التحويل ومصدر الدليل وإصدار migration. الصفوف الموسومة بالمراجعة لا يجوز تحويلها آلياً في بيانات حقيقية.

| الحالة القديمة | الحالة canonical المقترحة | درجة التحويل | القاعدة والقيود |
|---|---|---:|---|
| `PROPOSED` | `REQUESTED` | آمن مبدئياً | طلب غير مؤكد؛ يلزم الاحتفاظ بـ`legacy_status` وعدم منح تأكيد للمريض أو مقدم الخدمة |
| `PENDING` | `REQUESTED` | مشروط | تُفسر كطلب ينتظر قبولاً ما لم يوجد event موثق يثبت الحجز؛ لا تُحوّل تلقائياً إلى `CONFIRMED` |
| `BOOKED` | `CONFIRMED` | مشروط مرتفع | لا يعتمد التحويل على الاسم وحده؛ يجب التحقق من المريض والمورد والزمن وعدم وجود تعارض وسجل حجز قابل للتدقيق |
| `ARRIVED` | `CHECKED_IN` | مشروط مرتفع | يتطلب دليلاً على وصول صحيح ضمن المنشأة/الموعد؛ لا يكفي تعديل status منفرداً |
| `IN_PROGRESS` | `IN_PROGRESS` | مباشر مع تحقق | يجب التحقق من workspace والموعد المفتوح وربط Encounter عند تفعيله |
| `COMPLETED` | `COMPLETED` | مباشر مع تحقق | حالة نهائية؛ لا يعاد فتحها بصمت، وأي تصحيح يمر بإجراء amendment/audit مستقل |
| `CANCELLED` | `CANCELLED` | مباشر مع تحقق | تُحفظ جهة وسبب الإلغاء وزمنه، ولا يُعاد استخدام slot دون معاملة وقيد تنافسي واضح |
| `NO_SHOW` | `NO_SHOW` | مباشر مع تحقق | تُحفظ سياسة ووقت التسجيل ومصدر القرار؛ لا تُستنتج آلياً من مرور الوقت فقط |
| `ENTERED_IN_ERROR` | لا تحويل تلقائي | مرفوض آلياً | ليست بديلاً عن `CANCELLED`; تُحفظ في quarantine/legacy audit إلى أن يحدد مالك المجال سياسة تصحيح قانونية وغير صامتة |
| لا توجد حالة قديمة مكافئة | `RESCHEDULED` | لا يُشتق من status | تُنشأ فقط من حدث reschedule موثق؛ الحالة الحالية بعد الحدث تعود إلى `REQUESTED` أو `CONFIRMED` وفق القرار الموثق |
| لا توجد حالة قديمة مكافئة | `EXPIRED` | لا يُشتق من status | يحتاج policy زمنية صريحة ومهمة موثوقة وسجل تدقيق؛ لا يحول backfill المواعيد إلى expired بالتخمين |

## الحالة والانتقالات canonical

| من | إلى المسموح | ملاحظة أمان |
|---|---|---|
| `REQUESTED` | `CONFIRMED`, `CANCELLED`, `EXPIRED` | التأكيد يتطلب صلاحية وسياق workspace وموعداً صالحاً |
| `CONFIRMED` | `CHECKED_IN`, `CANCELLED`, `RESCHEDULED`, `NO_SHOW`, `EXPIRED` | reschedule حدث versioned وليس overwrite للوقت |
| `CHECKED_IN` | `IN_PROGRESS`, `NO_SHOW` | لا يبدأ Encounter من واجهة دون object authorization |
| `IN_PROGRESS` | `COMPLETED` | إغلاق الموعد لا يوقع Encounter أو note تلقائياً |
| `RESCHEDULED` | `REQUESTED` | لا تُستخدم لإخفاء سجل الزمن السابق؛ يلزم event/audit |
| الحالات النهائية | لا انتقال صامت | التصحيح أو amendment مسار مستقل ومصرح ومدقق |

هذه الانتقالات هي هدف التحقق فقط. لا تزال خدمة National الحالية تملك انتقالات مختلفة، منها `PROPOSED → PENDING → BOOKED` و`ARRIVED → IN_PROGRESS`، ولذلك يجب منع أي route جديد من استيراد جدولها مباشرة قبل قرار الترحيل.

## خطة الترحيل القابلة للعكس

لن يبدأ الترحيل بتغيير معنى الأعمدة الحالية. المرحلة الأولى هي **add**: إضافة حقول canonical nullable أو جدول أحداث/compatibility mapping منفصل، مع حفظ `legacy_status`, `legacy_source`, و`mapping_version`، وإضافة قيود وفهارس لا تغيّر السلوك القديم. المرحلة الثانية هي **backfill** على نسخة اصطناعية وبيانات staging مع تقرير counts وambiguous/quarantined rows، دون الكتابة فوق المصدر ودون تحويل `ENTERED_IN_ERROR` أو الحالات الزمنية بالتخمين.

المرحلة الثالثة هي **validate**: فحص uniqueness للتداخل على resource/practitioner، اكتمال tenant/workspace، سلامة المراجع، توافق المنطقة الزمنية، سلامة الإصدار، ومطابقة كل تحويل لسجل تدقيق. المرحلة الرابعة هي **shadow read**: قراءة النموذجين ومقارنة النتائج في بيئة development/staging فقط، من دون تغيير واجهة الإنتاج. المرحلة الخامسة هي **switch** بعد اعتماد مالك المجال ونجاح اختبارات contract/security/concurrency/performance، ثم إبقاء rollback عبر feature flag وقراءة legacy غير مدمرة خلال فترة مراقبة محددة.

لا يسمح هذا ADR بحذف الجدول القديم، ولا بتعديل حالة `SIGNED` أو `RELEASED` أو سجل سريري ذي أثر، ولا بربط frontend-v3 بأي write route. إذا فشل التحقق، تعود القراءة إلى المسار السابق مع تسجيل الفشل، ولا تُستخدم بيانات Demo كـfallback لبيانات Live.

## شروط فتح أول API إنتاجية للمواعيد

قبل فتح endpoint canonical يجب أن توجد schemas typed وerror envelope آمن، وتحقق account/session/device/workspace/membership/organization/facility/patient relationship/purpose، وقاعدة object-level وtenant authorization، وACID transaction واحدة، وlocking أو قيد قاعدة بيانات يمنع double booking، و`If-Match` أو version compare-and-swap، وتخزين دائم لـ`Idempotency-Key` مع replay semantics، وتدقيق append-only، وrate limit، وترقيم صفحات، واختبارات negative للـIDOR وwrong patient/workspace/org وsession/consent expiry، واختبارات التزامن وrollback وcontract وE2E الاصطناعية.

عند توفر هذه الأدلة فقط يمكن إنشاء vertical slice صغير: **request/confirm appointment**. ولا يشمل ذلك في البداية الموارد والجداول وقائمة الانتظار والتذكيرات أو التكاملات الوطنية. بعد تثبيت الحجز، يُربط Check-in ثم Encounter في موجات منفصلة، مع عدم تمرير أي كتابة إلى frontend-v3 قبل نجاح عقد backend وremote CI وstaging smoke.

## العواقب والمخاطر

هذا القرار يبطئ فتح ميزات الحجز السريعة ظاهرياً، لكنه يمنع وجود state machines متنافسة وقرارات UI غير موثوقة. الخطر المتبقي هو أن معنى `PENDING` و`BOOKED` التاريخي قد يختلف بين الجهات؛ لذلك جرى إبقاء التحويل مشروطاً، مع quarantine ومراجعة بشرية للصفوف الملتبسة. كما أن صلاحية `system:admin` الحالية لا تثبت صلاحية المواطن أو الطبيب، ووجود `version` في الجدول لا يثبت أن repository يطبق optimistic locking.

**Rollback:** طالما لم تُنفذ migration أو switch في هذا ADR، فالرجوع هو عدم تفعيل أي feature flag وعدم تغيير route. بعد تنفيذ المراحل اللاحقة يجب أن يكون rollback عبارة عن إيقاف القراءة canonical، إعادة القراءة legacy غير المدمرة، وحفظ جميع أحداث المقارنة والتدقيق؛ لا يجوز rollback بحذف سجلات أو الكتابة فوق الحالة السريرية.

## الأدلة المطلوبة لإغلاق ADR

يُغلق هذا ADR فقط بعد إضافة قرار مالك المجال، migration plan reviewed، canonical model/API، authorization matrix، repository transaction/locking proof، persisted idempotency، audit integration، compatibility tests، concurrency/security tests، synthetic FastAPI E2E، remote CI، staging smoke، ومؤشرات rollback. أما الوضع الحالي فهو **DESIGNING / EXTERNAL_DEPENDENCY** وليس `READY_FOR_STAGING` أو `READY_FOR_PRODUCTION`.
