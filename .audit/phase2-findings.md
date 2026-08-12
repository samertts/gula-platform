# نتائج التدقيق الأمني والوظيفي — مسودة عمل

## نتائج مؤكدة من الكود والنشر

| المعرّف | الخطورة | النتيجة | الدليل |
|---|---:|---|---|
| AUTH-01 | حرجة | الخلفية تعيد access وrefresh tokens في JSON بالإضافة إلى وضعها في كوكيز HttpOnly، بينما الواجهة تخزن الرموز في `localStorage`. هذا يوسّع أثر أي XSS ويخالف سياسة الجلسات الآمنة الموحدة. | `backend/app/routes/login.py:163-195`، `frontend-v3/src/api/client.ts:24-28`، `frontend-v3/src/contexts/AuthContext.tsx:31-36` |
| AUTH-02 | عالية | `frontend-v3` لا يستعيد جلسة من الخادم، بل يعتبر وجود `localStorage.access_token` كافيًا لحماية المسار، ويمكن أن يعرض واجهة محمية اعتمادًا على حالة محلية قديمة. | `frontend-v3/src/routes/index.tsx:85-89` |
| AUTH-03 | عالية | مسار `/auth/refresh` يدعم `LabUser` فقط وفق الكود الموصوف في المستودع، بينما `/login` يسمح أيضًا بحسابات `User` مثل المواطن والطبيب؛ لذلك تجديد جلسة هذه الفئات غير متطابق. | `backend/app/routes/login.py:58-70,139-150` و`backend/app/routes/mobile.py` |
| AUTH-04 | عالية | تسجيل الطبيب ينشئ الحساب `is_active=True` و`is_verified=False`، لكن مسار الدخول العام يتحقق من `is_active` فقط ولا يفرض `is_verified` على الحسابات غير الموثقة. | `backend/app/routes/register.py:615-626`، `backend/app/routes/login.py:60-70` |
| AUTH-05 | متوسطة/عالية | تسجيل المواطن يفعّل الحساب فورًا `is_active=True` و`is_verified=False` دون مسار تحقق إلزامي ظاهر، وهو غير كافٍ لحسابات صحية قبل منح أي وصول حساس. | `backend/app/routes/register.py:331-340` |
| AUTH-06 | عالية | `logout` يرفع `perm_version` للمستخدمين في `LabUser` فقط، ولا يرفعها لحسابات `User`، مع أن كلا النوعين يحصل على رموز من `/login`. | `backend/app/routes/login.py:231-244` |
| AUTH-07 | عالية | في مسار تسجيل الدخول الفاشل، يُستخدم `hashlib.sha256` دون استيراد `hashlib` في أعلى الملف؛ هذا قد يحول محاولة دخول خاطئة إلى 500 بدل 401، وقد يسبب تسريبًا تشغيليًا أو تعطيلًا لمسار الحماية. | `backend/app/routes/login.py:2,81-91` |
| REG-01 | حرجة | `register.py` يستخدم `re.search` و`re.match`، لكن لا يظهر استيراد `re` في أعلى الملف؛ التحقق من البيانات قد يفشل بـ500 بدل 4xx. | `backend/app/routes/register.py:2-5,23-35,164-172` |
| REG-02 | عالية | الاختبارات الموجودة تستخدم كلمات مرور مثل `Secure123` و`Doctor123` الأقصر من سياسة 12 حرفًا، ما يشير إلى عدم تزامن الاختبارات مع العقد الحالي. | `backend/tests/test_routes_register.py:113-120,289-296` مقابل `register.py:23-35` |
| WEB-01 | عالية | الموقع المنشور يرد من Vercel كواجهة ثابتة، ومسارات `/api/health` و`/health` و`/api/openapi.json` و`/openapi.json` أعادت 404؛ لا يوجد دليل على أن الموقع المنشور متصل بالخلفية الحالية. | فحص HTTP في 2026-08-11، مع `https://www.gula-platform.org/` |
| WEB-02 | عالية | استجابة الموقع المنشور تحتوي `access-control-allow-origin: *`، بينما الخلفية تسمح ببيئات محددة مع credentials؛ هذا يدل على عدم تطابق طبقة النشر مع سياسة الخلفية. | رؤوس HTTP للنطاق المنشور، `backend/app/factory.py:389-409` |
| WEB-03 | متوسطة | `CORS_ORIGINS` في `.env.production` يضم النطاق غير-www فقط، في حين أن المستخدم يفتح `www.gula-platform.org`; يلزم قرار نطاق أساسي وإعادة توجيه موحد أو إضافة النطاقين صراحةً. | `.env.production:63-66` |
| CI-01 | عالية | أحدث Nightly Build انتهى بـ `startup_failure`، وOpenSSF Scorecard فشل لأن GitHub checkout وجد gitlink باسم `gula-platform` دون `.gitmodules` يحتوي URL. | تشغيلات GitHub بتاريخ 2026-08-10/11، `git ls-files -s` و`git ls-tree HEAD gula-platform` |
| OPS-01 | متوسطة | `backend` يتطلب Python 3.12+ بينما بيئة الفحص الحالية Python 3.11 ولا تحتوي pytest؛ لذلك لم تُنفذ اختبارات backend بعد، ويجب تشغيلها داخل Python 3.12/حاوية المشروع. | `backend/pyproject.toml:9`، نتيجة `python3 -m pytest`: No module named pytest |

