# تنفيذ التصميم الفعلي للواجهات الأمامية Screen-by-Screen

## القرار التنفيذي

أضيف route آمن باسم `/screen-by-screen` داخل `frontend-v3`. هذا route هو **معرض تفاعلي اصطناعي للقراءة فقط** يتيح معاينة الشاشات حسب الدور والمسار والجهاز، بدلاً من نسخ عشرات الصفحات إلى routes منفصلة أو إنشاء عمليات محلية توحي بأنها حقيقية.

> المعرض يثبت تصميم الشاشة وتفاعلها وحالاتها، لكنه لا يثبت توفر backend contract أو صلاحية المستخدم أو جاهزية الإنتاج.

تم اختيار تصميم `Clinical Command Gallery`: تنقل أفقي للأدوار، قائمة شاشات جانبية، مرحلة عرض responsive، مؤشرات حالة موحدة، وأسطح مستقلة لـmobile/desktop. يعتمد العرض على `Unified Clinical Journey & Frontend Design System` ولا يستدعي API ولا يغير workspace أو session.

## مصفوفة الشاشات

| المجموعة | الشاشات المنفذة في المعرض | حدود التشغيل |
|---|---|---|
| البداية والوصول | Welcome، Login، OTP، New Device، Identity Journey | المعاينة لا تسجل الدخول ولا ترسل OTP ولا تقرأ OCR/NFC ولا تشغل Liveness |
| المواطن | Citizen Home، Health Timeline، Lab Result، Appointments، Sharing، Security | البيانات اصطناعية؛ مشاركة البيانات وإلغاءها والموعد والنتيجة الحية تمر عبر عقودها فقط |
| الطبيب | Doctor Dashboard، Patient Context، Encounter Workspace | patients/orders فقط يمكن أن تأتي من canonical gateway في المسارات الحقيقية؛ لا Encounter أو Sign محلي |
| الممرض | Nurse Dashboard، Nurse Patient | Vitals وMedication Administration وHandover معروضة كحالات مقيدة ولا تحفظ محلياً |
| المختبر | Lab Dashboard، Worklist، Result Validation | لا accession أو analyzer أو validation أو critical notification حي |
| الصيدلية | Pharmacy Dashboard، Verification/Dispensing | Verification منفصل عن Dispensing، ولا approve/reject/dispense أو stock mutation |
| المستشفى | Hospital Dashboard، Bed Management/Detail | occupancy والبنية التشغيلية Demo؛ لا admission أو bed allocation أو transfer |
| الطوارئ والإسعاف | Emergency Dashboard، Ambulance App، ICU Dashboard | لا Dispatch أو GPS أو ePCR أو Break-Glass أو ICU telemetry أو interventions |
| الإدارة | Admin Dashboard، Audit Viewer | لا role assignment أو policy mutation أو قراءة audit شاملة |
| Web/Desktop | Web Portal، Desktop Master/Detail | large datasets تعرض server pagination كتصميم؛ لا جلب مليون سجل ولا raw storage |

## الشاشة الأولى ومسار الوصول

عند دخول مستخدم Demo إلى `/screen-by-screen` يظهر عنوان واضح يذكر أن المعرض اصطناعي وقراءة فقط. يختار المستخدم الدور، ثم الشاشة، ثم يرى المرحلة التفاعلية. كل زر تنقل يبدل حالة المعرض محلياً فقط، ولا يعتبر حجزاً أو اعتماداً أو توقيعاً أو حفظاً.

تم تسجيل route في `routePolicies` تحت `READONLY_ROLES`، وأضيف إلى navigation كمدخل قراءة فقط. وتمت إضافته إلى prefetch كتحميل للـchunk دون API calls. المواطن لا يحصل تلقائياً على مسار المؤسسة أو معرض الأدوار الداخلية؛ صلاحيات الوصول في الواجهة دفاعية، والخادم هو صاحب القرار النهائي.

## حالات الحالات السريرية

