# تنفيذ Unified Clinical Journey & Frontend Design System

## الملخص

أضيفت طبقة أساس موحدة إلى `frontend-v3` لتقليل اختلاف التجارب بين مسارات المواطن والطبيب والمؤسسة والمختبر والصيدلية والأشعة والعيادة والمستشفى والطوارئ. التنفيذ لا يستبدل عقود backend ولا ينشئ صلاحيات محلية؛ بل يوحد طريقة عرض السياق والحالات والمكونات ويجعل نقص العقد أو منع الوصول واضحاً للمستخدم.

> القاعدة التشغيلية: Backend Domain ← API Contract ← State Machine ← Authorization ← UI State ← User Interaction.

## ما تم تثبيته

| الطبقة | التنفيذ |
|---|---|
| Design Tokens | توسعت `frontend-v3/src/index.css` لتضم عائلات الخطوط العربية/اللاتينية، ألوان info والحالات السريرية، spacing tokens من 4 إلى 64، touch target، shell/content/navigation utilities، وحالات critical/urgent/safe في Light وDark. |
| RTL وresponsive | بقي RTL أساس `body`، وأضيفت utilities للـshell والـnavigation مع احترام اتجاه اللغة، وtouch targets لا تقل عن 44px تقريباً، و`prefers-reduced-motion`. |
| Page states | أضيفت حالات موحدة loading وloaded وempty وpartial وoffline وsyncing وerror وunauthorized وforbidden وexpired وconflict وmaintenance في `ClinicalStatePanel`. |
| AsyncBoundary | أصبح يقبل `clinicalState` اختيارياً مع عنوان ووصف وaction، مع بقاء props والسلوك السابقين صالحين. لا يؤدي `loaded` إلا إلى عرض children، ولا يخفي الحجب أو التعارض أو الفشل. |
| Clinical primitives | أضيفت `ClinicalStatusBadge` و`PatientContextCard` و`CriticalAlertBanner` و`ClinicalTimeline` مع عقود Props وحالات restricted وARIA واضحة. |
| Clinical safety UX | التنبيه الحرج يعرض icon + label + priority ولا يعتمد على اللون وحده، ويفصل بين acknowledgement والإجراء. سياق المريض يعرض ملخصاً محدوداً لا السجل الكامل. |
| Shell | رُبط `DashboardLayout` بتوكنات `gula-shell` و`gula-topbar` و`gula-content`، وربطت Sidebar بـ`gula-nav-link` مع بقاء فلترة permissions وserver-reflected capabilities وprefetch كما هي. |
| Assistant layer | توسعت إرشادات GuideAssistant للمسارات السريرية والطوارئ والمستشفى والمختبر والصيدلية والأشعة والعيادة. يعلن المساعد أنه مرشد محلي بلا وصول مستقل إلى قاعدة البيانات ولا قرار سريري. |
| Doctor workspace | استُخدم `ClinicalStatePanel` في بطاقات القراءة السريرية للطبيب لتوحيد loading/error/forbidden/empty/loaded بدلاً من نصوص محلية متفرقة. |

## عقود المكونات

كل مكون مشترك يجب أن يحدد Props وstates وevents وaccessibility وresponsive behavior وerror/loading behavior ومتطلبات authorization. المكونات الجديدة لا تستدعي API ولا تعرف قاعدة البيانات؛ تنتظر ViewModel أو بيانات مصفاة من الصفحة أو domain layer.

`PatientContextCard` لا يقبل افتراضاً أن الاسم أو Health ID قابلان للعرض؛ يمكن تمرير `restricted` فيعيد حالة `forbidden`. `CriticalAlertBanner` لا يوفر زر اعتماد أو تنفيذ؛ يعرض حالة التنبيه فقط، ويؤكد أن الاستلام لا يساوي الإجراء. `ClinicalTimeline` يعرض الأحداث التي يقدمها النطاق الحالي، ويحوّل القائمة الفارغة إلى state معلنة بدلاً من شاشة فارغة.

## نموذج الحالة الموحد

