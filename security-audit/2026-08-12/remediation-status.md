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

## التحقق الحالي

تم التحقق من `frontend-v2` و`frontend-v3` باستخدام lint وTypeScript وunit tests وbuild بنجاح. كما تم التحقق من `git diff --check`، وفحص النطاقات القديمة في الملفات المتأثرة، وعدم وجود مراجع لمكتبة Google AI أو متغيرات مفاتيح Gemini في مصدر `frontend-v2`. تعذر تشغيل `flutter analyze` وAndroid Gradle في بيئة التنفيذ لأن Flutter غير مثبت وGradle احتاج اتصالاً خارجياً؛ لذلك تبقى اختبارات الهاتف وdesktop بحاجة إلى CI أو جهاز بناء فعلي.
