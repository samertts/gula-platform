# PATIENT VISIT BACKEND CONTRACT MAP

## قاعدة القراءة

هذه الخريطة لا تعتبر تشابه أسماء المسارات إثباتًا لعقد API. المسار الخادمي الموجود باسم `encounter-management` حاليًا يعيد stubs عامة، ولا يثبت علاقة المريض بالمؤسسة والمنشأة ومساحة العمل أو انتقالات Encounter أو التفويض متعدد السياقات. لذلك تُصنف شاشات الزيارة التشغيلية `BACKEND_DEPENDENCY` أو `BLOCKED` حتى يثبت عقد typed واختبار عزل وتدقيق.

## الخريطة الرئيسية

| الشاشة | Route مقترح/قائم | API وHTTP | Request | Response | Permission | Organization / Facility / Workspace | Audit | Feature Flag | Error | الجاهزية |
|---|---|---|---|---|---|---|---|---|---|---|
| Appointment list | `/patient-management?tab=appointments` قائم تجريبي | لا يوجد عقد موثق؛ لا تعتمد `/appointments` generic | غير موثق | غير موثق | غير موثق | غير موثق | غير موثق | غير موثق | 401/403/404/409/503 مطلوبة | BACKEND_DEPENDENCY |
| Walk-in intent | `/patient-visit/check-in` جديد | غير موجود كعقد موثق | Patient/appointment or walk-in context، idempotency key | Check-in decision + status + encounter reference عند السماح | CheckIn.Create | مطلوب الثلاثي organization/facility/workspace | إلزامي | `patient_visit_check_in` مقفول افتراضيًا | 400/401/403/404/409/422/503 | BACKEND_DEPENDENCY |
| Check-in detail | `/patient-visit/check-in/:id` جديد | غير موجود | encounter/appointment reference | minimal patient + reason + organization/facility/department/practitioner + verification state | Encounter.Read + CheckIn.Read | مطلوب | قراءة تدقيقية | نفس العلم | 401/403/404/409 | BACKEND_DEPENDENCY |
| Queue | `/patient-visit/queue` جديد | غير موجود | cursor/page، filters، workspace context | scoped entries + pagination + server time | Queue.Read | مطلوب | قراءة تدقيقية عند البحث الحساس حسب السياسة | `patient_visit_queue` مقفول | 401/403/409/429/503 | BACKEND_DEPENDENCY |
| Triage | `/patient-visit/:id/triage` جديد | غير موجود | validated triage payload + version | saved triage + transition result | Triage.Read/Create/Update حسب الدور | مطلوب | before/after + actor + reason | `patient_visit_triage` مقفول | 400/403/409/422/503 | BLOCKED حتى يوجد contract رسمي وقياس معتمد |
| Encounter header | `/patient-visit/:id` جديد | national Encounter model موجود داخليًا، لكن UI contract غير مثبت | encounter ID + workspace context | scoped header + status + participants | Encounter.Read | مطلوب | read audit | `patient_visit` مقفول | 401/403/404/409 | BACKEND_DEPENDENCY |
| Clinical notes | `/patient-visit/:id/notes` جديد | غير مثبت | append note + current version + idempotency key | note revision + audit reference | ClinicalNote.Create/Read | مطلوب | immutable append audit | `patient_visit_notes` مقفول | 403/409/422/503 | BLOCKED |
| Orders | `/patient-visit/:id/orders` جديد | `/orders` قائم لكنه لا يثبت relation to Encounter | typed order + encounter ID + version | order state + source + audit reference | Order.Create/Read | مطلوب | إلزامي | `patient_visit_orders` مقفول | 400/403/409/422/503 | BACKEND_DEPENDENCY |
| Results | `/patient-visit/:id/results` جديد | `/results` محجوب/غير مثبت | encounter ID + scoped filters | Pending/Available/Reviewed scoped results | Result.Read؛ validation server-only | مطلوب | قراءة واعتماد عند Backend | `patient_visit_results` مقفول | 401/403/404/409/503 | BLOCKED |
| Timeline | `/patient-visit/:id/timeline` جديد | غير موجود | encounter ID + cursor | immutable event list: actor/time/source/status | Timeline.Read | مطلوب | المصدر هو audit/event log | `patient_visit_timeline` مقفول | 401/403/404/503 | BACKEND_DEPENDENCY |
| Follow-up | `/patient-visit/:id/follow-up` جديد | غير موجود | follow-up fields + encounter ID | follow-up decision/reference | FollowUp.Create | مطلوب | إلزامي | `patient_visit_follow_up` مقفول | 403/409/422/503 | BACKEND_DEPENDENCY |
| Referral | `/patient-visit/:id/referral` جديد | national referral model موجود؛ UI contract غير مثبت | destination/reason/priority/receiving org/facility | referral status؛ لا يفترض القبول | Referral.Create/Read | مطلوب | إلزامي | `patient_visit_referral` مقفول | 403/409/422/503 | BACKEND_DEPENDENCY |
| Close encounter | `/patient-visit/:id/close` جديد | national Encounter service/workflow موجود جزئيًا؛ UI contract غير مثبت | current version + close summary + required fields | closed status + mandatory requirements | Encounter.Close | مطلوب | immutable before/after audit | `patient_visit_close` مقفول | 403/409/422/503 | BLOCKED |
| Patient view | `/citizen/visits/:id` غير مثبت | citizen surface generic وغير موثق | visit ID | policy-filtered summary | CitizenVisit.Read | organization/workspace boundary حسب العقد | read audit حسب السياسة | `citizen_visit_view` مقفول | 401/403/404/503 | BACKEND_DEPENDENCY |

