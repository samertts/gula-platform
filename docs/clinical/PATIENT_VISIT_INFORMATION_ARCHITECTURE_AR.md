# PATIENT VISIT INFORMATION ARCHITECTURE

## الغرض والنطاق

تحدد هذه الوثيقة المعمارية المعلوماتية لنظام زيارة المريض داخل GULA، وتحوّل المتطلبات المرفقة إلى حدود قابلة للتنفيذ والمراجعة. هذه الدفعة **تصميمية وتعاقدية** ولا تنشئ عملية سريرية حقيقية أو بيانات مرضى حقيقية أو صلاحيات جديدة.

> **المبدأ الحاكم:** الموعد `Appointment` حجز أو نية وصول، بينما الزيارة `Encounter` حدث سريري فعلي يبدأ بعد الوصول والتحقق والقبول الذي يسمح به Backend.

تدعم المعمارية مؤسسات مختلفة مثل المستشفى والعيادة والمركز الصحي والمختبر والأشعة والجهات الحكومية والخاصة، لكن نوع الجهة لا يمنح صلاحية سريرية تلقائيًا. كل قرار وصول يجب أن يعتمد على هوية الجلسة، العضوية الموثقة، المؤسسة والمنشأة والقسم ومساحة العمل والدور والصلاحية وسياسة Backend وسجل التدقيق.

## قرار الجاهزية الحالي

| النطاق | الحالة | الأساس |
|---|---|---|
| تعريف Information Architecture وUser Flows | READY_FOR_REVIEW | يمكن تنفيذه كوثيقة وتصميم Stitch دون بيانات تشغيلية |
| شاشة Patient/Appointment/Queue تجريبية | BACKEND_DEPENDENCY | السطح الحالي يستخدم بيانات محلية اصطناعية ويعلن ذلك صراحة |
| Encounter حقيقي وCheck-in وTriage وClose | BACKEND_DEPENDENCY | العقد الحالي العام لا يثبت Request/Response أو انتقالات موثقة أو Authorization متعدد السياقات |
| عرض النتائج المرتبطة بالزيارة | BLOCKED | سطح `/results` محجوب عمدًا لعدم ثبوت `test-results.read` مع سياق المنشأة والتفويض الخادمي |
| كتابة الملاحظات أو العلامات الحيوية أو التشخيص أو الأوامر | BLOCKED | لا تنفيذ دون عقد خادمي typed، version check، idempotency، audit، وسياسة انتقالات |
| Prototype Stitch | READY_FOR_REVIEW | تصميم غير تشغيلي ببيانات اصطناعية وحواجز واضحة |

## كيان Appointment وكيان Encounter

| العنصر | Appointment | Encounter |
|---|---|---|
| المعنى | حجز أو طلب موعد | زيارة سريرية فعلية |
| يبدأ متى؟ | عند إنشاء/اقتراح الحجز | بعد Check-in والتحقق والقبول الخادمي |
| يرتبط بـ | المريض أو الجهة، الموعد، الخدمة، المنشأة، المهني عند توفره | المريض، المؤسسة، المنشأة، القسم، المهني، مساحة العمل، الممثل، الصلاحية، التدقيق |
| حالات مرجعية موجودة | `proposed`, `pending`, `booked`, `arrived`, `in_progress`, `completed`, `cancelled`, `no_show` | `planned`, `in_progress`, `on_hold`, `discharged`, `completed`, `cancelled`, `entered_in_error`, `unknown` |
| قاعدة العرض | لا تعرض الحجز كزيارة | لا تعرض الزيارة كحجز ولا تسمح بانتقال واجهة منفرد |

## الدخول إلى مسار الزيارة

```text
Patient or authorized staff
        ↓
Appointment or Walk-in intent
        ↓
Check-in request
        ↓
Backend identity/record/context verification
        ↓
Queue placement when supported
        ↓
Encounter creation or activation by Backend
        ↓
Role-scoped clinical workflow
```

التصميم لا يفترض أن كل مريض مواطن أو أن كل مؤسسة حكومية. يمكن أن يكون الكيان عراقيًا أو غير عراقي، لكن أي مستوى تحقق أو ارتباط سريري يجب أن يأتي من Backend Contract موثق، وليس من اسم مكتوب في الواجهة.

## حالات واجهة الزيارة

تُعرض الحالات الآتية كحالات معلوماتية فقط إلى أن يعرّف Backend انتقالاتها رسميًا:

