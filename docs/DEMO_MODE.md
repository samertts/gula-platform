# وضع العرض التجريبي المعزول في GULA

هذا الوضع مخصص لمشاهدة واجهات المنصة واختبار التدفقات باستخدام بيانات اصطناعية فقط. لا يُعدّ هذا الوضع نسخة قراءة من الإنتاج، ولا يجوز توجيهه إلى قاعدة بيانات الإنتاج أو Redis الإنتاجي أو أجهزة المختبر أو خدمات الهوية الحكومية.

## شروط التفعيل

يجب تشغيل خدمة خلفية منفصلة بقاعدة بيانات وRedis منفصلين، ثم ضبط المتغيرات التالية:

```dotenv
ENV=demo
RUNTIME_MODE=api
DEMO_MODE=true
DEMO_DATA_ISOLATION_ACK=true
ENABLE_DEMO_DATA=true
GULA_ADAPTER_MODE=stub
GULA_ADAPTER_MODE_NID=stub
GULA_ADAPTER_MODE_INSURANCE=stub
GULA_ADAPTER_MODE_RESIDENCY=stub
GULA_ADAPTER_MODE_CLOUDFLARE=stub
DATABASE_URL=postgresql://demo_user:REPLACE_ME@demo-postgres:5432/gula_demo
REDIS_URL=redis://:REPLACE_ME@demo-redis:6379
CORS_ORIGINS=https://demo.gula-platform.org,https://www.gula-platform.org
```

يوقف الخادم تشغيله إذا كان `DEMO_MODE=true` دون `DEMO_DATA_ISOLATION_ACK=true`. كما يرفض الجمع بين `ENV=production` و`DEMO_MODE=true`. هذه الحماية لا تغني عن فصل الشبكة وبيانات الاعتماد وقاعدة البيانات على مستوى البنية التحتية.

## الوصول العام

تستخدم الواجهة زر **مشاهدة المنصة بالوضع التجريبي** في صفحة الدخول. الزر يستدعي `POST /demo/access`، وتُنشئ الخلفية حساب مشاهدة اصطناعيًا عند الحاجة، ثم تصدر كوكيز HttpOnly نفسها المستخدمة في الدخول العادي. لا توجد كلمة مرور تجريبية في الواجهة، ولا يُعرض أي رمز JWT في رابط أو localStorage.

حساب العرض مرتبط بمختبر اصطناعي باسم `GULA Synthetic Demo Lab`. يجب أن تُنشأ البيانات الاصطناعية في قاعدة العرض قبل فتحه للعموم، وأن تُمنع عمليات التصدير والاتصال بالأجهزة والخدمات الحكومية من خلال وضع `stub`.

## التسجيل والتحقق المجاني

تسجيل المواطن متاح عبر `/register/citizen`. بعد الإنشاء، يطلب العميل رمزًا من `/auth/verification/request` ويؤكده عبر `/auth/verification/confirm`. تُخزن الخلفية digest للرمز فقط في التخزين المؤقت وتفرض مدة 15 دقيقة وحدًا أقصى للمحاولات. في `ENV=demo` أو `ENV=development` يمكن إظهار `demo_code` داخل الاستجابة لتسهيل الاختبار؛ لا تُظهر الخدمة الرمز في الإنتاج، بل ترسله عبر SMTP أو موصل SMS مهيأ.

تظل حسابات الأطباء والمواطنين غير الموثقة ممنوعة من إصدار جلسة أو الوصول إلى مسارات محمية حتى اكتمال التحقق. تظل MFA عبر TOTP وWebAuthn خيارين مجانيين للحسابات التي تصل إلى مرحلة الجلسة، وتبقى MFA الإلزامية للحسابات الإدارية شرطًا منفصلًا.

## نشر الواجهة

يجب بناء `frontend-v3` مع عنوان API الخاص ببيئة العرض، وليس عنوان الإنتاج:

```bash
cd frontend-v3
VITE_API_BASE_URL=https://demo-api.gula-platform.org npm ci
VITE_API_BASE_URL=https://demo-api.gula-platform.org npm run build
```

إذا استُخدم `vercel.json`، يجب أن تشير إعادة الكتابة `/api/*` إلى خدمة العرض التجريبي، لا إلى `api.gula-platform.org` الإنتاجية. يُفضّل استخدام نطاقين واضحين مثل `demo.gula-platform.org` و`demo-api.gula-platform.org`، مع شهادة TLS وقائمة CORS تحتويهما صراحةً.

## فحص قبل فتح الرابط للعامة

يجب التحقق من أن `/demo/access` يعمل، وأن `/session` يعيد `demo_mode=true`، وأن أي طلب إلى قاعدة الإنتاج غير ممكن من شبكة العرض. كما يجب تجربة logout، refresh، فشل رمز التحقق، ومحاولة طلب كتابة بمصدر Origin غير مصرح، ثم التأكد من ظهور شارة **بيانات اصطناعية ومعزولة** داخل المساعد الإرشادي.
