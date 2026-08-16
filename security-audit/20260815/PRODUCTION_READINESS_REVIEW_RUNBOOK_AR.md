# Runbook مراجعة الجاهزية للإنتاج — GULA Platform

**النطاق:** نظام العيادات الطبية الشعبية ومنصة GULA، بما في ذلك الهوية، RBAC، البيانات الصحية، NID، الدفع، الموصلات، CSV/XLSX، Redis، PostgreSQL، الواجهة، وOffline-first.
**الهدف:** إصدار قرار موثق: `GO` أو `GO_WITH_RESTRICTIONS` أو `NO_GO`.
**قاعدة أساسية:** هذه المراجعة لا تنشر ولا تدمج ولا تغيّر Production. هي بوابة أدلة قبل أي انتقال.

> **ملاحظة طبية وتشغيلية:** المراجعة التقنية لا تثبت السلامة السريرية أو الاعتماد الحكومي وحدها. يجب أن يراجع طبيب مسؤول، ومالك بيانات، ومسؤول أمن، ومالك تكامل حكومي، ومسؤول تشغيل أي قرار يطال بيانات المرضى أو الخدمات الصحية.

## 1. مخرجات المراجعة وبوابة القرار

لا تبدأ المراجعة على `main` أو على بيئة Production مباشرة. ثبّت commit مرشحاً للإصدار، وأنشئ مجلداً للأدلة باسم commit وتاريخ المراجعة. كل نتيجة يجب أن ترتبط بـcommit، وأمر التنفيذ، ووقت UTC، واسم المنفذ، وartifact قابل لإعادة الفحص.

| القرار | شروطه |
|---|---|
| `GO` | لا توجد P0/P1، وكل بوابات الأمن والبيانات والنسخ الاحتياطي والتراجع ناجحة، وNID/الدفع/الموصلات لديها sandbox رسمي أو موافقة تعطيل واضحة، مع موافقة بشرية موثقة |
| `GO_WITH_RESTRICTIONS` | التشغيل محدود بميزات مغلقة أو cohort اصطناعي/مصرح، مع منع NID الحقيقي والدفع الحقيقي والتسجيل العام، ووجود مراقبة وتراجع |
| `NO_GO` | فشل tenant isolation، أو تسريب سر/PHI، أو Redis degraded غير مقصود، أو عدم وجود backup/restore، أو غياب rollback، أو فشل موفر الهوية/الدفع، أو وجود P0/P1 مفتوح |

النتيجة الحالية المتوقعة للمستودع، وفق تقرير الإغلاق المحلي، هي `GO_WITH_RESTRICTIONS` للبيئة التجريبية فقط، وليست `GO` للإنتاج الحكومي؛ لأن موفر NID، وRedis/PostgreSQL متعدد العمال، والموصلات الحقيقية، وPentest، واختبارات الأجهزة ما زالت خلف `SAFE_STOP` [1].

## 2. تثبيت نطاق الإصدار والمسؤوليات

### 2.1 تثبيت commit والفرع

ينفذ المراجع الأوامر التالية من نسخة نظيفة، ولا يجوز تنفيذ `reset` أو `rebase` أو `force-push` على فرع مشترك:

```bash
cd /home/ubuntu/gula-platform
mkdir -p security-audit/20260815/readiness-evidence
printf 'review_started_utc='; date -u +%Y-%m-%dT%H:%M:%SZ
printf 'branch='; git branch --show-current
printf 'commit='; git rev-parse HEAD
git status --short
git diff --check
git log -1 --oneline --decorate
```

إذا كان working tree غير نظيف، يسجل المراجع كل ملف غير ملتزم به، ويقرر هل هو ضمن الإصدار المرشح. لا يُسمح بإصدار قرار جاهزية على commit غير محدد.

### 2.2 مصفوفة المسؤوليات

