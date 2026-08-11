# تقرير فحص وتحصين منصة GULA

**المستودع:** [samertts/gula-platform][1]

**الموقع الذي تمت مراجعته:** [gula-platform.org][2]

**فرع العمل:** `security-hardening-demo-alignment`

**تاريخ الفحص:** 11 أغسطس 2026

**إعداد التقرير:** Manus AI

## الملخص التنفيذي

أُجري فحص للكود الخلفي والواجهة الأمامية ومسارات المصادقة والتسجيل والنشر العام، ثم نُفذت مجموعة إصلاحات على فرع مستقل. شملت الإصلاحات منع اعتماد حماية المسارات على `localStorage`، استعادة الجلسة من الخادم، دعم حسابات المواطنين والأطباء في refresh وdependency، فرض التحقق قبل إصدار الجلسة، إضافة CSRF للطلبات المعتمدة على الكوكيز، إضافة وضع عرض تجريبي معزول، وبناء مساعد إرشادي داخل الواجهة.

> **تنبيه نشر:** الكود والاختبارات المحلية تحسنت ونجحت المجموعة المركزة، لكن لا يجوز فتح رابط العرض التجريبي للعامة قبل نشر Backend منفصل بقاعدة بيانات وRedis منفصلين وبيانات اصطناعية فقط. تغيير الكود وحده لا يثبت أن النشر الحالي معزول عن الإنتاج.

| المجال | النتيجة | الحالة |
|---|---|---|
| فحص Backend syntax | `python3.12 -m compileall` | ناجح |
| اختبارات Backend المركزة | 86 اختبارًا ناجحًا | ناجحة مع 4 تحذيرات غير حاجزة |
| Frontend lint/typecheck/build | جميعها ناجحة | ناجحة |
| Frontend Vitest | لا توجد ملفات unit tests؛ الأمر ينجح صراحةً مع `--passWithNoTests` | يحتاج إضافة اختبارات فعلية |
| pip-audit | لا توجد ثغرات معروفة في اعتماديات backend المحددة | ناجح |
| npm audit للإنتاج | `high=0`, `critical=0`, `moderate=0`, `low=0` بعد ترقية React Router | ناجح |
| Android/iOS/Windows native build | لم يُنفذ بسبب غياب Flutter/Xcode/MSBuild وخلل Gradle wrapper | غير متحقق في هذه البيئة |
| النشر العام الحالي | يحتاج ربطًا ونشرًا منفصلًا للـ API وإعادة تحقق من CORS | إجراء نشر مطلوب |

## المشكلات التي عولجت

| المعرّف | الخطورة قبل الإصلاح | المعالجة | الوضع |
|---|---:|---|---|
| AUTH-01/AUTH-02 | حرجة/عالية | أزيل اعتماد الويب على `localStorage` في AuthContext وحماية المسارات، وأصبح عميل Axios يعتمد `withCredentials` وتدوير refresh واستعادة `/session`. | عولج للويب؛ تبقى استجابة JSON القديمة للهواتف للتوافق الانتقالي |
| AUTH-03 | عالية | أصبح refresh يبحث في `LabUser` ثم `User`، ويفرض أن يكون حساب `User` نشطًا وموثقًا. | عولج |
| AUTH-04/AUTH-05 | عالية | أضيفت سياسة تمنع إصدار جلسة للحسابات المدنية والطبية غير الموثقة، مع مساري طلب وتأكيد رمز تحقق مؤقت. | عولج |
| AUTH-06 | عالية | أصبح logout يدعم `User` و`LabUser`، وفُصل namespace الخاص بـ `perm_version` لمنع تصادم معرفات النوعين. | عولج |
| AUTH-07/REG-01 | عالية | أضيفت الاستيرادات المفقودة التي كانت تحول محاولات الدخول أو التسجيل غير الصحيحة إلى أخطاء 500. | عولج |
| CSRF | عالية | أضيف `CSRFMiddleware` يرفض مصدر Origin/Referer غير المصرح للطلبات المتغيرة مع كوكيز الجلسة ويسجل المحاولة. | عولج واختُبر |
| BUILD-01 | عالية | أضيفت `@types/node` وإعداد `types: ["node"]` في `tsconfig.node.json`. | عولج |
| NOTIFY-01 | عالية | أصلحت خدمة الإشعارات استخدام API غير موجود (`allow_request`/`record_success`) واستُخدم `CircuitBreaker.state/call` الفعلي. | عولج واختُبر |
| DEP-01 | عالية | رُقي `react-router-dom` من نطاق متأثر إلى `^7.18.2` لمعالجة advisory [3]. | عولج؛ تدقيق الإنتاج صفر |
| CI-01 | عالية | أزيل gitlink الميت `gula-platform` الذي لم يكن له `.gitmodules` ويعطل بعض فحوص GitHub. | عولج في الفرع؛ يحتاج push ومراجعة CI |

## الميزات المنفذة

### التسجيل والتحقق

أضيفت صفحة `/register` لتسجيل المواطن، مع كلمة مرور لا تقل عن 12 محرفًا، وطلب رمز من `/auth/verification/request` وتأكيده عبر `/auth/verification/confirm`. تُخزن digest للرمز فقط في cache، وتُفرض مدة 15 دقيقة وخمسة محاولات كحد أقصى. في `ENV=demo` أو `ENV=development` يمكن إظهار `demo_code` لتسهيل الاختبار؛ في الإنتاج يجب تهيئة SMTP أو موصل SMS، ولا يُعاد الرمز داخل الاستجابة.

### الوضع التجريبي المعزول

