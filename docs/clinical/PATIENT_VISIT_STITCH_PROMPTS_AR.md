# PATIENT VISIT STITCH PROMPTS

## تعليمات مشتركة لكل موجّه

صمّم واجهة GULA عربية أولًا `RTL`، متجاوبة على desktop/tablet/mobile، مع WCAG 2.2 AA، أهداف لمس لا تقل عن 44×44px، تركيز مرئي، نصوص بجانب الألوان، ودعم العربية والإنجليزية والكردية والتركمانية والسريانية. استخدم بيانات اصطناعية عامة مثل `Patient A` و`Facility 01` ولا تستخدم أسماء أو أرقامًا حقيقية أو بيانات سريرية قابلة للتعرف.

اعتبر التصميم prototype بصريًا فقط. لا تنفذ API، ولا تحفظ بيانات، ولا تنشئ Encounter حقيقيًا، ولا تفترض صلاحية أو قبول جهة أو تحقق هوية. اعرض كل ما يحتاج Backend Contract كحالة `BACKEND_DEPENDENCY`. اجعل المؤسسة والمنشأة والقسم ومساحة العمل والدور والصلاحية واضحة في النطاق البصري، لكن لا تجعل الواجهة مصدر القرار. لا تضف OCR أو NFC أو biometrics أو سجلًا حكوميًا أو دفعًا.

## Prompt A — Patient Visit Information Architecture

أنشئ لوحة معلومات عربية باسم `GULA Patient Visit — Information Architecture` توضح الفرق بين Appointment وEncounter في مسارين متوازيين. اعرض مخططًا من Appointment/Walk-in إلى Check-in إلى Verification إلى Queue إلى Encounter، ثم شريط حالات: Scheduled، Arrived، Checked-in، Waiting، In Consultation، Completed، Cancelled، No-show، Referred. استخدم labels عربية مع الإنجليزية الثانوية، وبطاقات حالة لا تعتمد على اللون وحده. ضع banner واضحًا: `Design prototype — no clinical operation`.

## Prompt B — Check-in وQueue

أنشئ شاشة desktop وشاشة mobile لمسار Check-in وWork Queue. اعرض فقط بيانات الحد الأدنى: patient label آمن، سبب الزيارة، الموعد أو Walk-in، organization، facility، department، practitioner عند توفره، وحالة verification. بعدها اعرض queue table على desktop وبطاقات على mobile تتضمن الدور، المريض، نوع الزيارة، الأولوية، وقت الوصول، وقت الانتظار، الحالة، والمهني المسؤول. أضف Search وFilter وPriority وStatus وPagination بصريًا فقط. صمّم حالات Loading وEmpty وForbidden وWrong Facility وExpired Session وOffline وConflict وService Unavailable.

## Prompt C — Encounter Unified Workspace

أنشئ صفحة Encounter موحدة متجاوبة بعنوان `GULA Encounter Workspace`. ضع Patient Header وVisit Summary ثم تبويبات أو أقسام: Chief Complaint، History، Vitals، Assessment، Diagnoses، Orders، Laboratory، Radiology، Medications، Procedures، Referrals، Clinical Notes، Documents، Timeline، Follow-up، Close Summary. اجعل كل قسم يحمل badge `Permission-scoped` وplaceholder `BACKEND_DEPENDENCY` عندما لا يكون العقد مثبتًا. لا تعرض زر اعتماد أو إغلاق فعلي؛ استخدم disabled state ورسالة أن Backend يحدد المتطلبات والانتقالات.

## Prompt D — Role Flows

أنشئ مجموعة شاشات توضح نفس Encounter مع اختلاف العرض حسب Doctor وNurse وTechnician وPharmacist وRadiologist وLaboratory Professional وAuthorized Administrator وCitizen/Patient. لا تنشئ سجل زيارة منفصلًا لكل دور. استخدم مقارنة مرئية لحقول `Can view` و`Can act when contract exists` و`Not granted automatically`. ضع تحذيرًا بأن نوع المؤسسة أو اسم الدور لا يمنح صلاحية سريرية.

## Prompt E — Timeline وAudit

أنشئ Timeline عربية للزيارة تعرض Check-in، Triage، Consultation، Order، Result، Medication، Referral، Procedure، Note، Discharge/Close. لكل حدث اعرض actor label آمن، time، source، status، وaudit reference placeholder. أضف حالات رفض انتقال، تعارض version، وجلسة منتهية. اجعل الخط الزمني read-only ولا تضف زر حذف أو تعديل.

## Prompt F — Patient View

أنشئ واجهة mobile وdesktop لمساحة المريض تعرض موعدي، حالة الوصول، الزيارة الحالية، ملخص الزيارة، التعليمات، الوصفات، الطلبات، النتائج المتاحة، والمتابعة. أخفِ الملاحظات والبيانات المقيدة خلف حالة `Policy-filtered by server`. صمّم empty state وpending results وno visit وforbidden وexpired session. لا تضف تسجيل مواطن أو تحقق وطني أو أي كاميرا/NFC/OCR.

## Prompt G — Prototype Failure Scenarios

أنشئ لوحات prototype لحالات Walk-in وUnauthorized وWrong Facility وExpired Session وOffline وCancelled وNo-show وService Failure. عند كل CTA استخدم تغييرًا بصريًا محليًا أو modal يوضح `No clinical operation was performed`. لا تستخدم fake success ولا تعرض نتيجة أو تشخيصًا أو وصفة كأنها حقيقية.

## Prompt H — Design Review Board

أنشئ صفحة مراجعة بعنوان `Patient Visit Readiness Board` تقسم العناصر إلى READY، READY_FOR_REVIEW، BACKEND_DEPENDENCY، BLOCKED. أدرج أسفل كل عنصر سبب الحالة: contract، permission، audit، version، feature flag، أو P4 gate. أضف جدولًا صغيرًا يربط Screen وRoute وAPI وMethod وRequest وResponse وPermission وOrganization وFacility وWorkspace وAudit وFeature Flag وError.
