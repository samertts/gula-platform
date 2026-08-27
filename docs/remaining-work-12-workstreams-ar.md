# سجل الفجوات للمهام الاثنتي عشرة السابقة

## الغرض

هذا السجل يحول طلب «تنفيذ كل ما لم يُنفذ» إلى مصفوفة قابلة للتحقق. لا يُعد أي عنصر مكتملًا لمجرد وجود صفحة أو زر؛ معيار الإكمال في GULA هو وجود عقد backend ونموذج بيانات وحالات رسمية وتفويض كائني وعزل tenant وتدقيق وتزامن وidempotency واختبارات API وFrontend وE2E وأمن ووصول وأداء، ثم نجاح الفحوص البعيدة قبل الدمج أو النشر.

> Demo في جميع المسارات اصطناعي ومعزول وقابل للقراءة فقط. الخادم هو مصدر الحقيقة للهوية والعضويات والمساحات والعلاقات والموافقات والصلاحيات والانتقالات السريرية.

## المصفوفة التنفيذية

| رقم | مسار سابق | ما تم إنجازه | ما لم يُنفذ بعد | سبب عدم التنفيذ أو الحجب | القرار التنفيذي |
|---:|---|---|---|---|---|
| 1 | المواطن والهوية | مركز الهوية والمساحات، قراءة memberships/workspaces المعادة من الخادم، consent withdrawal، Demo معزول، منع كشف المعرفات الوطنية الخام | OTP/session/device self-management، access history، إنشاء sharing، family/guardian، documents، insurance، government verification، OCR/NFC/liveness، deduplication، health-record discovery | تحتاج عقود self-service محددة، MFA/rate limits، أدلة تحقق واحتفاظاً وخصوصية وتكاملاً مفوضاً. لا يجوز أن تنشئ الواجهة هوية أو verification | أبقي المعاينة والبوابات؛ أضيف typed contract catalog واختبارات حالات فقط، ولا أفتح writes بلا عقد |
| 2 | الطبيب | Doctor workspace، workspace switch خادمي، قراءة patients/orders من canonical clinical gateway، fail-closed وبدون legacy fallback | appointment/calendar، patient-access decision، encounter/note/sign/amendment، lab order، result review، prescription، referral، follow-up، tasks، delegation | كل عنصر كتابة سريري يحتاج relationship/scope وstate machine وIf-Match وIdempotency-Key وaudit وسياسة توقيع | أبني خريطة Golden Path وعقود typed/guards؛ تظل العمليات gated |
| 3 | المؤسسة الصحية | workspace/membership display، Demo، حدود عدم إنشاء organization/role/membership من الواجهة | licensing/approval، branches/departments، invitations، role assignment، devices، inventory، finance، quality، complaints، access review | هذه قرارات IAM/organization خادمية وليست صلاحيات UI؛ تحتاج ownership وtenant scope وتدقيقاً | لا أفتح CRUD؛ أضيف contract readiness mapping فقط |
| 4 | المختبر | Lab operations Demo، Live workspaces وقراءة orders المحدودة، حجب LIS الخام | lab order lifecycle، accession/specimen، barcode/chain-of-custody، analyzer/QC/calibration، result validation/release، critical escalation، inventory/billing | لا يوجد frontend-safe LIS contract مع senior validation وimmutable result history وescalation/audit | أضيف state-machine types وnegative tests، ولا أرسل نتائج أو أستقبل عينات حقيقية |
| 5 | الصيدلية | Demo read-only، Live summary/catalog/stock المحدود، حجب dispense/POS | prescription verification، interaction/allergy checks، pharmacist decision، batch/expiry، partial dispensing، controlled medicines، medication record، returns/recalls | الصرف أثر سريري/مخزني ومالي؛ يتطلب authorization، batch ledger، idempotency، concurrency، audit وseparation of duties | لا أفتح أزرار صرف؛ أكتفي بمعاينة وحالات contract gate |
| 6 | الأشعة | Demo، Live metadata محدود، منع DICOM/PACS/report/sign/download | imaging order، scheduling، study/performed، report lifecycle، verification/release، DICOM/PACS، sharing، amendments، dose workflow | التكامل يحتاج RIS/PACS/DICOM وobject authorization وخصوصية للصور وتوقيعاً وتدقيقاً | أبقي metadata/gate؛ لا أختلق URLs أو تقارير أو صوراً |
| 7 | العيادة والـEncounter | Clinic operations Demo، Live patients/orders المحدود، حالات محجوبة | appointment/queue، check-in، encounter، note، diagnosis، orders، prescription، referral، care plan، telemedicine، billing | لا توجد عقود workspace-scoped مكتملة؛ فتح الكتابة من adapter عام يخرق boundary | أضيف typed readiness وواجهة حالات؛ لا clinical write |
| 8 | المستشفى | Hospital Operations Demo، `/hospital` صار alias آمناً، Live patients/orders فقط، حجب CRUD legacy | admissions، beds/occupancy، ward/nursing/eMAR، OR، ICU، blood bank، discharge، live audit | broad `/hospital/*` ليس frontend-safe؛ العمليات عالية الخطورة تحتاج facility/ward scope وstate machine وIf-Match وidempotency | لا أوصل broad endpoints؛ أجهز contract backlog واختبارات gate |
| 9 | الطوارئ والإسعاف والرعاية الحادة | Acute Care Demo، `/ems` و`/critical-care` aliases آمنة، Live patients/orders فقط | emergency encounter، temporary identity، triage، break-glass، dispatch/GPS/ePCR، pre-alert/handover، ICU telemetry، critical escalation | break-glass والـEMS تتطلب سبباً إلزامياً وdataset محدوداً وتنبيهاً وتدقيقاً وانتهاءً تلقائياً وتكاملاً مفوضاً | تبقى جميعها gated؛ لا اتصال إسعاف أو GPS حقيقي |
| 10 | Unified Clinical Journey & Design System | tokens، RTL/dark/reduced-motion، clinical states/primitives، AsyncBoundary، shell، GuideAssistant، runtime indicator | i18n الكامل لكل الموارد الخمسة، visual regression، device parity، production telemetry، formal component governance | بعض هذه العناصر تحتاج product/content review وبيئات Web/Mobile/Desktop وremote observability | أستكمل typed status/state catalog واختبارات الوصول، دون ادعاء parity إنتاجية |
| 11 | Screen-by-Screen | معرض تفاعلي اصطناعي للأدوار والمنصات، gated states، lazy route، prefetch code-only | كل شاشة domain-aware حقيقية، backend bindings، mobile/desktop native packaging، E2E عبر بيئات حقيقية اصطناعية | الشاشة وحدها لا تثبت contract أو authorization أو integration أو store readiness | يبقى المعرض مرجع UX؛ المسارات الحية تظل مصدر الحقيقة |
| 12 | Frontend Master / Golden Path | domain routes، contract gate، Golden Path Readiness، governance artifacts، 39 ملف اختبار/129 اختباراً في آخر تحقق | Appointment → Encounter → Lab → Result → Review → Citizen → Share → Revoke → Audit كرحلة E2E حقيقية، backend contracts، remote CI، staging/canary | هذا هو الفرق بين readiness وproduction؛ العقود الحالية تقبل patients/orders فقط، والـremote PR ما يزال UNSTABLE | أبدأ typed contract registry وnegative/security fixtures، ولا أعلن GOLDEN PATH PASSED |

