# عزل بيئات Vercel عن API الإنتاج

## المشكلة

كان `vercel.json` يحتوي rewrite ثابتاً للمسار `/api/:path*` إلى `https://api.gula-platform.org/api/:path*`. وبما أن Vercel كان مفعلاً لعمليات `main` و`develop` و`preview`، فقد يؤدي ذلك إلى أن تستخدم واجهة غير إنتاجية API الإنتاج.

## المعالجة المطبقة

أزيل rewrite الثابت من `vercel.json`. أصبح عميل `frontend-v3` يعتمد على `VITE_API_BASE_URL`، ويستخدم `/api` فقط كقيمة fallback للتطوير المحلي أو الاستضافة التي توفر reverse proxy صراحةً. لا يحتوي عميل API على عنوان إنتاج hard-coded، كما أضيف فحص `scripts/verify-vercel-api-isolation.mjs` الذي يفشل إذا عاد rewrite إلى production أو ظهر عنوان الإنتاج داخل العميل.

> القاعدة الأساسية: **كل deployment يجب أن يحقن API URL الخاص ببيئته أثناء build؛ لا يجوز أن تستنتج الواجهة البيئة من اسم الفرع ولا أن تعتمد على rewrite عالمي ثابت.**

## مصفوفة الإعداد المطلوبة في Vercel

| Vercel Environment | Branch/Source | `VITE_API_BASE_URL` | `VITE_DEPLOYMENT_ENV` | API backend المسموح |
|---|---|---|---|---|
| Production | `main` | `https://api.gula-platform.org/api` | `production` | موارد production فقط |
| Preview أو `develop` | `develop` أو Preview deployment | `https://api.staging.gula-platform.org/api` | `staging` أو `preview` | موارد staging فقط |
| Local development | محلي | `/api` | `development` | Vite proxy إلى localhost |

إذا لم يكن نطاق staging مفعلاً بعد، يجب استخدام Railway preview URL أو نطاق staging فعلي معتمد، وليس عنوان production. لا تُستخدم بيانات مرضى حقيقية، ولا أسرار production، ولا webhooks حقيقية في staging.

## إعداد Vercel Dashboard

في **Project Settings → Environment Variables**، أنشئ المتغير `VITE_API_BASE_URL` ثلاث مرات مع تحديد البيئة المناسبة. اربط قيمة production ببيئة Production فقط، وقيمة staging أو preview ببيئتي Preview/Development فقط. يجب حذف أي متغير أقدم يضع عنوان production على Preview أو Development.

يجب أيضاً ضبط `VITE_DEPLOYMENT_ENV` بالقيم المناسبة، ومراجعة **Git → Production Branch** بحيث يكون `main` فقط هو production branch. إذا كان `develop` يحتاج نطاقاً ثابتاً، فالأفضل ربطه بمشروع Vercel مستقل باسم staging بدلاً من مشاركة مشروع production.

بعد تعديل المتغيرات، يجب إعادة deployment لأن متغيرات `VITE_*` تُضمَّن داخل ملفات JavaScript أثناء build ولا تتغير بمجرد تعديل Dashboard دون إعادة البناء.

## إعداد API الخلفي

يجب أن يقبل backend staging فقط origin واجهة staging في `CORS_ORIGINS`، وأن يحتوي `TRUSTED_HOSTS` على hostname الخاص بـAPI staging فقط. يجب أن تكون قاعدة PostgreSQL وRedis والأسرار وموفرو الدفع والإشعارات منفصلين تماماً عن production. تُراجع هذه الشروط وفق [دليل staging](STAGING_RUNBOOK.md).

## التحقق قبل السماح بالبيانات

يجب تشغيل الحاجز التالي من جذر المستودع:

```bash
node scripts/verify-vercel-api-isolation.mjs
```

ثم فحص artifact المبني بحثاً عن عنوان الإنتاج في Preview:

```bash
VITE_API_BASE_URL=https://api.staging.gula-platform.org/api \
VITE_DEPLOYMENT_ENV=preview \
npm --prefix frontend-v3 run build

grep -R "api.gula-platform.org" frontend-v3/dist/assets || true
```

وجود عنوان production في Preview يُعد فشلاً ويوقف الترقية. أما Production فيجب فحصه منفرداً والتأكد من أن deployment URL والنطاق والـAPI والـdatabase جميعها production بصورة مقصودة.

## التصميم الأفضل على المدى الطويل

الفصل الأقوى هو مشروع Vercel مستقل للواجهة staging ومشروع مستقل للواجهة production، مع نطاقين واضحين وبيئتي backend منفصلتين. ويمكن إبقاء Preview deployments داخل مشروع staging فقط، بحيث لا تملك Preview أي مسار أو secret إلى production. هذا يقلل خطر الخطأ البشري في Environment Variables ويجعل DNS وCSP وCORS قابلين للمراجعة لكل بيئة.

## مراجع

[1]: https://vercel.com/docs/projects/environment-variables "Vercel Environment Variables"
[2]: https://vercel.com/docs/deployments/environments "Vercel Deployment Environments"
[3]: https://github.com/samertts/gula-platform/blob/develop/docs/STAGING_RUNBOOK.md "Gula staging runbook"