| الحالة المرئية | المعنى المقترح | شرط النقل |
|---|---|---|
| Scheduled | موعد مجدول | Appointment contract |
| Arrived | وصول مسجل | Appointment/arrival contract |
| Checked-in | Check-in مقبول | Verification + facility/workspace authorization |
| Waiting | موجود في قائمة انتظار | Queue contract |
| In Consultation | دخل المرحلة السريرية | Encounter workflow contract |
| Completed | اكتملت الزيارة | Close requirements contract |
| Cancelled | ألغيت | Backend cancellation policy |
| No-show | لم يحضر | Backend attendance policy |
| Referred | أحيلت الحالة | Referral contract؛ لا يعني قبول الجهة المستلمة |

لا يجوز للواجهة أن تغيّر الحالة بمجرد تغيير badge أو اختيار قائمة. كل انتقال يجب أن يعود من Backend، ويجب رفض الانتقال غير المسموح وتسجيل محاولة المخالفة.

## Check-in

يعرض Check-in أقل قدر لازم من البيانات: المريض أو المعرّف المصرّح بعرضه، سبب الزيارة، مرجع الموعد أو نوع الوصول، المؤسسة، المنشأة، القسم، المهني عند توفره، وحالة التحقق. لا يعرض بيانات صحية أو وطنية أو تعريفية إضافية لمجرد تحسين التصميم.

الحالات التي يجب أن يصممها Stitch والواجهة هي: تحميل، عدم العثور على الحجز، وصول غير مصرح، مؤسسة خاطئة، منشأة خاطئة، جلسة منتهية، تعارض version، خدمة غير متاحة، وضع Offline، ونجاح مشروط من Backend. نجاح الواجهة لا يعني أن Encounter أُنشئ إلا بعد استجابة عقدية صريحة.

## Queue / Work Queue

يعرض طابور العمل رقم الدور أو المعرف الآمن، المريض ضمن النطاق، نوع الزيارة، الأولوية، وقت الوصول، وقت الانتظار، الحالة، والمهني المسؤول عند السماح. يدعم البحث والتصفية والأولوية والحالة والتقسيم إلى صفحات. لا يسمح التصميم بإعادة ترتيب الطابور أو رفع الأولوية من الواجهة ما لم يوجد عقد وصلاحية وتدقيق لذلك.

أي priority أو risk score يجب أن يأتي من نظام معتمد وعقد موثق. لا يضيف التصميم Clinical Scoring جديدًا ولا يستنتجه من اللون أو الاسم.

## صفحة Encounter الموحدة

تتكون الصفحة من وحدات قابلة للإخفاء حسب Backend authorization:

| الوحدة | نوعها | قاعدة الوصول |
|---|---|---|
| Patient Header | هوية مختصرة ونطاق المؤسسة والمنشأة ومساحة العمل | أقل بيانات لازمة؛ لا كشف عابر للمستأجرين |
| Visit Summary | نوع الزيارة والسبب والحالة والزمن | قراءة وفق Encounter.Read |
| Chief Complaint / History | بيانات سريرية | دور سريري وسياسة مجال |
| Vitals | ملاحظات منظمة | لا تعرض أو تكتب إن لم يدعم Backend العقد |
| Assessment / Diagnoses | تقييم وتشخيص | دور مخول وانتقال موثق |
| Orders | مختبر، أشعة، دواء، إجراء، إحالة | كل طلب مرتبط بالـEncounter ومصدره وحالته |
| Results | Pending، Available، Reviewed | لا اعتماد نتيجة من الواجهة |
| Clinical Notes | ملاحظات | append/version policy وتدقيق |
| Documents | مستندات ومرجع تخزين | لا رفع أسرار أو ملفات غير موثقة |
| Timeline | حدث، actor، time، source، status | immutable/read-only من منظور الواجهة |
| Follow-up | التاريخ والمهني والمنشأة والسبب والتعليمات | إنشاء Appointment فقط إذا دعمه Backend |
| Close Summary | ملخص الإغلاق والتعليمات | الإغلاق النهائي مشروط بمتطلبات Backend |

## سير العمل السريري

```text
Check-in → Triage → Consultation → Assessment → Orders → Results → Review → Plan → Follow-up → Close Encounter
```

هذه الخريطة لا تعني أن جميع الخطوات مفعلة. كل خطوة تحمل حالة `READY` أو `BACKEND_DEPENDENCY` أو `BLOCKED`. لا يجوز إدخال نتيجة بلا عينة موثقة، ولا اعتماد نتيجة بلا دور مخول، ولا تسجيل انتقال غير موجود في state machine.

## Triage

