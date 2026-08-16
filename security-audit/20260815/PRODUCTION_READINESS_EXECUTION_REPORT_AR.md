# تقرير تنفيذ مراجعة الجاهزية للإنتاج — GULA Platform

**تاريخ التنفيذ:** 16 آب 2026
**النطاق:** مراجعة محلية غير إنتاجية على فرع `security/p0-bootstrap-alembic`
**سياسة التغيير:** لم يُنفذ push أو merge أو deployment أو production migration، ولم تُستخدم بيانات مواطنين حقيقية أو credentials حكومية.

## القرار المختصر

القرار الحالي هو:

> **GO_WITH_RESTRICTIONS — للبيئة المحلية/التجريبية والـpilot الاصطناعي فقط.**

لا يصدر هذا التنفيذ موافقة على Production الحكومي، ولا يزيل `SAFE_STOP`. لا تزال هناك أدلة لا يمكن إنتاجها محلياً، ومنها NID الرسمي، Redis/PostgreSQL متعدد العمال، payment settlement الحكومي، browser/device accessibility، backup/restore على تخزين دائم، وPentest مرخص.

## خط الأساس

| المؤشر | النتيجة |
|---|---|
| الفرع | `security/p0-bootstrap-alembic` |
| commit المرشح | `b2b90972` كما كان مثبتاً عند بدء المراجعة |
| working tree | تغييرات محلية مقصودة، مع ملفات readiness evidence؛ لا يوجد push أو merge |
| `git diff --check` | ناجح |
| `datetime.utcnow` في `backend/app` و`shared` | صفر occurrences |
| `alembic heads` | ناجح؛ الرأس `20260815_0025` |

## البوابات المنفذة

| البوابة | النتيجة |
|---|---:|
| grouped security/RBAC/tenant/NID/import gate | **141 passed، تحذير واحد** |
| backend full non-integration gate بعد الإصلاح | **2666 passed، 42 deselected، 20 warnings** خلال 214.87 ثانية |
| frontend lint/typecheck/build/PWA | ناجحة؛ build وservice worker تولدا دون خطأ |
| focused Python Ruff للملفات المضافة/الحساسة | ناجح؛ `All checks passed!` |
| compileall | ناجح في البوابات السابقة وعلى الملفات المعدلة |
| UTC residual scan | ناجح؛ لا توجد `datetime.utcnow` |
| staging preflight وNID mock contracts | ناجحان في الحالات المحاكية؛ الحالات الخارجية محظورة عمداً |
| CSV/XLSX validation | ناجح؛ preview غير مستمر ولا كتابة إلى قاعدة البيانات |

## إصلاح regression أثناء المراجعة

أظهر أول grouped readiness gate فشلاً واحداً في `test_blacklisted_refresh_token_rejected` بسبب تلوث حالة module بين `test_staging_config_guard.py` و`app.config`: كان الاختبار المؤقت يعيد `sys.modules['app.config']` دون إعادة مرجع `app.config` على package، فأصبح `auth.py` يستخدم secret مختلفاً عن الاختبار.

تم إصلاح عزل الاختبار بإعادة المرجع الأصلي على مستويي `sys.modules` وpackage attribute. بعد الإصلاح نجح grouped gate كاملاً، ثم نجح backend full gate كاملاً. هذا الإصلاح لا يفتح أي fallback إنتاجي؛ هو إصلاح deterministic لعزل الاختبارات.

## Migration والبيانات

نجح `alembic heads`. تعذر `alembic check` محلياً كفحص اتصال فعلي لأن PostgreSQL غير متاح على `localhost:5432`. هذا **ليس دليلاً على فشل migration في الكود**، لكنه دليل على أن مراجعة migration التشغيلية لم تُغلق محلياً. يجب تنفيذ `alembic check` وmigration rehearsal على PostgreSQL staging حقيقي، بعد backup، ومن دون Production.