## فجوات مشتركة لم تُغلق

### العقود الخلفية

لا تزال العقود المجالّية الرسمية للمواعيد والجلسات والأجهزة والوصول الكائني والإنابة والمهام وEncounter وClinical Note وLab Order وSpecimen وResult وCritical Result وNotification وAudit الحي غير مقبولة داخل frontend safety boundary. وجود wrappers قديمة في `src/api/endpoints.ts` لا يجعلها عقوداً آمنة؛ المرجع الفعلي هو allowlist والـcanonical gateway في `src/api/client.ts` و`workspaceScopedReads.ts`.

### الاختبارات العابرة للمجالات

الاختبارات الحالية تثبت العزل والحجب والقراءات المحدودة، لكنها لا تثبت رحلة end-to-end خادمية حقيقية لأن endpoints الكتابة والعقود المتسلسلة غير متاحة. لذلك لا يمكن تسمية Golden E2E ناجحاً، ولا يجوز إنشاء بيانات اختبار تشبه مواطنين حقيقيين أو الاتصال ببيئة إنتاج.

### التوطين والمنصات

الأساس RTL ويدعم Light/Dark وresponsive، لكن parity الكامل بين العربية والإنكليزية والكردية والتركمانية والسريانية، إضافة إلى تطبيق Mobile/EXE فعلي وتوقيع المتاجر، يحتاج موارد ترجمة ومراجعة بشرية وبيئات بناء وحسابات نشر ومدخلات مالك. لا يجوز استخدام ترجمة آلية غير مراجعة في نصوص طبية حساسة أو ادعاء نجاح store pipeline دون حسابات وتوقيعات وفحوص بعيدة.

