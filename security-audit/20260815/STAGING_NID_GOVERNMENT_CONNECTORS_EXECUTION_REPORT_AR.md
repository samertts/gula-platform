# تقرير تنفيذ التحضير المحلي لـStaging — NID والموصلات الحكومية

**التاريخ:** 16 آب 2026
**الفرع:** `security/p0-bootstrap-alembic`
**الحدود:** تنفيذ محلي آمن فقط؛ لم تُستخدم credentials حقيقية، ولم يحدث اتصال بموفر حكومي، ولم يُنفذ push أو merge أو deployment.

## ما تم تنفيذه

| العنصر | النتيجة |
|---|---|
| أداة staging preflight | أُنشئت `scripts/staging_preflight.py` وتتحقق fail-closed من `ENV=staging`، Redis TLS، منع degraded Redis، CORS HTTPS، NID mode، sandbox HTTPS، egress allowlist، ومنع production URLs |
| اختبارات preflight | أُنشئت `backend/tests/test_staging_preflight.py` وتغطي configuration صالحاً، Redis degraded، HTTP connector، NID production URL، credentials الناقصة، ومنع STUB عند طلب external gate |
| عقد NID SHADOW | أضيف اختبار يثبت أن external call يمكن محاكاته للمقارنة، بينما يعيد caller نتيجة stub ولا يثق بنتيجة الموفر قبل اعتماد LIVE |
| staging workflow | أضيف checkout وpreflight إلى `.github/workflows/staging-verify.yml` قبل health/readiness؛ يستخدم GitHub Environment secrets/vars ولا يطبع القيم السرية |
| التشغيل المحاكى | إعداد sandbox متسق مرّ بنجاح دون أي اتصال خارجي |
| الوضع المحلي الحالي | preflight حُظر كما يجب بسبب غياب `ENV=staging` و`REDIS_URL` المشفر وCORS staging origin |

## نتائج الاختبارات

| الاختبار | النتيجة |
|---|---:|
| preflight + gateway modes + NID production guard | **21 passed، 1 warning** |
| backend full non-integration gate | **2660 passed، 42 deselected، 20 warnings** خلال 210.96 ثانية |
| compileall للملفات الجديدة | ناجح |
| ruff للملفات الجديدة والاختبار | ناجح |
| `git diff --check` | ناجح |
| اتصال NID حقيقي | **لم يُنفذ**؛ لا توجد credentials أو sandbox رسمي |
| workflow staging فعلي | **لم يُشغّل**؛ يتطلب GitHub Environment وأسراراً وموافقة بشرية |

## ما توقف عنده التنفيذ

بقي `SAFE_STOP` سارياً لأن التشغيل الفعلي يحتاج القيم الرسمية التالية عبر GitHub Environment `staging` أو secret manager معتمد:

```text
STAGING_REDIS_URL=rediss://...
STAGING_CORS_ALLOWED_ORIGINS=https://...
GULA_ADAPTER_MODE_NID=shadow
MOI_NID_API_URL=https://<official-sandbox>
MOI_NID_API_KEY=<official-sandbox-secret>
STAGING_EGRESS_ALLOWLIST=<approved-host:port-list>
GOV_CONNECTOR_URLS=https://<approved-government-sandbox-list>
```

لا يجوز ملء هذه القيم بقيم تخمينية أو production credentials. كما يلزم اعتماد رسمي لنطاقات NID والموصلات، certificates أو mTLS عند الحاجة، وقواعد egress. غياب هذه العناصر ليس خطأً في التنفيذ المحلي؛ بل حاجز أمان مقصود يمنع success وهمياً أو اتصالاً غير مصرح به.

## الخطوة البشرية التالية

يُنشئ مالك التكامل GitHub Environment باسم `staging` ويضع القيم الرسمية بعد مراجعة الأمن والجهة الحكومية. بعد ذلك يُشغّل workflow يدوياً على commit محدد. يجب أن يمر preflight أولاً، ثم `/health` و`/health/ready` و`/health/deep`، ثم SHADOW contract tests، ثم browser CSRF/CORS وtenant/RBAC matrix، ثم fault injection وrollback drill. لا يُنتقل إلى LIVE إلا بعد تقرير SHADOW موقع وموافقة مالك البيانات والأمن والتكامل.

## مراجع

[1]: `STAGING_NID_GOVERNMENT_CONNECTORS_RUNBOOK_AR.md` — runbook التنفيذ التفصيلي.

[2]: `../../scripts/staging_preflight.py` — preflight fail-closed.

[3]: `../../backend/tests/test_staging_preflight.py` — اختبارات configuration والـSAFE_STOP.

[4]: `../../backend/app/gateways/national_identity_gateway.py` — عقد NID وأوضاع STUB/SHADOW/LIVE.

[5]: `../../.github/workflows/staging-verify.yml` — بوابة staging المحدثة.


## ملحق: تنفيذ محاكاة NID واستيراد CSV/Excel

تم تنفيذ مسار محلي آمن للبيانات الاصطناعية في `backend/app/services/staging_tabular_import.py`. يقبل المسار ملفات `.csv` و`.xlsx` فقط، بحد أقصى 5 MiB و1,000 صف، ويفرض عقداً محدوداً لحالات NID الاصطناعية: `case_id` و`synthetic_nid` و`expected_status` و`expected_http_status`. يرفض الأعمدة غير المعروفة، التكرار، أرقام الهوية غير الاصطناعية، الصيغ formula-like، والـHTTP statuses غير المسموحة.

تمت إضافة endpoint غير إنتاجي هو `/staging/import/nid-cases/validate` في `backend/app/routes/staging_import.py`. endpoint محمي بصلاحية `integration:manage`، ومتاح فقط في `development` و`staging` و`test`. يقرأ الملف في ملف مؤقت، يتحقق منه، يعيد preview metadata فقط، لا يعيد `synthetic_nid`، ولا يكتب أي سجل إلى قاعدة البيانات، ثم يحذف الملف المؤقت. أُضيف تسجيله إلى factory في البيئات غير الإنتاجية فقط.

أُضيفت اختبارات CSV وXLSX وendpoint، ونجحت بوابة NID/preflight/import الجديدة: **27 اختباراً ناجحاً، وتحذير واحد**. يظل هذا المسار مخصصاً للـfixtures وحالات التكامل الاصطناعية؛ استيراد المرضى أو السجلات الصحية الحقيقية يحتاج عقداً منفصلاً، tenant scope، consent/data-governance، mapping ومراجعة بشرية وaudit قبل أي persistence.