| المجال | المسؤول الذي يوقع |
|---|---|
| نطاق الإصدار والـrollback | Release owner |
| الأمن وRBAC وCSRF وegress | Security owner |
| PHI وPII وretention وconsent | Data/privacy owner |
| القرارات السريرية وworkflow | Clinical owner |
| NID والموصلات الحكومية | Government integration owner |
| الدفع والتسوية | Finance/payment owner |
| قاعدة البيانات والنسخ الاحتياطي | DBA/SRE |
| Flutter/Android/Offline | Mobile owner |
| قبول التشغيل | Operations owner |

لا تعتبر المراجعة مكتملة إذا كان أحد المجالات الحساسة بلا مالك محدد أو بلا توقيع.

## 3. جرد الميزات وتصنيفها

أنشئ جدولاً يربط كل ميزة بحالتها، feature flag، البيانات التي تلمسها، صلاحياتها، dependency الخارجية، وخطة rollback.

| الميزة | البيانات | dependency | القرار الأولي |
|---|---|---|---|
| Chronic disease dispensing | PHI، وصفات، صرف شهري | PostgreSQL، RBAC، audit | لا تفتح للعامة قبل clinical/UAT وtenant proof |
| Ticketing and collection | PII ومالية | payment gateway | مغلق حتى sandbox والتسوية |
| NID | national ID | official provider | SAFE_STOP حتى sandbox رسمي |
| Lab/radiology/sonar | PHI وتقارير | LIS/RIS/PACS | staging contract ثم pilot |
| CSV/XLSX validation | synthetic test cases | local parser | مسموح في staging فقط حالياً |
| Offline-first | PHI محلي | SQLCipher/sync | لا يفتح قبل device/conflict tests |
| Notifications | contact/appointment data | SMS/push | لا ترسل PHI في templates |
| Analytics | aggregated health data | warehouse/reporting | minimum aggregation وde-identification |

لكل ميزة حساسة، يجب أن يكون القرار أحد: `enabled in production`، `disabled by default`، `staging-only`، أو `not implemented/SAFE_STOP`.

## 4. مراجعة الكود والتهيئة

### 4.1 اختبارات المصدر والـlint

نفذ البوابات على commit المرشح وسجل المخرجات كاملة:

```bash
cd /home/ubuntu/gula-platform
export PYTHONPATH="$PWD/backend:$PWD"

# فحص المساحات وملفات generated/secret-like
find . -path './.git' -prune -o -type f -size +10M -print
find . -path './.git' -prune -o -type f \( -name '.env' -o -name '*.pem' -o -name '*.key' \) -print

git diff --check
ruff check backend/app shared scripts
python3 -m compileall -q backend/app shared scripts

# فحص UTC القديم
if grep -RIn --include='*.py' --exclude-dir='__pycache__' 'datetime\.utcnow' backend/app shared; then
  echo 'FAIL: deprecated datetime.utcnow remains'; exit 1
fi
```

يجب مراجعة أي استثناءات ruff يدوياً. لا يكفي أن ينجح compileall؛ فهو لا يثبت صحة authorization أو isolation أو التعاقد مع provider.

### 4.2 بوابة backend والـfrontend

```bash
cd /home/ubuntu/gula-platform/backend
export PYTHONPATH=/home/ubuntu/gula-platform/backend:/home/ubuntu/gula-platform
pytest -q -m 'not integration' 2>&1 | tee ../security-audit/20260815/readiness-evidence/backend-full.txt

cd ../frontend-v3
pnpm install --frozen-lockfile
pnpm run lint
pnpm run typecheck
pnpm run build
```

تسجل أعداد `passed` و`failed` و`deselected` و`warnings` منفصلة. التحذيرات ليست نجاحاً مطلقاً؛ يجب أن يكون لكل deprecation مالك وتاريخ إغلاق.

### 4.3 migrations وOpenAPI

```bash
cd /home/ubuntu/gula-platform/backend
alembic heads
alembic check
python3 ../scripts/export_openapi.py > ../security-audit/20260815/readiness-evidence/openapi.json
```

