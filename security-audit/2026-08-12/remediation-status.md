# GULA Remediation Status

هذا السجل يوضح ما عولج في التحديث الحالي وما يحتاج إلى إجراء تشغيلي أو اختبار إضافي. لا يتضمن أي قيمة سرية أو بيانات مستخدمين.

| المجال | الإجراء المنفذ | الحالة | التحقق |
|---|---|---|---|
| نشر الواجهة | توحيد Workflow مع `frontend-v3` وإضافة typecheck/build وLighthouse | مكتمل محلياً | TypeScript وbuild نجحا |
| SPA routing | الإبقاء على fallback إلى `index.html` لمسارات الواجهة العميقة | مكتمل في المصدر | يحتاج تحققاً بعد النشر من `/login` و`/register` |
| API configuration | دعم `VITE_API_BASE_URL` و`VITE_API_BASE` مع `/api` كقيمة افتراضية | مكتمل | TypeScript نجح |
| AI secrets | إزالة الاستدعاءات المباشرة لمكتبة Google AI وتبعياتها وتعليمات المفتاح من `frontend-v2` | مكتمل في المصدر | فحص المصدر لا يظهر استدعاء أو مفتاح Google AI |
| Android pinning | استبدال pins الوهمية ببصمة API الإنتاجية المتحققة وتوحيد release base URL | مكتمل في المصدر | يحتاج build واختبار release على جهاز/محاكي |
| iOS pinning | استبدال pins الوهمية وحصر pinning على `api.gula-platform.org` وتوحيد base URL | مكتمل في المصدر | يحتاج build واختبار release على جهاز/محاكي |
| CSP | إضافة `wss://api.gula-platform.org` إلى `connect-src` | مكتمل في المصدر | يحتاج تحققاً بعد النشر من WebSocket |
| أسرار Git التاريخية | تحديد التعرض المحتمل دون رفع القيم أو عرضها | يتطلب إجراءً خارج Git | إبطال وتدوير كل المفاتيح والرموز المتأثرة |
| التبعيات | توثيق تنبيهات GitHub وDependabot | يتطلب إجراءً إضافياً | تحديث lockfiles بعد مراجعة توافق الإنتاج |
| اختبار runtime | لا يوجد تسجيل دخول أو استغلال أو فحص IDOR/RBAC في هذا التغيير | متبقٍ | يُنفذ في Staging بمستخدمين اختبار فقط |

## قيود السلامة

لم تُرفع ملفات `.env`، أو الحزم الخام، أو السجلات التي قد تحتوي عناوين داخلية أو أسراراً. تقرير التدقيق نفسه يجب أن يبقى في مستودع خاص أو ضمن صلاحيات وصول محدودة.

