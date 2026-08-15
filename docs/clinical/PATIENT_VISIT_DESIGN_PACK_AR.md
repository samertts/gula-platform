# PATIENT VISIT DESIGN PACK

## 1. Encounter Components

| المكوّن | العرض المكتبي | العرض المحمول | نوع البيانات | حالة التنفيذ |
|---|---|---|---|---|
| Patient Header | بطاقة ثابتة أعلى الصفحة مع نطاق المؤسسة والمنشأة | رأس مضغوط قابل للفتح | أقل بيانات لازمة | BACKEND_DEPENDENCY |
| Visit Summary | بطاقة ملخص مع الحالة والزمن والسبب | بطاقة واحدة مع status | Appointment/Encounter references | BACKEND_DEPENDENCY |
| Check-in Panel | نموذج متعدد الخطوات | خطوات عمودية | Request من Backend فقط | BACKEND_DEPENDENCY |
| Queue Board | جدول قابل للتصفية والتقسيم | بطاقات مرتبة | Queue contract | BACKEND_DEPENDENCY |
| Triage Panel | أقسام حسب الحقول المسموحة | تبويب واحد لكل قسم | Vitals/priority عند توفرها | BLOCKED قبل العقد |
| Consultation Workspace | أعمدة للملاحظات والتقييم والطلبات | تبويبات | clinical data مقيدة | BLOCKED |
| Orders Panel | جدول طلبات مع المصدر والحالة | بطاقات حالة | order contract | BACKEND_DEPENDENCY |
| Results Panel | جدول Pending/Available/Reviewed | بطاقات read-only | result contract | BLOCKED |
| Timeline | خط زمني أفقي/عمودي | خط زمني عمودي | audit/event source | BACKEND_DEPENDENCY |
| Follow-up | نموذج متابعة | sheet أو خطوات | follow-up contract | BACKEND_DEPENDENCY |
| Referral | نموذج وجهة وسبب وأولوية | خطوات قصيرة | referral contract | BACKEND_DEPENDENCY |
| Close Summary | ملخص قبل الإغلاق مع requirements | مراجعة قبل التأكيد | close contract | BLOCKED |

## 2. User Flows

### Appointment إلى Encounter

```text
Appointment أو Walk-in intent
        ↓
عرض Check-in المطلوب
        ↓
فحص session وorganization/facility/workspace من Backend
        ↓
قرار Checked-in
        ↓
Queue عند دعم العقد
        ↓
Encounter عند قبول workflow
        ↓
عرض الدور أو الحالة المسموحة
```

### Walk-in

يبدأ Walk-in كنية وصول لا كـEncounter. تعرض الواجهة حالة `BACKEND_DEPENDENCY` إلى أن يؤكد Backend تسجيل الوصول وإنشاء المرجع. لا تنشئ الواجهة UUID سريريًا ولا تستعمل local mock كأنه سجل حقيقي.

### Unauthorized وWrong Facility

يُعرض Forbidden عام لا يكشف إذا كان المريض أو الزيارة موجودين في مؤسسة أخرى. لا تعيد الواجهة توجيه المستخدم إلى مؤسسة أو مساحة أخرى ولا تسمح بتعديل workspace من client state.

### Expired Session وOffline وService Failure

يُحفظ فقط draft غير حساس إذا كان ذلك مسموحًا بسياسة المنتج، ثم تُعرض حالة إعادة المصادقة أو القراءة غير المتاحة. لا تُنشأ queue محلية لانتقال سريري ما لم يثبت عقد offline reconciliation وaudit.

### Close Encounter

```text
Review required fields
        ↓
Fetch current version
        ↓
Backend validates mandatory requirements
        ↓
Confirm reason and audit intent
        ↓
Close or return 409/422
        ↓
Render server-confirmed Visit Summary
```

## 3. Role Flows

