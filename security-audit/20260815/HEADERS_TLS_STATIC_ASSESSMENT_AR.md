# تقييم Headers وTLS وتحديد نطاق اختبار الاختراق

**النطاق:** مستودع `samertts/gula-platform` وبيئة staging الموثقة في ملفات المشروع فقط.
**نوع التقييم:** تدقيق ثابت + محاولة وصول سلبية محدودة عبر HTTP/TLS.
**الهدف:** تقييم الضبط الأمني دون تسجيل دخول، دون إرسال payloads، ودون تنفيذ ZAP active scan أو Burp Intruder أو أي استغلال.

## الخلاصة

تعذر إصدار حكم على Headers وTLS الفعلية للخدمة المنشورة لأن جميع عناوين staging الموثقة لم تُحل عبر DNS من بيئة الفحص في تاريخ التقييم. شملت المحاولة `staging.gula.health`، وهو الهدف المعلن في إعداد DAST، إضافة إلى العناوين الأخرى المذكورة في إعدادات وعقود المشروع [1] [7]. لذلك فإن نتائج live securityheaders/SSL Labs غير متاحة، وأي تصنيف لHeaders المنشورة سيكون غير مهني إذا اعتُبر نتيجة مؤكدة.

في المقابل، أظهر التدقيق الثابت وجود ضوابط جيدة في طبقة FastAPI وVercel وNginx، مع وجود **مخاطر اتساق وعزل تحتاج معالجة قبل Pentest حي** [2] [3] [5] [6]. أخطر ملاحظة هي أن `vercel.json` يوجه `/api/:path*` إلى `https://api.gula-platform.org`، وهو عنوان إنتاج، بينما يفعّل الملف نفسه deployments لفرعي `develop` و`preview`. يجب إثبات أن staging أو preview لا يستخدم هذا rewrite قبل السماح بإدخال أي بيانات اختبار؛ وإلا فهناك احتمال توجيه واجهة غير إنتاجية إلى API الإنتاج.

## حالة الوصول الشبكي

| الهدف | النتيجة | الدلالة |
|---|---|---|
| `https://staging.gula.health` | DNS resolution failed | الهدف الموثق في `config/security/dast-config.yml` غير قابل للوصول من بيئة الفحص |
| `https://staging.gulaplatform.com` | DNS resolution failed | لا توجد نتيجة HTTP/TLS قابلة للتقييم |
| `https://staging-api.gulaplatform.com` | DNS resolution failed | لا توجد نتيجة HTTP/TLS قابلة للتقييم |
| `https://staging.gula-platform.org` | DNS resolution failed | لا توجد نتيجة HTTP/TLS قابلة للتقييم |
| `https://api.staging.gula-platform.org` | DNS resolution failed | لا توجد نتيجة HTTP/TLS قابلة للتقييم |

لم تُرسل أي طلبات إلى نطاق إنتاج، ولم تُستخدم بيانات دخول أو بيانات مرضى. فشل DNS منع الوصول قبل مرحلة HTTP وTLS، ولذلك لا يمكن تأكيد الشهادة أو HSTS أو CSP من الشبكة.

## الضوابط الثابتة المؤكدة من المصدر

| المجال | الدليل | التقييم الثابت |
|---|---|---|
| FastAPI headers | `backend/app/middleware.py:169-192` | يضيف `nosniff` و`X-Frame-Options` وReferrer-Policy وPermissions-Policy وCOOP وCORP وCSP وCache-Control، ويضيف HSTS عند `IS_PRODUCTION` |
| Staging security mode | `backend/app/config.py:15-37` | `ENV=staging` يعامل كإنتاج من ناحية الأمن، ويتطلب CORS وTrusted Hosts صراحةً |
| CORS | `backend/app/factory.py:424-466` | يمنع wildcard مع credentials، ويفرض HTTPS على origins في staging/production |
| Trusted Host | `backend/app/factory.py:445-455` | يفعّل `TrustedHostMiddleware` في staging/production |
| Vercel frontend | `vercel.json:20-45` | يضيف HSTS مع preload وCSP وX-Frame-Options وPermissions-Policy وnosniff |
| Nginx TLS | `nginx.conf:47-60` | يصرح بـTLS 1.2 وTLS 1.3 ويضيف HSTS وCSP وHeaders أساسية |