في staging، تُجرى migration على نسخة backup أو clone، ويُختبر rollback أو forward-fix بحسب سياسة Alembic. لا تنفذ migration على production أثناء هذه المرحلة.

## 5. مراجعة التهيئة والأسرار

أنشئ جدولاً لكل متغير إنتاجي: المالك، المصدر، الدور، rotation interval، وهل يظهر في logs أو frontend. يجب أن تكون القيم في secret manager، لا في Git أو artifact أو bundle.

| الفحص | شرط القبول |
|---|---|
| `ENV` | قيمة معتمدة ومطابقة للبيئة |
| `REDIS_URL` | `rediss://` في staging/production، ولا fallback غير مصرح |
| `ALLOW_DEGRADED_REDIS` | `false` في staging/production |
| `ENCRYPTION_KEY` و`NID_HMAC_KEY` | مفاتيح مستقلة لكل بيئة، rotation موثق |
| refresh/session secrets | مستقلة وغير موجودة في frontend |
| CORS/CSRF origins | HTTPS allowlist فقط، بلا wildcard أو localhost |
| NID/payment keys | sandbox منفصلة عن production، ولا تظهر في logs |
| Sentry/telemetry | project وenvironment منفصلان، مع redaction |

نفذ preflight الحالي في staging بعد توفير قيم sandbox الرسمية:

```bash
ENV=staging \
ALLOW_DEGRADED_REDIS=false \
REDIS_URL=rediss://<staging-redis>:6380/0 \
CORS_ALLOWED_ORIGINS=https://<staging-frontend> \
GULA_ADAPTER_MODE_NID=shadow \
MOI_NID_API_URL=https://<official-nid-sandbox> \
MOI_NID_API_KEY="$MOI_NID_API_KEY" \
GOV_CONNECTOR_URLS=https://<approved-connector-sandbox> \
STAGING_EGRESS_ALLOWLIST=<approved-host:port-list> \
STAGING_REQUIRE_EXTERNAL_NID=true \
python3 scripts/staging_preflight.py
```

يجب أن يكون الخروج `STAGING PREFLIGHT: PASS`. إذا أصبح NID فعلياً `stub` بسبب credentials ناقصة، فالنتيجة `NO_GO` لا نجاحاً جزئياً.

## 6. مراجعة الهوية وRBAC وtenant isolation

أنشئ مصفوفة deny-first لكل endpoint حساس، ثم نفذها على مستخدمين اصطناعيين في tenantين مختلفين. يجب أن تفشل كل محاولة cross-tenant، وأن تفشل الجلسة الصحيحة بلا scope، وأن تفشل الصلاحية الصحيحة داخل workspace خاطئ.

| الحالة | المتوقع |
|---|---|
| طبيب يقرأ سجل مريض في tenantه | allow وفق workflow |
| طبيب يقرأ tenant آخر | 403/404 آمن، بلا تسريب |
| pharmacist يصل إلى financial orchestration | deny |
| ticket issuer يكتب clinical prescription | deny |
| integration operator يقرأ audit metadata | allow محدود |
| system admin قديم يستخدم scope عام | deny أو migration mapping موثق |
| token منتهي أو revoked | deny |
| refresh replay | deny وتسجيل security event |

نفذ الاختبارات ذات الصلة:

```bash
cd /home/ubuntu/gula-platform/backend
pytest -q tests/test_security_regression.py \
  tests/test_side_door_hardening.py \
  tests/test_tenant_isolation_matrix.py \
  tests/test_service_account_scopes.py \
  tests/test_staging_config_guard.py
```

لا يكفي فحص route؛ يجب فحص service/repository/query layer للتأكد من وجود tenant predicate على كل قراءة وكتابة للبيانات الصحية.

## 7. مراجعة البيانات الصحية والخصوصية