| الدور | يرى | ينفذ عند وجود العقد | ممنوع تلقائيًا |
|---|---|---|---|
| Doctor | Encounter وAssessment والطلبات التي تسمح بها الصلاحية | consultation/assessment/order/follow-up | اعتماد نتيجة أو تغيير دور ذاتيًا |
| Nurse | Check-in/Triage/vitals عند السماح | triage أو queue transition الموثق | التشخيص أو اعتماد النتائج |
| Technician | الطلبات أو العينات ضمن المنشأة | عمليات فنية بعقد منفصل | قراءة Encounter خارج scope |
| Pharmacist | Medication orders ضمن النطاق | صرف/تحديث دواء إذا دعمه العقد | تعديل التشخيص أو close |
| Radiologist | radiology workflow المصرح | review/report إذا كان العقد موجودًا | عرض كل Encounter |
| Laboratory Professional | lab orders/results ضمن scope | إجراءات المختبر الموثقة | اعتماد عام خارج الصلاحية |
| Authorized Administrator | الحالة التشغيلية والتدقيق | إدارة scope أو flow المصرح | الوصول السريري لمجرد admin |
| Citizen/Patient | بياناته المفلترة حسب policy | طلب أو عرض الخدمة المتاحة | الملاحظات المقيدة والاعتماد |

لا يمنح الاسم أو نوع المؤسسة أو القطاع أو الدور العام صلاحية سريرية. كل خلية في الجدول تحتاج permission وorganization/facility/workspace context من Backend.

## 4. Mobile/Desktop

يستخدم سطح المكتب تقسيمًا واضحًا بين Patient Header وVisit Summary ومحتوى Encounter وTimeline. يستخدم الهاتف طبقات: Header، Summary، Current Step، Primary Action، More. لا يختفي زر محظور كأنه مسموح؛ يجب أن تظهر حالة Unauthorized أو Forbidden عند الحاجة.

تلتزم الشاشات بعرض لا يقل عن 44×44px للأهداف التفاعلية، ولا تستخدم horizontal overflow في Queue أو Timeline أو Results. الجداول تتحول إلى بطاقات، ويظل النص الكامل للحالة والمصدر والوقت متاحًا لقارئات الشاشة.

## 5. Multilingual

| اللغة | الاتجاه | عناصر اختبار إلزامية |
|---|---|---|
| العربية العراقية | RTL | مصطلحات الاستقبال والصف والزيارة، أسماء طويلة، أرقام عربية/لاتينية |
| العربية الفصحى | RTL | نصوص السياسة والرسائل الرسمية |
| English | LTR | المصطلحات السريرية القياسية دون ادعاء اعتماد قانوني |
| Kurdish | RTL | تمدد labels وتطابق الحروف |
| Turkmen | LTR | طول النص في badges والأزرار |
| Assyrian | RTL | اتجاه الحقول والخطوط الاحتياطية |
| Persian | RTL | جاهزية مستقبلية؛ لا تُفعل دون مورد ترجمة ومراجعة |

لا يترجم النظام معرّفًا أو رقمًا أو قيمة سريرية بطريقة تغير معناها. التواريخ تعرض بتنسيق locale لكن تخزن داخليًا UTC عند الحاجة.

## 6. Permission Map

| permission | نطاق | القراءة | الكتابة/الانتقال | مصدر القرار |
|---|---|---|---|---|
| `encounter.read` | Encounter داخل workspace | نعم عند scope | لا | Backend authorization |
| `encounter.create` | إنشاء Encounter | لا ينشئه frontend وحده | نعم عند workflow | Backend + audit |
| `encounter.update` | تحديث نسخة حالية | نعم عند scope | versioned update | Backend + audit |
| `encounter.close` | الإغلاق | ملخص قبل الإغلاق | transition فقط | Backend mandatory requirements |
| `queue.read` | queue للمؤسسة/المنشأة | نعم | لا | Backend scope |
| `queue.assign` | تعيين أو نقل في queue | حسب الدور | نعم عند العقد | Backend policy |
| `triage.read` | Triage fields | نعم | لا | Role + context |
| `triage.update` | Triage fields | نعم | نعم عند العقد | Backend state machine |
| `order.create` | طلب مرتبط بالزيارة | نعم عند scope | نعم | Backend order policy |
| `result.read` | نتائج مرتبطة | نعم عند scope | لا | Clinical gateway + Backend |
| `result.review` | مراجعة/اعتماد | نعم | نعم عند role | Backend authorization |
| `timeline.read` | أحداث الزيارة | نعم عند scope | لا | Audit/event policy |
| `referral.create` | إحالة | نعم | نعم دون افتراض القبول | Backend referral policy |