| الحالة | معنى الواجهة | السلوك الآمن |
|---|---|---|
| loading | انتظار عقد أو سياق | لا تعرض بيانات جزئية على أنها مكتملة |
| loaded | بيانات ضمن النطاق | لا يمنح العرض صلاحية كتابة |
| empty | لا توجد عناصر ضمن النطاق | تعرض سبباً قابلاً للفهم |
| partial | جزء من البيانات فقط | تذكر ما هو غير متاح |
| offline | لا اتصال | لا تدعي أن البيانات حديثة |
| syncing | مزامنة معلقة | لا تخفي الأعمال المعلقة |
| error | فشل الطلب | لا تستخدم fallback سريرياً غير موثق |
| unauthorized | جلسة غير مصادق عليها | توجه لتسجيل الدخول دون كشف بيانات |
| forbidden | لا صلاحية أو سياق | لا تعرض زر تجاوز |
| expired | انتهت صلاحية السياق | تطلب إعادة تحميل السياق |
| conflict | تعارض نسخة أو حالة | تتطلب مراجعة صريحة ولا تستخدم Last Write Wins |
| maintenance | capability غير متاحة مؤقتاً | يستمر النظام غير المعتمد عليها |

## التنقل وWorkspace

لا يغير هذا التنفيذ نموذج NIAM. تسجيل الدخول لا يساوي دوراً، واختيار workspace لا يمنح صلاحية، ودور الطبيب لا يساوي الوصول إلى كل المرضى. يظل الخادم صاحب القرار النهائي في identity وmembership وfacility وdepartment وcare context وpurpose وpermission. إخفاء رابط أو زر هو UX defense فقط وليس authorization.

الـshell يوفر مكاناً ثابتاً للـWorkspaceContextHeader وGuideAssistant وMobileBottomNav، مع الحفاظ على اختلاف IA حسب الدور. لذلك لا تتم مطابقة كل تطبيق بصرياً، بل تتشارك المسارات قواعد الألوان والحالات والسياق والتدقيق، بينما يختلف التنقل وفق workspace والدور والجهاز.

## Assistant Layer

GuideAssistant الحالي إرشادي محلي ولا يتصل بذكاء اصطناعي أو قاعدة بيانات. عند توفر عقد AI مستقبلية يجب أن يكون المسار: User + Workspace + Authorization Context → Authorized Service → Filtered Context → AI، وليس AI → Database. يجب تسجيل ما يلزم من السؤال والسياق والإجابة والفعل البشري وفق سياسة الخصوصية، ويجب أن يبقى GULA مستمراً إذا تعطل المساعد.

علي رضا لا يقرر صلاحية أو وصولاً، ولا يفرز، ولا يشخص، ولا يوقع، ولا يعتمد، ولا يغير السجل، ولا ينشئ role أو workspace أو identity، ولا يتجاوز Break-Glass.

## ما لم يُفتح

لم يتم إنشاء واجهات كتابة سريرية عامة، ولا contracts جديدة في backend، ولا offline queue أو sync engine جديد، ولا feature flag server-side، ولا kill switch تشغيلي، ولا جلسات أو MFA أو privacy endpoints جديدة. هذه عناصر تحتاج عقوداً خادمية وتدقيقاً منفصلاً ولا ينبغي محاكاتها محلياً في Design System.

كما لم تتم إضافة بيانات أو صور أو تكاملات خارجية أو خرائط أو OCR أو biometrics أو government verification. صفحات Demo تبقى اصطناعية ومعزولة وقابلة للقراءة فقط.

## الاختبارات

تشمل الاختبارات الجديدة الحالات الموحدة للحجب والتحميل والـoffline والـtimeline والتنبيه الحرج، واختبار AsyncBoundary، واختبارات قابلية الوصول الحالية، مع استمرار اختبارات المسارات والـnavigation والعقود وحدود التكامل. يجب أن تغطي الجولة الكاملة lint وunification وcontract governance وintegration boundary وtypecheck وtest وbuild وdiff check وفحص الأسرار.

## الخطوة التالية

العمل التالي backend-first وليس إعادة نسخ الواجهة: تثبيت Foundation Contracts لـPatient Context وEncounter وAppointment وOrder وResult وMedication وConsent وAudit وOffline/Sync وAI، ثم بناء ViewModels typed فوقها، ثم إضافة feature flags وrollout وkill switch من الخادم. بعد ذلك يمكن توسيع نفس primitives إلى Nurse وAdministration وDesktop وMobile دون نسخ منطق authorization داخل كل عميل.