قبل Production، يجب إنشاء data inventory يحدد كل حقل PHI/PII، الغرض، المالك، retention، encryption at rest، encryption in transit، access roles، audit event، وحق الحذف أو التصحيح. يمنع استخدام NID الخام في cache keys أو logs أو URLs. يجب أن تكون نتائج المختبر العامة tokenized وTTL محدوداً، مع عدم إظهار تفاصيل الخطأ للمستخدم.

### 7.1 اختبار CSV/XLSX

المسار الحالي `/staging/import/nid-cases/validate` مخصص لحالات NID الاصطناعية ولا يحفظ البيانات. لا تحوله إلى import مرضى قبل إضافة:

1. malware scanning وcontent-type sniffing وquota لكل tenant.
2. mapping versioned مع preview وموافقة بشرية قبل persistence.
3. duplicate detection وidempotency key.
4. validation للقيم والتواريخ والوحدات والـencoding.
5. audit لكل upload وdownload وreject.
6. quarantine وretention وsecure deletion.
7. صلاحيات منفصلة للاستيراد والموافقة والنشر.
8. transaction atomicity وrollback عند فشل صف واحد أو batch.

## 8. مراجعة NID والموصلات

لا تنفذ اتصالاً حقيقياً قبل اعتماد endpoint sandbox، certificate chain، mTLS، API scopes، rate limits، schema، timeout، retry، circuit breaker، idempotency، وdata processing agreement. استخدم التسلسل:

```text
STUB -> local mock -> official sandbox SHADOW -> official sandbox LIVE limited
     -> pilot cohort -> production canary -> controlled expansion
```

يجب أن تفشل الحالات التالية بشكل صريح: 401، 403، 429، timeout، 5xx، JSON ناقص، schema drift، شهادة غير صالحة، replayed webhook، وموصل غير متاح. لا يجوز أن تتحول إلى `verified=true` أو قرار سريري.

## 9. النسخ الاحتياطي والاستعادة والتراجع

يجب تنفيذ drill فعلي على staging، وليس مراجعة ملف إعداد فقط:

```text
1. خذ backup مشفراً وموسوماً بالـcommit والوقت.
2. أنشئ tenant test اصطناعي وسجلات صرف/تذاكر/تقارير.
3. احذف أو اعزل قاعدة الاختبار.
4. استعد backup إلى target منفصل.
5. تحقق من row counts وhashes والعلاقات وtenant boundaries.
6. نفذ login/dispensing/report read بعد الاستعادة.
7. قس RPO وRTO وسجل الفشل.
8. احذف target والنسخ المؤقتة وفق retention.
```

معيار القبول هو وجود RPO/RTO معتمدين، واستعادة قابلة للتكرار، وعدم خلط tenants، وعدم وجود secrets في backup غير مشفر. يجب أن يكون rollback للـapplication والـfeature flags والـschema واضحاً قبل canary.

## 10. الأداء والاستقرار والمراقبة

ينفذ load test على staging ببيانات اصطناعية وحجم متفق عليه. تقاس `p50/p95/p99` للقراءة والكتابة، error rate، CPU، memory، PostgreSQL locks، Redis latency، queue depth، external latency، circuit opens، وworker restarts.

تجهز dashboards وتنبيهات منفصلة للإنتاج، ولا تعرض PHI أو raw NID. يجب أن يتوفر runbook للحالات التالية: Redis outage، DB failover، NID timeout، queue backlog، certificate expiry، secret rotation، cross-tenant alert، وارتفاع 5xx.

## 11. اختبارات المتصفح والهاتف

تُجرى browser matrix على Chromium وFirefox وSafari أو البديل المعتمد، وتشمل cookies وcredentials وpreflight وrefresh/logout وCSRF invalid/missing وCORS wrong-origin. لا تعتبر اختبارات `TestClient` بديلاً عن ذلك.