تقتصر واجهة Triage على الحقول التي يثبتها Backend: سبب الزيارة، الأولوية، العلامات الحيوية عند توفر عقدها، الحساسية، التنبيهات، ودرجة الخطورة إذا كان هناك نظام معتمد. لا تنشئ GULA مقياس خطورة جديدًا ولا تفسر قيمة غير موثقة على أنها تشخيص أو قرار طبي.

## Orders وResults

الطلب داخل Encounter يحمل نوعه، المصدر، الحالة، المؤسسة والمنشأة ومساحة العمل والفاعل عند السماح. الأنواع التصميمية هي Lab Order وRadiology Order وMedication وProcedure وReferral، لكنها لا تصبح قابلة للإرسال إلا بعقد typed وصلاحية وانتقال وتدقيق.

النتائج داخل الزيارة تعرض `Pending` و`Available` و`Reviewed` فقط عندما يثبت Backend علاقة النتيجة بالـEncounter وسياق المنشأة والصلاحية. لا تستخدم الواجهة fallback قديمًا للقراءة، ولا تنفذ اعتمادًا متفائلًا، ولا تعرض mock clinical data في live mode.

## Patient View

يعرض المواطن أو صاحب المساحة المصرح له: موعده، حالة الوصول، الزيارة الحالية، ملخص الزيارة، التعليمات، الوصفات، الطلبات، النتائج المتاحة، والمتابعة وفق policy. تُحجب الملاحظات أو الحقول المقيدة عندما لا يثبت Backend حق العرض. هذه الدفعة لا تفعل citizen registration ولا national identity ولا OCR/NFC/biometrics.

## أنواع الزيارة

يدعم التصميم أسماء قابلة للتوسع: Outpatient وEmergency وInpatient وFollow-up وTelehealth وPreventive وScreening وHome Visit. لا تُعرض كخيارات مفعلة إلا إذا عاد Feature Flag أو Capability Contract يسمح بها. نوع الزيارة لا يمنح الدور أو الصلاحية.

## الأدوار المتعددة

يُستخدم Encounter واحد مع واجهات مختلفة بحسب صلاحية الدور: Doctor، Nurse، Technician، Pharmacist، Radiologist، Laboratory Professional، Authorized Administrator. لا ينشئ النظام Encounter منفصلًا لكل دور. الفرق في الواجهة يقتصر على ما يسمح به Backend، ولا يسمح إخفاء زر بالواجهة باعتباره Authorization.

## الخصوصية والأمن

كل Encounter يجب أن يرتبط منطقيًا بالمريض، المؤسسة، المنشأة، مساحة العمل، actor، permission، وaudit. يجب منع cross-tenant access، وfrontend-only authorization، وlegacy fallback، وبيانات clinical mock في live mode. لا تُخزن بيانات حساسة في localStorage، ولا تُرسل أسرار أو tokens من شاشات Stitch أو Prototype.

## حالات النظام المطلوبة

يجب تصميمها واختبارها في كل شاشة: Loading، Empty، Waiting، In Progress، Pending، Completed، Cancelled، No-show، Unauthorized، Forbidden، Expired Session، Offline، Service Unavailable، وConflict. لا يعتمد فهم الحالة على اللون وحده؛ يستخدم النص، الرمز، وحالة التركيز المرئية.

## Mobile وRTL/LTR

تدعم الواجهات RTL للعربية والكردية والسريانية، وLTR للإنجليزية والتركمانية عند الحاجة، وتتعامل مع الأسماء الطويلة والأرقام والتواريخ والمصطلحات الطبية. الحد الأدنى للهدف اللمسي 44×44px، ولا يسمح التصميم بHorizontal Overflow. تُراجع Patient وQueue وEncounter وOrders وResults وTimeline وMore على الهاتف.

## تصنيف التنفيذ

| التصنيف | المعنى |
|---|---|
| READY | وثيقة أو تصميم أو سطح قراءة لا يغير بيانات سريرية |
| READY_FOR_REVIEW | تنفيذ أولي يحتاج مراجعة بشرية قبل الدمج |
| BACKEND_DEPENDENCY | التصميم جاهز لكن العقد الخادمي أو التفويض أو التدقيق غير مثبت |
| BLOCKED | يمنع تنفيذه الآن بسبب بوابة سلامة أو قيد P4 |

## القرار

يُعتمد هذا المستند كمرجع تصميمي أولي فقط. لا يفتح P5، ولا يغير حالة P4، ولا يثبت جاهزية Encounter للإنتاج. أي تنفيذ لاحق يجب أن يمر عبر Backend Contract Map واختبارات عزل المؤسسة والتفويض والتدقيق والتعارض قبل السماح به.