## عقود الانتقال المطلوبة

يجب أن يقدم Backend جدولًا صريحًا للانتقالات، وليس مجرد endpoint عام:

| من | إلى | شروط إلزامية | صلاحية أو سياسة | تدقيق |
|---|---|---|---|---|
| Scheduled | Arrived | appointment موجود أو walk-in policy | CheckIn.Read/Arrive | actor/time/source |
| Arrived | Checked-in | verification + facility/workspace match | CheckIn.Create | before/after |
| Checked-in | Waiting | queue assignment accepted | Queue.Assign | queue audit |
| Waiting | In Consultation | assigned practitioner/workflow gate | Encounter.Start | actor/time |
| In Consultation | Completed | close requirements | Encounter.Close | before/after |
| أي حالة | Cancelled | cancellation policy وسبب | Appointment/Encounter.Cancel | reason |
| Scheduled | No-show | attendance policy ووقت/تعريف رسمي | Appointment.MarkNoShow | actor/time |
| Encounter | Referred | referral contract accepted for send only | Referral.Create | destination/source |

أي انتقال خارج الجدول يجب أن يعيد hard failure مناسبًا، ويجب أن يسجل محاولة مخالفة لا أن يصححها بصمت.

## الحد الأدنى لـRequest/Response

كل طلب تشغيلي يحتاج `request_id` و`idempotency_key` عند الكتابة، و`workspace_id` أو سياق مساحة العمل المستخرج خادميًا، ومعرّف المؤسسة والمنشأة عند الحاجة، و`expected_version` لتعارضات التحديث. لا يرسل frontend قرار الصلاحية أو حالة العضوية كقيمة موثوقة.

كل استجابة تشغيلية يجب أن تعيد حالة typed، مع `resource_id` و`version` و`server_time` و`audit_reference` عند الكتابة، ورسالة خطأ قابلة للترجمة دون كشف بيانات حساسة. لا يكفي `{success: true}` أو `{id: ""}` كعقد سريري.

## نموذج الأخطاء

| HTTP | معنى الواجهة | السلوك |
|---|---|---|
| 400 | طلب غير صالح | إبراز الحقول دون تخطي state machine |
| 401 | جلسة منتهية | حفظ المسودة المحلية غير الحساسة فقط ثم إعادة المصادقة |
| 403 | ممنوع | لا تعرض زرًا بديلًا يتجاوز القرار |
| 404 | غير موجود أو غير مرئي | لا تكشف وجود tenant آخر |
| 409 | تعارض version أو انتقال | إعادة تحميل آمنة ومسار حل صريح |
| 422 | تحقق أعمال فشل | عرض السبب القادم من Backend |
| 429 | حد طلب | retry policy مرئية دون تكرار side effect |
| 503 | خدمة غير متاحة | degraded/read-only state ولا كتابة سريرية محلية غير معتمدة |

## Feature Flags

كل سطح Patient Visit جديد يجب أن يكون server-controlled ومقفولًا افتراضيًا. لا يكفي علم frontend. لا يفعّل العلم أي تسجيل مواطن أو تحقق وطني أو OCR أو NFC أو biometric أو government registry. أي flag غير موجود في Backend Contract يبقى `BACKEND_DEPENDENCY`.

## القرار

لا يجوز استخدام هذه الخريطة كترخيص لتنفيذ API أو migration. هي قائمة متطلبات تعاقدية. بعد اعتمادها، يجب إنشاء عقود typed واختبارات policy وtenant isolation وaudit وversion conflict في دفعات مستقلة، ثم يمكن تحويل الأسطح من `BACKEND_DEPENDENCY` إلى `READY_FOR_IMPLEMENTATION` بالتدريج.
