# مصفوفة التكافؤ عبر المنصات في GULA

**الإصدار:** 1.0 — 18 آب/أغسطس 2026
**الحالة:** evidence-based؛ لا تعني نجاحاً إنتاجياً أو اعتماداً وطنياً

## قاعدة التصنيف

> **PASS** يعني أن السطح بُني واختُبر بالأدلة المتاحة. **UNVERIFIED** يعني أن البناء أو الاختبار لم يكتمل بسبب بيئة أو صلاحية خارجية. **NOT_BUILT** يعني أن السطح غير موجود أو لم تُنفذ وظيفته بعد. لا تُحوّل أي من الحالتين الأخيرتين إلى PASS.

| السطح | المواطن/الأسرة | الطبيب/المختبري | المؤسسة | الحالة المثبتة |
|---|---|---|---|---|
| Web/PWA | Citizen Workspace، family، notifications، account-request UI | Clinical Workspace للمرضى والطلبات، `results.read` لعرض DTO النتائج، Lab Operations مع بيانات اصطناعية معزولة | Institution Workspace وروابط الوحدات | **PASS محلياً للعقود والواجهة**: TypeScript/build، اختبارات العقد، ESLint، bundle budget؛ E2E الإنتاجي UNVERIFIED |
| Android Kotlin/Compose | لا توجد أدلة parity محدثة للدفعات الجديدة | لا توجد أدلة parity محدثة للدفعات الجديدة | signing CI-only، لا يوجد keystore متتبع | **UNVERIFIED**: CI infrastructure وrotation الخارجيان غير مغلقين |
| Flutter Android/iOS | لا توجد أدلة parity محدثة للدفعات الجديدة | لا توجد أدلة parity محدثة للدفعات الجديدة | لا يوجد إثبات تشغيل متطابق للدفعات الجديدة | **UNVERIFIED**: native CI لم ينفذ بنجاح |
| Flutter Desktop | لا توجد أدلة parity محدثة للدفعات الجديدة | لا توجد أدلة parity محدثة للدفعات الجديدة | surface موجود في route/workflow، لكن parity الوظيفية غير مثبتة | **UNVERIFIED** |
| Device Gateway | واجهة المؤسسة موجودة، لكن لا يملكها الفرد | تكامل الجهاز/المحلل يحتاج profile وcontract tests | ملكية gateway للمؤسسة مفروضة تصميمياً | **PARTIAL**: التصميم موجود، تشغيل الأجهزة الحقيقي يحتاج rehearsal |
| Ministry/National | لا يوجد ربط حي | لا يوجد ربط حي | sandbox/governance فقط | **NOT_BUILT** للاتصال الحكومي الحي |

## ما تم إثباته محلياً

أثبتت Web/PWA دفعات المواطن والمساحة السريرية ومساحة المؤسسة عبر TypeScript وVite build وESLint واختبارات بوابة القراءة السريرية وbundle budget. وأصبحت النتائج التفصيلية للمختبر متاحة داخل Clinical Workspace من خلال عقد `results.read` وDTO minimal وسجل التدقيق، مع اختيار طلب مصرح به فقط ومنع حقول المشاركة العامة. كما أن شاشة تشغيل المختبر تعرض بيانات اصطناعية معزولة وتوضح ذلك للمستخدم بدلاً من الإيحاء بأنها بيانات إنتاجية.

## فجوات التكافؤ

الفجوة الأكبر ليست في إظهار صفحة مماثلة على كل جهاز، بل في إثبات أن **نفس القرار الخادمي والعزل وسياق المؤسسة** يعملان عبر كل سطح. لذلك يجب أن تستخدم Android وiOS وFlutter وDesktop عقوداً canonical مشتركة، وألا تعيد تنفيذ authorization محلياً. يجب اختبار session expiry وtenant mismatch وoffline-safe behavior وعدم وجود fallback إلى endpoint legacy في كل تطبيق.

| الأولوية | المطلوب لإغلاق الفجوة | دليل الإغلاق |
|---|---|---|
| عالية | توحيد client SDK لعقود `patients.read` و`orders.read` ونتائج لاحقة | contract tests لكل منصة |
| عالية | إثبات session/tenant/role parity | negative authorization matrix مشتركة |
| عالية | إغلاق Android signing incident | تدوير المفتاح والأسرار وhistory containment بموافقة حوكمة |
| متوسطة | تشغيل native CI على runners فعليين | run ناجح وartifact قابل للتدقيق |
| متوسطة | rehearsal للأجهزة وoffline/outbox | test fixtures، retry/idempotency، وrecovery evidence |
| لاحقة | تعريب وإتاحة متكافئة | RTL/accessibility tests لكل سطح |

## القيود

لا تتضمن هذه المصفوفة بيانات مواطنين حقيقية، ولا اتصالاً بوزارة الصحة، ولا ادعاءً بأن المنصة جاهزة لاعتماد سريري أو حكومي. أي pilot عام يحتاج مالك بيانات، مراجعة سريرية وأمنية، بيئة اختبار، خطة incident response، وموافقة الجهة المالكة.
