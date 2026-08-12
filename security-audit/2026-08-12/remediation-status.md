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

## التحقق الحالي

تم التحقق من `frontend-v2` و`frontend-v3` باستخدام lint وTypeScript وunit tests وbuild بنجاح. كما تم التحقق من `git diff --check`، وفحص النطاقات القديمة في الملفات المتأثرة، وعدم وجود مراجع لمكتبة Google AI أو متغيرات مفاتيح Gemini في مصدر `frontend-v2`. أضيفت اختبارات regression للـhealth exchange وحواجز إعدادات الإنتاج؛ شغّلت الاختبارات المعزولة بنجاح: 5 passed، مع نجاح compileall وحارس الأسرار. تعذر تشغيل `flutter analyze` وAndroid Gradle في بيئة التنفيذ لأن Flutter غير مثبت وGradle احتاج اتصالاً خارجياً؛ لذلك تبقى اختبارات الهاتف وdesktop بحاجة إلى CI أو جهاز بناء فعلي. كما تبقى نتائج `pip-audit` وDependabot التشغيلية بحاجة إلى متابعة GitHub بعد الدفع.