## النتائج المصنفة

### F-01 — خطر عزل staging عن الإنتاج في Vercel — High / يحتاج تحققاً فورياً

يُعرّف `vercel.json` deployments لفرعي `main` و`develop` و`preview`، لكنه يوجه `/:path*` إلى الواجهة، و`/api/:path*` إلى `https://api.gula-platform.org/api/:path*`. هذا rewrite ثابت على عنوان إنتاج. لا يمكن من الملف وحده إثبات وجود override خاص ببيئة staging [5].

**الأثر المحتمل:** قد تعرض واجهة develop أو preview بيانات أو عمليات API الإنتاج، أو قد تُرسل بيانات اختبار إلى قاعدة الإنتاج. هذا يتعارض مع دليل staging الذي يشترط عدم القراءة من أو الكتابة إلى خدمات الإنتاج.

**المعالجة المطلوبة قبل أي فحص مصادق عليه:** فصل إعدادات production وstaging على مستوى المشروع أو deployment، واستخدام `VITE_API_URL`/rewrite خاص ببيئة staging، ثم إضافة اختبار CI يفشل إذا ظهر عنوان `api.gula-platform.org` في artifact staging. يجب إثبات ذلك عبر deployment URL فعلي ولقطة إعدادات منزوعة الأسرار.

### F-02 — عدم اتساق CSP وHeaders بين الطبقات — Medium

توجد سياسات CSP متعددة في FastAPI وVercel وNginx. بعضها يسمح بـ`unsafe-inline`، وبعضها يختلف في `connect-src` و`img-src` و`Permissions-Policy` و`X-Frame-Options` (`DENY` مقابل `SAMEORIGIN`). كما أن CSP في FastAPI يذكر نطاقات الإنتاج فقط. هذا لا يثبت ثغرة مباشرة، لكنه يجعل النتيجة الفعلية تعتمد على الطبقة التي تنهي TLS وترتب headers.

**المعالجة المطلوبة:** اعتماد مصدر واحد للسياسة النهائية، أو توثيق مصفوفة واضحة لكل origin وطبقة. يجب أن تحتوي سياسة staging على origins staging اللازمة فقط، وأن تُختبر بالمتصفح وبـHTTP response headers بعد النشر. ينبغي إزالة `unsafe-inline` إن لم يكن ضرورياً، أو استبداله بـnonce/hash عند الإمكان.

### F-03 — HSTS وPreload بحاجة إلى تحقق من DNS ونطاقات subdomains — Low/Medium

Vercel يضبط `max-age=63072000; includeSubDomains; preload`، بينما FastAPI وNginx يستخدمان سياسات مختلفة ولا يضيفان `preload`. لا يمكن اعتماد preload أو includeSubDomains قبل إثبات أن كل subdomain مشمول يعمل عبر HTTPS ولا يحتاج HTTP.

**المعالجة المطلوبة:** بعد تفعيل DNS، فحص الشهادة وسلسلة الثقة، وإعادة التوجيه HTTP→HTTPS، وتغطية SAN، ثم مراجعة قائمة subdomains قبل أي preload submission.

### F-04 — X-XSS-Protection قديم وغير ضروري — Informational

تضيف عدة طبقات `X-XSS-Protection: 1; mode=block`. هذا header obsolete في المتصفحات الحديثة ولا يعوض CSP، وقد يسبب سلوكاً غير متوقع في متصفحات قديمة.

**المعالجة المطلوبة:** إبقاؤه فقط إذا كان جزءاً من baseline توافق موثق، وإلا إزالته تدريجياً مع الاعتماد على CSP وoutput encoding وTrusted Types حيث تنطبق.

### F-05 — استثناء asset responses من SecurityHeadersMiddleware — Informational/Low

