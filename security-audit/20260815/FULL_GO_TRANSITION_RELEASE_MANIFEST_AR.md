# Release Manifest — حزمة الانتقال نحو Full GO

**الحالة:** حزمة محلية غير منشورة
**الفرع:** `security/p0-bootstrap-alembic`
**الـcommit المرصود عند التنفيذ:** `b2b90972`
**القرار:** `GO_WITH_RESTRICTIONS` — لا نشر ولا merge ولا tag تلقائي.

## النطاق المسموح

تتضمن الحزمة إصلاحات UTC، granular RBAC، tenant isolation، CSRF/CORS، fail-closed Redis policy، NID local mock وpreflight، CSV/XLSX preview غير المستمر، اختبارات الأمن، ومواءمة frontend scopes.

## الميزات المقفلة

| الميزة | وضعها الحالي |
|---|---|
| NID الرسمي | مغلق؛ `STUB` أو `SHADOW` المحاكى فقط حتى توفير sandbox رسمي |
| الدفع الحكومي | مغلق خلف feature flag حتى payment sandbox وreconciliation |
| التسجيل العام | مقيد؛ لا يفتح قبل اعتماد الهوية والخصوصية |
| CSV/XLSX الحقيقي | validation/preview فقط؛ لا كتابة إلى سجلات المرضى |
| Redis degraded fallback | ممنوع في staging/production |
| migrations الإنتاجية | لم تُنفذ |
| background workers الحكوميون | لا تفعيل دون بنية staging ومراقبة |

## شروط بيئة Staging

```text
ENV=staging
ALLOW_DEGRADED_REDIS=false
GULA_ADAPTER_MODE_NID=shadow أو live بعد توفير sandbox رسمي
STAGING_REQUIRE_EXTERNAL_NID=true
CORS_ALLOWED_ORIGINS=https://<staging-frontend>
REDIS_URL=rediss://<staging-redis>:6380/0
MOI_NID_API_URL=https://<official-nid-sandbox>
STAGING_EGRESS_ALLOWLIST=<approved-hosts-only>
```

لا تُعبأ القيم السرية في هذا الملف أو Git؛ تُحقن من GitHub Environment أو secret manager.

## بوابات التنفيذ المحلية

نجحت بوابة الانتقال المحلية في **141 اختباراً مع تحذير واحد**، وشملت NID mode guards، staging preflight، CSV/XLSX validation، security regression، side-door hardening، tenant isolation، وpayment foundation/orchestration. كما نجحت بوابة backend الكاملة السابقة في **2666 اختباراً** مع **42 مستبعداً و20 تحذيراً**، ونجح frontend lint/typecheck/build.

## شروط فتح Staging الرسمي

لا يفتح staging الخارجي إلا بعد توفير NID sandbox credentials، Redis/PostgreSQL TLS، DNS وegress allowlist، payment sandbox، object storage منفصل، وملاك توقيع للأمن والخصوصية والتكامل الحكومي والدفع والتشغيل.

## شروط Canary وFull GO

يتطلب Canary نجاح contract tests وtenant matrix وbackup/restore وload test وbrowser/mobile وPentest مصرحاً، ثم يفتح لعيادة أو وحدة إدارية محددة. لا ينتقل إلى Full GO قبل reconciliation صفري الفروقات في بيانات الاختبار، عدم وجود P0/P1، نجاح rollback drill، وموافقة Go/No-Go مكتوبة.

## ما لم يُنفذ

لم يُنفذ push أو merge أو deployment أو production migration أو اتصال NID أو payment حقيقي أو استخدام بيانات مواطنين حقيقية. لذلك لا يمثل هذا الملف تفويضاً للتشغيل الحكومي.