كل شاشة حساسة تعرض على الأقل حالة loaded أو partial أو empty أو forbidden بحسب طبيعتها. حالات الحجب تستخدم النص والأيقونة واللون معاً. التنبيه الحرج لا يساوي إجراءً، و`acknowledgment` لا يساوي علاجاً أو اعتماداً. الرسوم الاصطناعية، مثل اتجاه SpO₂، تعرض الوحدة والوقت والمصدر في النص المساعد ولا تعتمد على اللون وحده.

حالات login وOTP وnew-device وidentity لا تدعي نجاحاً وهمياً. OCR وNFC والقارئ الخارجي وSelfie/Liveness وIdentity Resolution معروضة كـmaintenance/forbidden حتى تتوفر integrations مفوضة وتتحقق من type/size/malware/authorization/audit حيث يلزم.

## التوطين وإمكانية الوصول

المعرض RTL-first في النص الحالي، وكل role/screen button قابل للوصول بلوحة المفاتيح وله حالة `aria-pressed` أو `aria-current` حيث يلزم. الحالات السريرية تستخدم `role=status` أو `role=alert`، مع ألوان متوافقة مع dark mode. تقسيم Desktop يوضح Sidebar وMaster/Detail، بينما mobile يحافظ على قائمة لمس قصيرة ولا يعيد استخدام navigation معقدة في واجهة الإسعاف.

النصوص الخاصة بالمعرض اصطناعية ومقصودة للتوثيق البصري. عند نقل أي شاشة إلى مسار إنتاجي يجب نقل النصوص إلى i18n resources للعربية والإنكليزية والكردية والتركمانية والسريانية، وتطبيق formatting مركزي للتاريخ والوقت والعملة والوحدات الطبية بدلاً من النصوص المحلية.

## Backend وauthorization

المعرض لا يفتح endpoints جديدة. المسارات الحقيقية تظل مسؤولة عن اختيار workspace وتفعيل السياق وقراءات patients/orders من canonical clinical gateway. لا يعني ظهور شاشة الطبيب أو الممرض أو الإدارة أن الدور يملك كل سجلات المؤسسة. الوصول الفعلي يحتاج session وworkspace وtenant وfacility وdepartment وrelationship وpurpose وpolicy وaudit من الخادم.

أي شاشة كتابة مستقبلية يجب أن تكون خلف contract محدد مع state machine، validation، RBAC سياقي، نطاق المنشأة، `If-Match`، `Idempotency-Key`، ACID transaction وتدقيق immutable. لا يجوز جعل زر المعرض بديلاً عن هذه الحواجز.

## الأداء

المعرض lazy-loaded عبر route مستقل، ولا يدخل في bundle الأساسي إلا عند فتحه. لا يستخدم صوراً كبيرة أو وسائط محلية، ولا يضع سجلات كبيرة في DOM. جدول Worklist وMaster/Detail يشرحان server-side pagination وdebounce/query cancellation كتصميم مستقبلي، ولا ينفذان تحميل بيانات حقيقية.

## الاختبارات

أضيفت اختبارات route المعرض لتثبت عرض شاشة البداية الاصطناعية، تبديل دور المواطن والوصول إلى نتيجة محكومة، تبديل الطوارئ والوصول إلى تطبيق الإسعاف، وبقاء العمليات الحساسة معلنة كمحجوبة. كما استمرت اختبارات navigation وGuideAssistant وclinical primitives وAsyncBoundary.

## ما بعد هذا التنفيذ

الخطوة التالية ليست إضافة أزرار fake، بل تحويل الشاشات ذات الأولوية إلى عقود backend محدودة: appointment search/hold/confirm، patient context، encounter lifecycle، order/result lifecycle، medication verification، emergency encounter/triage/handover، audit viewer purpose-limited، وfeature flags server-side. بعد كل عقد يضاف ViewModel typed واختبارات contract وauthorization وoffline/error/accessibility قبل rollout تدريجي.