أضيف `POST /demo/access`، وهو غير متاح إلا إذا كانت `DEMO_MODE=true` و`DEMO_DATA_ISOLATION_ACK=true`، كما يرفض الإعداد الجمع بين `ENV=production` و`DEMO_MODE=true`. ينشئ المسار مستخدمًا ومختبرًا اصطناعيين، ويصدر كوكيز HttpOnly وSecure عند النشر عبر HTTPS. لا توجد كلمة مرور تجريبية في الواجهة.

التفاصيل التشغيلية الكاملة موجودة في [docs/DEMO_MODE.md](docs/DEMO_MODE.md). يجب أن تستخدم بيئة العرض قاعدة PostgreSQL وRedis منفصلين، وأن تُضبط موصلات الهوية والتأمين والأجهزة على `stub` أو محاكاة محلية. لا يكفي تغيير اسم النطاق وحده لعزل البيانات.

### الواجهة والمساعد

أضيف `GuideAssistant` إلى `DashboardLayout`. يعرض إرشادات حسب المسار الحالي، ويحذر من إدخال بيانات حقيقية في العرض، ويظهر شارة البيانات الاصطناعية. يعمل محليًا ولا يرسل محتوى المستخدم إلى نموذج خارجي. كما أضيف زر الدخول التجريبي إلى صفحة الدخول، وأضيفت حماية المسارات لتنتظر استعادة الجلسة من الخادم.

### تطبيقات Desktop/EXE

وُحّد عقد Desktop مع الخلفية: يقرأ `access_token` أو `token` للتوافق، يدعم `user` المتداخل، يتحقق من `/session`، ويملك `startDemo()` وزرًا للمشاهدة المعزولة. تظل الرموز في `flutter_secure_storage`. تم توثيق الوضع في [docs/MOBILE_DESKTOP_STATUS.md](docs/MOBILE_DESKTOP_STATUS.md).

## نتائج الاختبارات والتدقيق

| الأمر | النتيجة |
|---|---|
| `python3.12 -m compileall -q backend/app shared` | ناجح |
| اختبارات `test_security_demo_contract.py`, `test_security_regression.py`, `test_routes_register.py`, `test_auth_infrastructure.py` | 86 ناجحًا |
| `npm run lint` | ناجح |
| `npm run typecheck` | ناجح |
| `npm run build` | ناجح؛ PWA generated |
| `npm test` | ناجح مع `--passWithNoTests`؛ لا توجد unit tests فعلية |
| `pip-audit -r backend/requirements.txt` | لا توجد ثغرات معروفة |
| `npm audit --omit=dev` | صفر ثغرات في اعتماديات الإنتاج بعد الترقية |

تبقى أربعة تحذيرات غير حاجزة في الاختبارات: deprecation لـ `datetime.utcnow()`، وتحذير SQLAlchemy عن دورة foreign keys أثناء teardown، وتحذير أمني من مفتاح اختبار قصير في حالة اختبار signature، وتحذير Starlette/TestClient. ينبغي تنظيفها في دورة لاحقة، خصوصًا استبدال `datetime.utcnow()` بزمن UTC واعٍ بالمنطقة.

## حدود الإنجاز وقرارات النشر

الموقع العام الذي فُحص لا يثبت حاليًا أن API المنشور متصل بالخلفية المقروءة من المستودع؛ كما ظهرت مؤشرات عدم تطابق في مسارات API وCORS. تم تحديث `.env.production` ليشمل النطاقين الأساسي و`www`، لكن إعدادات مزود الاستضافة الخارجي تحتاج نشرًا فعليًا وإعادة فحص. لم تُجرَ أي محاولة دخول أو كتابة بيانات حقيقية.

أدوات Flutter غير مثبتة، وGradle wrapper في Android يفتقد `GradleWrapperMain`، ولا تتوفر Xcode أو MSBuild؛ لذلك لا يصح إعلان أن APK أو IPA أو Windows EXE قد بُنيت بنجاح من هذه البيئة. يلزم تشغيل أوامر البناء في CI native أو جهاز مناسب، ثم إرفاق نتائج `flutter analyze`, `flutter test`, `assembleRelease`, و`build windows --release` قبل الإصدار.

## خطوات النشر المطلوبة

1. راجع التغييرات في الفرع `security-hardening-demo-alignment` ثم ادفعها إلى GitHub وأنشئ Pull Request بدل الدمج المباشر إلى `main`.
2. أنشئ خدمة `demo-api` وقاعدة بيانات وRedis منفصلين، واضبط `ENV=demo`, `DEMO_MODE=true`, `DEMO_DATA_ISOLATION_ACK=true`، ولا تستخدم أي secret أو DSN من الإنتاج.
3. اضبط `VITE_API_BASE_URL` في بناء `frontend-v3` على API التجريبي، واجعل إعادة كتابة `/api/*` في Vercel تشير إلى `demo-api` لا إلى API الإنتاج.
4. اختبر `/demo/access`, `/session`, refresh, logout، التسجيل والتحقق، CSRF، ورفض الحساب غير الموثق من خارج شبكة الإنتاج.
5. لا تفتح الوصول العام قبل نجاح فحص عزل الشبكة وقاعدة البيانات، ومراجعة CORS وTLS وSecure cookies، وتشغيل CI كاملًا.

## المراجع

[1]: https://github.com/samertts/gula-platform "مستودع GULA Platform على GitHub"
[2]: https://www.gula-platform.org/ "الموقع العام لمنصة GULA"
[3]: https://github.com/advisories/GHSA-qwww-vcr4-c8h2 "React Router RSC Mode CSRF Bypass advisory"