### الأمن والتشغيل الخارجي

Dependabot #471 ما يزال مفتوحاً ولم يُخفَ أو يُdismiss، وحالة PR #250 البعيدة `UNSTABLE`. لا يمكن إصلاح Code Scanning أو Remote CI من خلال إخفاء التنبيهات أو تجاوز billing/runner restrictions. Telegram token السابق لا يُستخدم؛ أي ربط إشعارات يحتاج token جديداً يديره المالك، عقد notification خادمي، opt-in، redaction، rate limit، audit، وfailure isolation.

### النشر والبيانات الحقيقية

لم يحدث merge أو deploy أو store submission أو ربط حكومي أو HIS/LIS/RIS/PACS أو استعمال بيانات حقيقية. السبب هو أن هذه أفعال خارجية حساسة تحتاج موافقة صريحة، أسراراً ومدخلات مالك وبيئة staging وsmoke test وrollback وremote CI ناجحاً، كما أن المواصفة نفسها تمنع اعتبار الاختبار المحلي دليلاً على production readiness.

## ما يمكن تنفيذه محلياً الآن بأمان

يمكن تنفيذ typed domain contracts وstate-machine guards وrequest/response/error fixtures، وتوسيع negative/security/accessibility tests، وتحسين contract gates وUX states، وتدقيق route/data-source inventories، وتوثيق runbooks وmigration plans. هذه الأعمال لا تفتح صلاحيات ولا تستبدل تحقق الخادم، لكنها تقلل الغموض وتمنع إضافة واجهات وهمية.

أما ما لا يمكن تنفيذه بأمان من الواجهة وحدها فهو إنشاء الأدوار والمساحات والعلاقات والتحققات والموافقات والسجلات الصحية، أو تشغيل appointment/encounter/lab/prescription/dispense/emergency/audit writes، أو الادعاء بتكامل حكومي أو DICOM/PACS أو SMS/Telegram حي، أو اعتبار Remote CI وDependabot محلولين دون صلاحية ونجاح فعلي.

## معيار الإغلاق

يُغلق كل صف فقط عندما تتوفر أدلة قابلة لإعادة الإنتاج على: Domain/Data Model، State Machine، Authorization/Object-Level Authorization، Tenant Isolation، API/Error Contract، Audit، Idempotency، Concurrency، Rate Limits، Frontend states، RTL، Accessibility، Offline policy، Unit/Integration/Contract/E2E/Security/Performance tests، ثم Remote CI وStaging smoke test وRollback plan. وحتى ذلك الوقت يستخدم التصنيف `Blocked / Placeholder / Demo-only` وليس `Completed`.