لم تُنفذ `alembic upgrade` أو أي تغيير schema. لا توجد نتيجة محلية تبرر تنفيذ migration إنتاجية.

## نتائج lint

نجح Ruff للملفات Python التي أضيفت أو عُدلت مباشرة في هذه الدفعة، ونجحت `git diff --check`. أما تشغيل Ruff الواسع على كل `backend/app` و`shared` فيكشف مخالفات تاريخية/مولدة في scaffolding، مثل أسماء modules/classes وقواعد import وFHIR mixed-case، ولذلك لا يصح وصف المستودع كله بأنه `warning-free` أو `lint-clean` حتى تُعالج تلك الدفعة مستقلة.

## SAFE_STOP المفتوح

| البند | سبب بقائه مفتوحاً | الدليل المطلوب |
|---|---|---|
| NID الرسمي | لا توجد credentials أو sandbox رسمي | contract sandbox، TLS/mTLS، SHADOW/LIVE محدود، وموافقة مالك التكامل |
| Redis/PostgreSQL | لا توجد عدة workers وTLS/ACL وrace environment | outage، revocation، tenant concurrency، migration rehearsal |
| الدفع الحكومي | لا توجد منظومة payment sandbox وتسوية حقيقية | success/failure/retry/refund/reconcile وsegregation of duties |
| browser CSRF/CORS | TestClient لا يغطي browser cookie/preflight matrix | Chromium/Firefox/Safari مع credentials وwrong-origin |
| Flutter/Android/Offline | لا توجد أجهزة/ADB/SQLCipher/TalkBack/Orca | instrumented tests، conflict/restore/device-loss وaccessibility |
| backup/restore | لا يوجد storage دائم وRPO/RTO drill | backup مشفر، restore إلى target منفصل، tenant proof، وقياسات RPO/RTO |
| Pentest | لا يوجد تفويض أمني موثق على staging | OWASP ZAP/Burp أو فريق مرخص، scope، findings، وإعادة اختبار |
| الأداء التشغيلي | لا توجد أحجام staging وتزامن إنتاجي | load/stress، p95/p99، queue/Redis/DB/resource evidence |

## الميزات المسموح بها حالياً

يمكن استخدام بوابة `staging_preflight`، وNID local mock، وCSV/XLSX validation، وRBAC tests، وfrontend build، والاختبارات البرمجية على بيانات اصطناعية فقط. يظل CSV/XLSX في وضع preview غير المستمر؛ لا يجوز تحويله إلى import للمرضى الحقيقيين قبل إضافة quarantine، malware scan، consent/approval، mapping versioning، idempotency، audit، retention، rollback، وtenant-scoped persistence.

## الميزات الممنوعة حالياً

لا يجوز تفعيل NID الحقيقي، التسجيل العام، الدفع الحكومي، استيراد PHI/PII حقيقية، Redis fallback في staging/production، أو deployment/migration إنتاجية استناداً إلى هذه المراجعة وحدها.

## خطوة الخروج التالية

لرفع القرار من `GO_WITH_RESTRICTIONS` إلى قرار Production محتمل، يجب أولاً إنشاء Staging رسمي مع PostgreSQL وRedis عبر TLS، توفير NID/payment sandbox credentials من الجهات المالكة، تنفيذ browser/mobile/backup/load tests، إجراء Pentest مصرح، ثم عقد Go/No-Go يوقعه مالك الإصدار والأمن والخصوصية والسريري والتكامل الحكومي والتشغيل.

## الأدلة

توجد مخرجات الأوامر في:

- `security-audit/20260815/readiness-evidence/baseline.txt`
- `security-audit/20260815/readiness-evidence/backend-full-readiness-rerun.txt`
- `security-audit/20260815/readiness-evidence/security-rbac-data-gates-rerun.txt`
- `security-audit/20260815/readiness-evidence/frontend-readiness.txt`
- `security-audit/20260815/readiness-evidence/alembic-readiness.txt`
- `security-audit/20260815/readiness-evidence/alembic-check-final.txt`
- `security-audit/20260815/readiness-evidence/focused-python-ruff-final.txt`

