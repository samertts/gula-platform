# تنفيذ Frontend Master Specification

## الملخص

تم تحويل Frontend Master Specification إلى طبقة موحدة فوق `frontend-v3` بدلاً من بناء واجهات منفصلة غير مترابطة. التنفيذ الحالي يثبت bootstrap وsession وworkspace وdomain-oriented routes وresponsive runtime state، ويستخدم Unified Clinical Journey & Frontend Design System ومعرض Screen-by-Screen الموجودين مسبقاً.

> الواجهة تعرض الخيارات والحالات؛ الخادم يقرر الصلاحيات والبيانات والانتقالات. ظهور route أو component لا يثبت authorization أو عقد backend أو جاهزية إنتاجية.

## ما تم تثبيته

أضيفت شاشة `/golden-path` كـ**خريطة جاهزية** للرحلة السريرية الذهبية. تعرض Identity وWorkspace وPatient Access وAppointment وEncounter وLab Order وSpecimen وResult وDoctor Review وCitizen Access وSharing/Revoke وAudit في ترتيب واحد، وتعلن صراحة أن الأساس الحالي جزئي ولا تستخدم عبارة `GOLDEN PATH PASSED` قبل اكتمال العقود والاختبارات عبر المجالات.

| مجال المواصفة | التنفيذ |
|---|---|
| APP-001 Bootstrap | `App.tsx` يحافظ على QueryClient وTheme وLocale وUpdateGate وAuth وAccessibility وRouter بالترتيب الحالي، مع defaults محدودة للقراءة وإعادة الاتصال دون تحميل كل modules. |
| Session/Demo | `AuthContext` يستعيد session وDemo marker وmembership وeffective permissions من الخادم، ويفشل مغلقاً عند خطأ العضويات. لا توجد صلاحية محلية بديلة. |
| WS-001 Workspace | `WorkspaceSelector` يقرأ المساحات من الخادم، يبدل فقط عبر `switchWorkspace`، ويعرض loading/empty/error/demo. لا يمكن اعتبار اختيار محلي سياقاً مهنياً صالحاً. |
| Runtime state | `AppRuntimeIndicator` يوضح Demo أو online/offline من حالة المتصفح فقط. لا يدّعي وجود outbox أو sync أو نجاح عملية سريرية. |
| Domain routes | أضيفت aliases آمنة لـ`/app/health` و`/app/appointments` و`/app/results` و`/workspace/doctor` و`/workspace/laboratory` و`/workspace/pharmacy`. تعرض هذه المسارات contract gate واضحاً ولا تقرأ بيانات أو تكتبها قبل اكتمال العقد. |
| Navigation | حراسة المسارات مركزية عبر `routePolicies`، والروابط لا تمنح صلاحيات. routes القديمة الآمنة تبقى مرتبطة بصفحاتها الحالية أو بواباتها المحكومة. |
| Screen-by-Screen | معرض تفاعلي اصطناعي يربط مواصفة الشاشات بالأدوار والمنصات، مع Welcome/Login/OTP/Citizen/Doctor/Nurse/Lab/Pharmacy/Hospital/Emergency/Admin/Web/Desktop. لا API ولا local clinical writes. |
| Clinical UX | `ClinicalStatePanel` و`ClinicalStatusBadge` و`PatientContextCard` و`CriticalAlertBanner` و`ClinicalTimeline` توحد loading/empty/error/forbidden/offline/conflict والـpriority دون اتخاذ قرار سريري. |
| Assistant | `GuideAssistant` محلي وcontext-aware من حيث المسار، لكنه لا يملك وصولاً مستقلاً للبيانات ولا ينفذ إجراءً حساساً. |
| Performance | lazy routes وcode splitting وprefetch للشفرة فقط وpagination كقاعدة تصميمية. لا يتم تحميل السجل الصحي كله أو تخزين mutable clinical data في cache محلي. |
| Generated governance | تم تحديث route contract map وdata-source inventory عبر مولدات المشروع بعد إضافة المسارات الجديدة. |

## حدود التشغيل

### ما يعمل الآن

تعمل المعاينة الاصطناعية للقراءة فقط، وتعمل شاشات shell والتنقل والحالات responsive وRTL/Dark/Accessibility وفق المكونات الموحدة. كما تعمل routes الحالية التي تملك عقود قراءة مثبتة، ومنها patients/orders عبر canonical workspace-scoped clinical gateway حيث تسمح السياسة والسياق بذلك.

### ما لا يفتح في هذه الموجة

لا تفتح الواجهة إنشاء حساب أو Person/Identity/Health Record، ولا OCR/NFC/Liveness أو government verification، ولا appointment booking حقيقي، ولا Encounter/Order/Prescription/Referral writes، ولا specimen/result validation، ولا dispensing، ولا bed allocation، ولا emergency dispatch/GPS/ePCR، ولا ICU telemetry، ولا audit mutation، ولا unrestricted AI tools، ولا offline clinical outbox جديد.

كل كتابة مستقبلية تحتاج API وrequest/response/errors/permissions/states/events، مع RBAC سياقي ونطاق tenant/organization/facility/department/relationship، وACID وversion/`If-Match` و`Idempotency-Key` وaudit append-only واختبارات state transition. لا تُستخدم `Last Write Wins` للبيانات السريرية الحساسة.

## التوطين والوصول

الـshell الحالي RTL-first ويدعم تبديل locale وtheme وreduced motion وkeyboard focus وARIA للحالات. النصوص العربية المضافة للمسارات الجديدة مقصودة للتجربة والتوثيق. قبل إطلاق كل مسار إنتاجي يجب إضافة موارده إلى i18n للعربية والإنكليزية والكردية والتركمانية والسريانية، مع date/time/unit formatting مركزي وعدم تسريب محتوى حساس إلى lock-screen notification.

## الاختبارات والإطلاق

تمت إضافة اختبارات لـ`AppRuntimeIndicator` و`DomainRouteContractGatePage`، واستمرت اختبارات Screen-by-Screen وnavigation وclinical primitives وAsyncBoundary. يجب أن تمر كل شاشة عبر contract/authorization/loading/empty/error/offline/sync/RTL/accessibility/responsive/dark-mode/audit/tests/performance بحسب نطاقها قبل rollout. استراتيجية الإصدار تبقى Development ثم QA ثم Internal ثم Pilot ثم نسب تدريجية مع rollback، ولا يحدث deploy تلقائي من هذا التغيير.

## الخطوة التالية

الـGolden Path التالي يجب أن يبدأ بعقود backend محدودة وقابلة للتدقيق لـappointment availability/hold/confirm ثم patient context ثم encounter lifecycle ثم lab order/result lifecycle، مع اختبارات cross-domain من المواطن إلى الطبيب إلى المختبر ثم عودة النتيجة للمواطن. بعد نجاحه على Web وMobile وDesktop يمكن توسيع domains دون تعديل Citizen Core.