تتجاوز `SecurityHeadersMiddleware` المسارات التي تبدأ بـ`/assets/` أو تنتهي بـ`.css` و`.js` و`.png` و`.ico`. طبقة Vercel/Nginx قد تغطي هذه الاستجابات، لكن ذلك غير مثبت live حالياً.

**المعالجة المطلوبة:** التحقق من asset response headers على staging. إذا لم تكن طبقة الحافة تغطيها، يجب إزالة الاستثناء أو إضافة سياسة موحدة في طبقة الاستضافة.

### F-06 — إعداد DAST الحالي نشط وثقيل ولا ينبغي تشغيله تلقائياً دون موافقة — Process Risk

يعرّف `config/security/dast-config.yml` وضع `full_scan`، ويُفعّل active scan بقوة attack `high` وسياسات تشمل SQL injection وXSS وSSRF وcommand injection وغيرها. هذا مناسب فقط لاختبار staging مع synthetic data وتفويض موثق، وليس لفحص غير مؤكد أو production [1].

**المعالجة المطلوبة:** إنشاء profile منفصل `passive_baseline` للفحوص اليومية، وحصر `full_scan` في نافذة اختبار معتمدة، وrate limit، ومراقبة، وبيانات synthetic، وkill switch. يجب عدم تشغيل الإعداد الحالي قبل إثبات DNS والعزل والتفويض.

## قرار الجاهزية

| البند | القرار |
|---|---|
| فحص live Headers/TLS | **مؤجل** بسبب DNS غير متاح |
| فحص ZAP passive baseline | **مؤجل** إلى حين تحديد هدف staging قابل للوصول |
| ZAP active/full scan | **ممنوع حالياً** دون تفويض ونافذة اختبار وعزل بيانات |
| فحص الإنتاج | **مرفوض** ضمن هذا التقييم |
| مراجعة F-01 | **أولوية عالية قبل أي بيانات اختبار** |
| إصدار قرار Go/No-Go أمني | **NO-GO مؤقتاً** حتى إثبات عزل staging وإتاحة DNS والتحقق من headers المنشورة |

## نطاق Pentest المقترح بعد تجهيز staging

ينبغي أن ينفذ الاختبار فريق أمني مرخّص أو جهة تملك تفويضاً مكتوباً من مالك النظام [7]. يبدأ الاختبار بمرحلة passive discovery وTLS/Headers، ثم authenticated testing محدود لحسابات synthetic موزعة على الأدوار: citizen، receptionist، cashier، doctor، pharmacist، laboratory، radiology، administrator. تشمل المحاور RBAC/IDOR والعزل بين العيادات والمحافظات، مسارات tickets/payments، منع الصرف الشهري المكرر، MFA/session/refresh/logout، rate limiting، upload، webhooks/HMAC، offline sync conflict handling، وتدقيق PII في logs.

لا تُستخدم بيانات مرضى حقيقية، ولا تُختبر خدمات SMS أو الدفع الحقيقي، ولا تُفعل SSRF أو command injection خارج حسابات وموارد staging المعزولة. يجب أن تتضمن قواعد التوقف: ظهور أي اتصال بخدمة إنتاج، تأثير على بيانات غير synthetic، تجاوز معدل الطلبات، أو فقدان قابلية rollback.

## الأدلة والمراجع داخل المستودع

[1]: ../../config/security/dast-config.yml "إعداد DAST وهدف staging وسياسات الفحص"
[2]: ../../backend/app/middleware.py "سياسة SecurityHeadersMiddleware"
[3]: ../../backend/app/factory.py "تهيئة CORS وTrustedHost وmiddleware"
[4]: ../../backend/app/config.py "حدود ENV=staging ومتطلبات HTTPS والشبكة"
[5]: ../../vercel.json "إعدادات Vercel وrewrites وheaders"
[6]: ../../nginx.conf "إعداد TLS وNginx headers"
[7]: ../../docs/STAGING_RUNBOOK.md "دليل عزل staging وإجراءات الترقية"