## ملاحظات سياسة طبية

لا ينبغي أن يمنح وضع العرض التجريبي أي اتصال بقاعدة البيانات أو Redis أو خدمات حكومية أو أجهزة مختبر أو بيانات مرضى. يجب أن يكون مفعّلًا بعلامة بيئة مستقلة، يستخدم قاعدة بيانات اصطناعية منفصلة، يمنع عمليات الكتابة الحساسة أو يعيدها إلى محاكاة محلية، ويُظهر شارة واضحة بأن البيانات تجريبية. كما يجب أن تبقى عمليات الانتقال السريرية الحقيقية محكومة بالخلفية لا بحماية المسارات في React.

| BUILD-01 | عالية | بناء `frontend-v3` يفشل قبل Vite لأن `vite.config.ts` يستخدم `path` و`__dirname` دون تعريفات Node؛ لا توجد `@types/node` في `package.json`. | `npm ci` نجح، ثم `npm run build` أعاد TS2307 وTS2304 في `vite.config.ts:4,100` |

## أولوية المعالجة

ستبدأ المعالجة بإصلاحات تمنع الوصول غير المصرح أو فشل المصادقة: إزالة الرموز من `localStorage`، توحيد refresh عبر كوكي HttpOnly مع دعم نوعي `LabUser` و`User`، فرض التحقق/الموافقة قبل الوصول الحساس، إصلاح أخطاء الاستيراد، إضافة حماية CSRF للطلبات المعتمدة على الكوكي، ثم عزل وضع العرض التجريبي. بعد ذلك تُصلح الواجهة وتُضاف اختبارات بناء وعقود مصادقة، ثم تُراجع مشاكل GitHub CI ونسخ التطبيقات المحمولة.

## نتائج التنفيذ والاختبار

تم تنفيذ إصلاحات أولية، وأصبحت المجموعة المستهدفة من اختبارات backend ناجحة: `86 passed` في `test_security_demo_contract.py` و`test_security_regression.py` و`test_routes_register.py` و`test_auth_infrastructure.py` تحت Python 3.12. شملت الإصلاحات استيرادات مفقودة في login/register، دعم User في dependency وrefresh، فصل namespace الخاص بـ `perm_version`، حارس CSRF، ومسار تحقق آمن.

تم بناء `frontend-v3` بنجاح بعد إضافة `@types/node` وإعداد `tsconfig.node.json`. كما نجحت أوامر lint وtypecheck وbuild وVitest (`--passWithNoTests`)، بينما اتضح أن المشروع لا يحتوي اختبارات Vitest وحدوية فعلية، وأن تشغيل Vitest الأصلي كان يخلط ملفات Playwright؛ تم فصل E2E عن Vitest في scripts.

كشفت اختبارات العقد الجديدة عطلًا إضافيًا في `NotificationService`: كان يستدعي `CircuitBreaker.allow_request/record_success/record_failure` رغم أن التنفيذ المشترك يوفّر `state/call`. تمت معالجة هذا التعارض واختباره ضمن دورة التحقق.

تبيّن أن أدوات Flutter غير مثبتة، وأن Android Gradle wrapper يفتقد `GradleWrapperMain`، ولا تتوفر أدوات Xcode أو MSBuild في بيئة الفحص؛ لذلك لا يمكن إعلان أن حزم iOS/Android/Windows قد بُنيت أو أُنجزت بالكامل هنا. تم الحفاظ على عقد `access_token` للهواتف مع تدوير refresh، بينما أصبحت واجهة الويب لا تقرأ الرموز من localStorage ولا تمررها في WebSocket URL.

## نتائج التحقق النهائي

نجحت `python3.12 -m compileall`، ونجحت مجموعة backend المركزة بعد الإصلاحات: `86 passed, 4 warnings`. نجحت الواجهة في `npm run lint` و`npm run typecheck` و`npm run build` و`npm test`، مع عدم وجود اختبارات Vitest وحدوية فعلية؛ الأمر الآن ينجح صراحةً مع `--passWithNoTests` بينما تبقى E2E في `npm run test:e2e`.

أظهر `pip-audit` عدم وجود ثغرات معروفة في اعتماديات `backend/requirements.txt`. أظهر `npm audit --omit=dev` ثغرتين عاليتين في react-router/react-router-dom ضمن النطاق `7.12.0` إلى `7.18.1`، وتمت الترقية إلى `react-router-dom ^7.18.2` وأصبح تدقيق اعتماديات الإنتاج `high=0, critical=0, moderate=0, low=0`.

تبقى تحذيرات غير حاجزة: تحذير deprecation في `datetime.utcnow()`، وتحذير SQLAlchemy متعلق بدورة foreign keys أثناء teardown الاختبارات، وتعارض peer قديم بين Vite 8 وVitest mocker يظهر أثناء npm install لكنه لا يمنع lint/typecheck/build.