## المراجع المحلية

[1]: `COMMAND06_LOCAL_CLOSURE_REPORT_AR.md` — تقرير الإغلاق المحلي السابق.

[2]: `PRODUCTION_READINESS_REVIEW_RUNBOOK_AR.md` — خطوات المراجعة ومعايير Go/No-Go.

[3]: `STAGING_NID_GOVERNMENT_CONNECTORS_EXECUTION_REPORT_AR.md` — تنفيذ preflight وNID staging محلياً.


## ملحق تنفيذ خطة الانتقال نحو Full GO

تم تنفيذ الجزء المحلي الآمن من خطة الانتقال. أُنشئت حزمة release manifest في `FULL_GO_TRANSITION_RELEASE_MANIFEST_AR.md`، وثُبتت حالة الميزات الحساسة على وضع مقيد: NID الرسمي غير مفعّل، الدفع الحكومي غير مفعّل، CSV/XLSX validation غير مستمر، وRedis degraded fallback ممنوع في البيئات الشبيهة بالإنتاج.

نجحت بوابة الانتقال المحلية في **141 اختباراً مع تحذير واحد**، وشملت `staging_preflight`، NID mode guards، security regression، side-door hardening، tenant isolation، CSV/XLSX، وpayment foundation/orchestration. لم تتصل هذه البوابة بخدمة حكومية ولم تستخدم بيانات حقيقية.

تم تثبيت إعدادات Staging المطلوبة: `ALLOW_DEGRADED_REDIS=false`، و`STAGING_REQUIRE_EXTERNAL_NID=true`، وNID في `shadow/live` فقط بعد توفير endpoint وcredentials رسميين. لم تُنشأ قيم سرية ولم تُكتب في Git.

يبقى القرار **GO_WITH_RESTRICTIONS**. لم تُنفذ مرحلة Staging الخارجية أو Pilot أو Canary أو Full GO، لأن ذلك يتطلب PostgreSQL/Redis TLS فعليين، NID/payment sandbox رسميين، egress allowlist، backup/restore، load test، browser/mobile، Pentest، وموافقات المالكين. لم يُنفذ push أو merge أو deployment أو production migration.


## ملحق معالجة المخاطر P0/P1 — دفعة محلية إضافية

تمت معالجة ضوابط قابلة للإغلاق محلياً ضمن SEC-03 وSEC-09. أزيلت الأسماء وأرقام health number وأرقام الجواز والتأشيرة والإقامة وشهادة الميلاد من سجلات `identity_governance` وhistory payloads، واستُبدلت بهاشات أو رسائل عامة. أضيف regression test يثبت عدم ظهور الاسم أو health number أو national ID في السجل.

شُدد `staging_tabular_import` بإضافة فحص null bytes في CSV، رفض macros وexternal links وpath traversal في XLSX، حد uncompressed archive، حد cell يبلغ 4096 حرفاً، وحد 32 عموداً. بقي المسار preview/validation غير مستمر ولا يكتب قاعدة البيانات، ولم يتحول إلى import للبيانات الحقيقية.

نجح focused importer gate في **9 اختبارات**، وprivacy/identity gate في **13 اختباراً**، ونجحت Ruff وcompileall للملفات المعدلة. ثم نجحت بوابة backend الكاملة في **2671 اختباراً، 42 مستبعداً، 20 تحذيراً** خلال 217.16 ثانية.

هذه المعالجة لا تغلق الأدلة التشغيلية الخارجية: tenant isolation على PostgreSQL متعدد العمال، NID الرسمي، payment sandbox/production، Redis outage/failover الحقيقي، backup/restore وRPO/RTO، browser/mobile، الأداء، وPentest. لذلك تبقى حالة القرار `GO_WITH_RESTRICTIONS`، ولا يجوز استخدام بيانات PHI/PII حقيقية أو تنفيذ Full GO.