تُجرى اختبارات Android/Flutter على جهاز أو emulator: secure storage، SQLCipher، backup/restore، offline queue، conflict resolution، device loss، clock skew، TalkBack، keyboard navigation، contrast، وscreen reader labels. أي وظيفة صحية تعمل offline يجب أن تحدد بوضوح متى تكون البيانات pending أو غير موثقة.

## 12. Pentest ومراجعة الاعتماد

ينفذ فريق مرخص أو تفويض موثق فحصاً على staging فقط، مع نطاق مكتوب ووقت بدء/انتهاء وقواعد تعامل مع بيانات الاختبار. تشمل المراجعة OWASP API risks، SSRF، broken access control، tenant escape، token/session abuse، file upload، webhook replay، rate limits، secrets، وsecurity headers. لا تستخدم Production كهدف للفحص الاستغلالي.

بعد الإصلاح، يجب أن توجد إعادة اختبار لكل finding مع severity وowner وevidence. لا يكفي تقرير “لا توجد ثغرات” بلا نطاق وأدوات وتاريخ وقيود.

## 13. اجتماع Go/No-Go

قبل القرار، تجمع الحزمة التالية:

| الدليل | الحالة |
|---|---|
| commit وdiff وSBOM | مرفق |
| backend/frontend test reports | مرفق |
| security scan وPentest | مرفق أو SAFE_STOP |
| RBAC/tenant matrix | مرفق |
| NID/payment connector contract | مرفق أو SAFE_STOP |
| backup/restore drill | مرفق |
| performance report | مرفق |
| browser/mobile accessibility | مرفق أو SAFE_STOP |
| incident/rollback runbook | مرفق |
| موافقات المالكين | مرفقة |

يوقع كل مالك على نطاقه. إذا بقيت أية خانة P0/P1 أو خانة حرجة بلا evidence، يصدر القرار `NO_GO` أو `GO_WITH_RESTRICTIONS` مع قائمة صريحة للميزات المغلقة.

## 14. ما يمكن تنفيذه الآن داخل المستودع

يمكن تنفيذ فحوصات commit، lint، compileall، backend/frontend gates، UTC scan، RBAC tests، preflight، local mock، CSV/XLSX validation، وكتابة التقارير دون اتصال خارجي. لا يمكن إثبات NID الرسمي، mTLS الحكومي، payment settlement، PostgreSQL/Redis production behavior، browser/device accessibility، أو Pentest من داخل هذه الخطوات المحلية وحدها.

## 15. قائمة الإغلاق المختصرة

```text
[ ] commit محدد وworking tree معروف
[ ] scope وowners وfeature flags موثقة
[ ] لا P0/P1 مفتوح
[ ] full backend/frontend gates ناجحة
[ ] migrations وOpenAPI مراجعة
[ ] secrets وENV وCORS/CSRF وRedis TLS ناجحة
[ ] RBAC وtenant matrix ناجحة
[ ] PHI/PII inventory وretention وaudit مكتملة
[ ] NID/payment/connector evidence أو SAFE_STOP صريح
[ ] backup/restore وrollback drill ناجحان
[ ] performance/load evidence مكتملة
[ ] browser/mobile/accessibility evidence مكتملة
[ ] Pentest مرخص وإعادة اختبار مكتملة
[ ] monitoring/alerts/runbooks جاهزة
[ ] موافقات المالكين مكتملة
[ ] Go/No-Go موقع
```

## مراجع محلية

[1]: `COMMAND06_LOCAL_CLOSURE_REPORT_AR.md` — تقرير الإغلاق المحلي وحدود SAFE_STOP.

[2]: `COMPREHENSIVE_RISK_INVENTORY_AND_REMEDIATION_PLAN_AR.md` — سجل المخاطر الشامل.

[3]: `STAGING_NID_GOVERNMENT_CONNECTORS_RUNBOOK_AR.md` — إعداد Staging والموصلات وNID.

[4]: `LOCAL_NID_MOCK_SIMULATION_GUIDE_AR.md` — محاكاة NID المحلية.