| Desktop API | توحيد عنوان الإنتاج إلى `api.gula-platform.org/api/v1` في نقطة التشغيل والثوابت والاختبار | مكتمل في المصدر | يحتاج Flutter analyze/test في بيئة Flutter |
| Desktop pinning | إزالة interceptor الشكلي وجعله fail-closed عند تفعيل pinning قبل توفير native adapter فعلي | مكتمل في المصدر | يحتاج native transport adapter قبل تمكينه في release |
| Health exchange secret | إزالة `LAB_PLATFORM_SECRET` الثابت، والاعتماد على `LAB_PLATFORM_API_KEY` من البيئة مع `hmac.compare_digest` والإغلاق الافتراضي | مكتمل في المصدر | اختبار regression: 2 passed |
| Secret prevention | إضافة `scripts/security/check_public_secrets.py` وفحصه ضمن CI، مع استثناءات محددة للـfixtures المنقحة فقط | مكتمل في المصدر | الحارس: لا أسرار محتملة في الملفات المتتبعة |
| Gitleaks | إضافة `.gitleaks.toml` مع القواعد الافتراضية وفحص كامل للتاريخ عبر workflow مجدول | مكتمل في المصدر | workflow `Security Hardening` مفعّل على push وPR والجدول الأسبوعي |
| Python dependency audit | إضافة `pip-audit` لم manifests Python الموجودة، مع Dependency Review على PRs | مكتمل في المصدر | ينتظر نتائج GitHub Actions وفتح إصلاحات التبعيات المتبقية |
| Production configuration | فرض `BASE_URL` وHTTPS، أسرار قوية لا تقل عن 32 حرفاً، Redis مشترك، ومدة refresh بين 1 و30 يوماً | مكتمل في المصدر | اختبارات config production: 3 passed |
| CORS/CSRF/Host | رفض wildcard مع credentials، حصر CORS الإنتاجي على HTTPS، إضافة TrustedHost، وتوحيد origins الرسمية في CSRF | مكتمل في المصدر | اختبار رفض wildcard وقبول الإعداد الآمن |
| Backend CSP | إضافة النطاقين الرسميين وAPI وWebSocket إلى `connect-src` مع `upgrade-insecure-requests` | مكتمل في المصدر | تحقق syntax وdiff check؛ يحتاج تحقق headers بعد النشر |
| Android transport | فصل إعداد release الصارم عن debug overlay، منع cleartext في release، إزالة pins الوهمية، وتوحيد `api.gula-platform.org` | مكتمل في المصدر | client transport guard و`compileall` نجحا؛ يحتاج Android release build |
| iOS refresh transport | توحيد refresh مع URLSession المزوّدة بـCertificatePinner بدلاً من جلسة النظام، وتصحيح حساب SPKI من SubjectPublicKeyInfo عبر سلسلة الثقة | مكتمل في المصدر | client transport guard نجح؛ يحتاج Xcode release build واختبار شهادة |
| Hospital desktop transport | فرض HTTPS والمضيفات المعتمدة، منع HTTP adapter وredirects، وحماية روابط التنزيل من تسريب bearer token | مكتمل في المصدر | اختبارات URL وcompileall وguard نجحت |
| Flutter desktop transport | إضافة endpoint allowlist، منع redirects، وإعادة المحاولة عبر نفس Dio instance حتى لا تتجاوز الحماية | مكتمل في المصدر | client transport guard نجح؛ يحتاج `flutter analyze` و`flutter test` في CI |
| Flutter secure key generation | استبدال توليد المفتاح المعتمد على الوقت بـ`Random.secure()` | مكتمل في المصدر | guard المصدر نجح؛ يحتاج اختبار Flutter على منصات الإصدار |
| TLS pin evidence | حفظ بصمة SPKI العامة ونوع شهادة الإنتاج في `tls-pinning-evidence.md` دون أي بيانات اعتماد | مكتمل في المصدر | تحقق TLS خارجي موثق؛ يلزم pin احتياطي موثق قبل التجديد |
| Vercel project-root headers | إضافة `frontend-v3/vercel.json` لأن إعداد root `vercel.json` لا يضمن تطبيق headers عندما يكون دليل المشروع `frontend-v3` | مكتمل في المصدر | يحتاج نشر Vercel ثم تحقق GET من CSP وsecurity headers؛ التحقق السابق أظهر غيابها في الموقع الحي |
| Secret rotation runbook | إضافة `secret-rotation-runbook.md` بأسماء الأسرار وخطوات الإبطال والتدوير والتحقق دون قيم سرية | مكتمل في المصدر؛ التنفيذ التشغيلي متبقٍ | يجب تدوير كل الأسرار التاريخية في مزوديها، ثم توثيق رقم الإصدار ونتيجة staging/production |
| Public demo isolation | إضافة Render Blueprint لخدمتي `gula-demo-backend` و`gula-demo-frontend` مع PostgreSQL وRedis منفصلين، `DEMO_MODE` وintegrations بنمط `stub` | مكتمل في المصدر؛ مزامنة Render متبقية | تحقق `/demo/access` و`/session`، راجع أن قاعدة demo ليست الإنتاج، ثم أضف DNS المخصص اختيارياً |
| Demo least privilege | خفض حساب العرض إلى دور `doctor` للقراءة، وإضافة `DemoReadOnlyMiddleware` لمنع عمليات الكتابة مع إبقاء access/refresh/logout | مكتمل في المصدر | اختبارات regression: 3 passed؛ يجب اختبار العرض بعد النشر من متصفح عام |
| Demo frontend identity | إزالة الهوية المحلية الوهمية من `AuthContext` واستعادة المستخدم الحقيقي من `/session` مع شارة البيانات الاصطناعية | مكتمل في المصدر | TypeScript وbuild بعد دفع التغيير |

## التحقق الحالي

تم التحقق من `frontend-v2` و`frontend-v3` باستخدام lint وTypeScript وunit tests وbuild بنجاح. كما تم التحقق من `git diff --check`، وفحص النطاقات القديمة في الملفات المتأثرة، وعدم وجود مراجع لمكتبة Google AI أو متغيرات مفاتيح Gemini في مصدر `frontend-v2`. أضيفت اختبارات regression للـhealth exchange وحواجز إعدادات الإنتاج؛ شغّلت الاختبارات المعزولة بنجاح: 5 passed، مع نجاح compileall وحارس الأسرار. تعذر تشغيل `flutter analyze` وAndroid Gradle في بيئة التنفيذ لأن Flutter غير مثبت وGradle احتاج اتصالاً خارجياً؛ لذلك تبقى اختبارات الهاتف وdesktop بحاجة إلى CI أو جهاز بناء فعلي. كما تبقى نتائج `pip-audit` وDependabot التشغيلية بحاجة إلى متابعة GitHub بعد الدفع. أظهر التحقق الخارجي الأخير أن الموقع الحي أعاد 200 لكنه لم يعرض CSP وبعض ترويسات الحماية، لذلك أضيف `frontend-v3/vercel.json` لمعالجة احتمال اختلاف دليل المشروع، ويبقى تحقق ما بعد النشر إلزامياً.