لا توجد صلاحيات speculative. القيم أعلاه تمثل map تصميمية وتحتاج مطابقة مع catalog الفعلي قبل تفعيلها.

## 7. Audit Map

| الحدث | before | after | actor | source | audit requirement |
|---|---|---|---|---|---|
| Check-in request | appointment/arrival state | server decision | session actor | UI/API | immutable request + decision |
| Queue assignment | queue state | assigned/waiting state | authorized actor | workflow | reason + workspace |
| Triage update | versioned fields | new version | clinical actor | UI/API | before/after + version |
| Note append | current note revision | new revision | clinical actor | UI/API | append-only reference |
| Order create | none/draft | submitted order | authorized actor | UI/API | idempotency + source |
| Result review | Available | Reviewed or rejected | authorized reviewer | backend | reviewer + timestamp |
| Referral send | draft | sent | authorized actor | backend | destination and reason |
| Close | active encounter | completed/discharged | authorized actor | workflow | mandatory fields + before/after |
| Forbidden attempt | attempted action | rejected | actor/session | API/UI | violation trace |

كل audit event يجب أن يتضمن user/actor ID، timestamp، action، entity، before state، after state، organization، facility، workspace، request ID، وسبب الرفض عند الفشل، بحسب العقد النهائي.

## 8. Error States

| الحالة | الرسالة التصميمية | الإجراء المسموح |
|---|---|---|
| Loading | جارٍ تحميل نطاق الزيارة | skeleton فقط |
| Empty | لا توجد زيارات ضمن نطاقك | تغيير filter المسموح |
| Waiting | بانتظار دور Backend | لا انتقال يدوي |
| In Progress | الزيارة قيد المعالجة | عرض خطوة server-confirmed |
| Pending | الطلب أو النتيجة قيد الانتظار | تحديث read-only |
| Completed | اكتملت العملية | ملخص لا يعني صلاحية جديدة |
| Cancelled | ألغيت | عرض السبب إذا سمح |
| No-show | لم يسجل الحضور | لا إنشاء Encounter تلقائي |
| Unauthorized | تتطلب تسجيل دخول | إعادة مصادقة |
| Forbidden | لا تملك الصلاحية أو النطاق | لا bypass |
| Expired Session | انتهت الجلسة | إعادة المصادقة |
| Offline | الخدمة غير متاحة محليًا | read-only/degraded policy |
| Service Unavailable | تعذر الاتصال بالخدمة | retry آمن دون duplicate side effect |
| Conflict | تغيرت النسخة أو الحالة | reload/resolve صريح |

## 9. Prototype Scenarios

Prototype Stitch يجب أن يستخدم أسماء عامة وبيانات اصطناعية غير قابلة للتعرف، ويمنع تنفيذ API أو كتابة سريرية. السيناريوهات المطلوبة هي: Appointment إلى Check-in إلى Queue إلى Encounter؛ Walk-in؛ Unauthorized؛ Wrong Facility؛ Expired Session؛ Offline؛ Cancelled؛ No-show؛ وService Failure. كل CTA في Prototype إما يغير حالة بصرية محلية واضحة أو يعرض `BACKEND_DEPENDENCY`، ولا يدّعي نجاحًا سريريًا.

## 10. Status Register

| العنصر | الحالة | السبب |
|---|---|---|
| Information Architecture | READY_FOR_REVIEW | وثيقة قابلة للمراجعة |
| Components and flows | READY_FOR_REVIEW | تصميم بدون side effects |
| Permission and audit map | READY_FOR_REVIEW | خريطة متطلبات وليست grant |
| Stitch prompts/prototype | READY_FOR_REVIEW | بيانات اصطناعية وبدون API |
| Patient/Appointment/Queue production data | BACKEND_DEPENDENCY | العقد غير مثبت |
| Triage/Orders/Results/Close writes | BLOCKED | state machine/version/audit/authz غير مثبتة للواجهة |
| Citizen visit summary | BACKEND_DEPENDENCY | policy-filtered contract غير مثبت |

لا يؤدي هذا التصميم إلى بدء P5 أو تفعيل Clinical Gateway، ولا يغيّر حالة أي Feature Flag.
