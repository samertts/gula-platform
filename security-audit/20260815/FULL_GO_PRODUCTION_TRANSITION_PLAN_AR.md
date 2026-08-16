# خطة الانتقال من GO_WITH_RESTRICTIONS إلى Full GO

**النظام:** GULA Platform — نظام العيادات الطبية الشعبية
**النطاق:** NID، البيانات الصحية، الصرف الدوائي، التذاكر والتحصيل، الدفع الحكومي، المختبر، الأشعة، السونار، الإشعارات، Offline-first، والتحليلات.
**الحالة الحالية:** `GO_WITH_RESTRICTIONS` للبيئة المحلية/التجريبية والـpilot الاصطناعي فقط.
**الهدف:** الوصول إلى `FULL_GO` للإنتاج الحكومي بطريقة مرحلية قابلة للتراجع، مع موافقات الجهة المالكة للبيانات والهوية والدفع والأمن والتشغيل.

> **تنبيه تشغيلي:** لا يعني نجاح الاختبارات البرمجية وحده أن النظام جاهز سريرياً أو حكومياً. يجب أن يوقع طبيب مسؤول، ومالك البيانات، ومسؤول الأمن والخصوصية، ومالك التكامل الحكومي، ومالك الدفع، ومالك التشغيل على نطاق كل منهم.

## 1. تعريف Full GO

لا يصدر قرار `FULL_GO` إلا إذا تحققت جميع الشروط التالية مع أدلة قابلة لإعادة الفحص:

| المجال | شرط Full GO |
|---|---|
| الإصدار | commit محدد ومراجع، working tree نظيف، artifact موقّع، ولا تغييرات غير معروفة |
| الأمن | لا توجد P0/P1 مفتوحة، وPentest مصرح مع إعادة اختبار ناجحة |
| الهوية | NID الرسمي يعمل في production بعقد معتمد، mTLS، rotation، وrollback |
| التفويض | RBAC وtenant isolation وservice accounts مجربة على PostgreSQL متعدد العمال |
| البيانات | PHI/PII inventory وretention وconsent وaudit وincident response معتمدة |
| الدفع | payment sandbox ثم production contract، idempotency، reconciliation، وفصل مهام |
| البنية | Redis/PostgreSQL وTLS/ACL وreadiness وfailover وbackups مثبتة |
| الاستعادة | backup/restore drill ناجح وRPO/RTO مقبولان وrollback قابل للتنفيذ |
| الأداء | load/stress evidence ضمن budgets المعتمدة، بلا saturation غير معالج |
| الواجهات | browser matrix وFlutter/Android وAccessibility مقبولة |
| التشغيل | dashboards وalerts وrunbooks وon-call وincident process جاهزة |
| الحوكمة | توقيعات Go/No-Go وخطة pilot وcanary ومصفوفة المسؤوليات مكتملة |

إذا بقي شرط واحد حرج بلا دليل، فالقرار يبقى `GO_WITH_RESTRICTIONS` أو `NO_GO`.

## 2. المراحل والبوابات

### المرحلة صفر: تثبيت القرار والنطاق

يُثبت الإصدار المرشح، وتُجمد قائمة الميزات، ويُحدد ما سيبقى مغلقاً في أول إطلاق. لا ينبغي فتح كل الوحدات في أول يوم. يبدأ الإصدار بحد أدنى قابل للرقابة: تسجيل مضبوط، ملف المواطن، workflow الطبيب، صرف دوائي مقيد، والتقارير الأساسية. يبقى الدفع الحقيقي وNID والتسجيل العام مغلقاً إلى أن تجتاز كل بوابة خاصة بها.

**مخرجات المرحلة:** release manifest، dependency inventory، feature-flag matrix، owners matrix، risk register، rollback decision tree، وموافقة بدء Staging.

### المرحلة الأولى: إغلاق فجوات البنية والأسرار

ينشأ Staging مطابق منطقياً للإنتاج، لكنه منفصل تماماً في الحسابات والشبكات والبيانات والمفاتيح. يستخدم PostgreSQL وRedis مُدارين عبر TLS/ACL، وobject storage منفصلاً، وDNS منفصلاً، وGitHub Environment أو secret manager منفصلاً. يحظر استخدام ملفات `.env` أو أسرار الإنتاج داخل CI logs أو frontend bundles.

| بوابة | معيار القبول |
|---|---|
| `ENV` | `staging` أو `production` فقط وفق policy |
| Redis | `rediss://`، ACL، timeout، fail-closed، ولا in-memory fallback |
| PostgreSQL | TLS، مستخدم أقل امتيازاً، connection pool وmigration rehearsal |
| الأسرار | مصدر مركزي، rotation، لا تظهر في logs أو artifacts |
| CORS/CSRF | allowlist HTTPS محددة، browser preflight ناجح |
| readiness | لا يقبل traffic قبل DB/Redis/migrations/critical seed |
| egress | allowlist للمضيفين والمنافذ، ومنع outbound غير معروف |

**نقطة توقف:** أي wildcard CORS، secret مكشوف، HTTP خارجي، fallback Redis غير مصرح، أو readiness أخضر مع dependency متوقفة.

### المرحلة الثانية: اعتماد NID والموصلات الحكومية

يُنفذ الربط بهذا التسلسل فقط:

```text
local mock -> official sandbox STUB/contract -> official sandbox SHADOW
-> official sandbox LIVE limited -> production canary -> controlled expansion
```

يُوثق عقد NID: endpoint، method، schema، claims، signature، certificate chain، mTLS، scopes، timeouts، retry، rate limit، correlation ID، error mapping، idempotency، وتاريخ انتهاء الشهادات. في `SHADOW` تُرسل المطالبة إلى sandbox للمقارنة، لكن لا تُمرر نتيجة provider إلى قرار الدخول أو القرار السريري حتى يعتمدها النظام وفق policy.

يجب اختبار 401 و403 و429 و5xx وtimeout وschema drift وcertificate failure وreplay وprovider unavailable. يجب ألا تتحول أي حالة فشل إلى `verified=true` أو إلى صرف دوائي أو قرار سريري.

**بوابة NID:** نجاح contract tests، مضاهاة السجلات الاصطناعية، توقيع مالك التكامل، دليل TLS/mTLS، قياس latency/error rate، runbook للفشل، وسيناريو تراجع إلى وضع مقفل لا إلى fallback غير موثوق.

### المرحلة الثالثة: اعتماد البيانات والخصوصية

يُنشأ سجل حقول يحدد PHI وPII وNID الخام والهاش والـtokens، والغرض من كل حقل، ومالك المعالجة، والاحتفاظ، والتشفير، والأدوار، وaudit event، ومسار التصحيح والحذف. يمنع تسجيل NID الخام، وإرسال تفاصيل مرضية في SMS/push، ووضع PHI في URLs أو cache keys.

يُغلق CSV/XLSX preview الحالي عن أي كتابة حقيقية حتى يضاف له: quarantine، malware scanning، content sniffing، quota، schema version، preview وموافقة، duplicate detection، idempotency، tenant scope، audit، retention، secure deletion، وtransaction rollback.

**بوابة البيانات:** عينة بيانات اصطناعية في Staging، tenant matrix سلبي، مراجعة privacy owner، اختبار redaction، واختبار restore لا يخلط المستأجرين.

### المرحلة الرابعة: اعتماد RBAC وعزل المستأجرين

تُشغل المصفوفة على مستخدمين وأدوار اصطناعية في أكثر من tenant وبأكثر من worker. يجب أن ينجح الطبيب في workflowه فقط، ولا يصل الصيدلي إلى financial orchestration، ولا يكتب ticket issuer وصفة سريرية، ولا يصل المختبري إلى بيانات خارج نطاق عمله.

| الاختبار | النتيجة المطلوبة |
|---|---|
| قراءة سجل في tenant صحيح | allow وفق الدور والـscope |
| قراءة tenant آخر | deny بلا تسريب |
| token منتهٍ أو revoked | deny |
| refresh replay | deny وتسجيل حدث |
| scope صحيح مع workspace خاطئ | deny |
| service account بلا scope | deny |
| financial write من دور سريري | deny |

**بوابة التفويض:** نجاح route/service/repository tests، concurrent tenant tests، audit evidence، ومراجعة بشرية لمصفوفة deny-first.

### المرحلة الخامسة: الدفع والتحصيل الحكومي

يبقى السعر والتسوية خلف feature flag حتى يثبت payment sandbox العقد الكامل. يجب أن يغطي الاختبار إنشاء التذكرة، التحصيل النقدي، التحصيل الإلكتروني، فشل الشبكة، timeout، retry، duplicate request، refund، reconciliation، إغلاق الوردية، التقرير اليومي، وفصل صلاحيات قاطع التذاكر عن الطبيب والصيدلي.

لا تعتمد المنصة على response واحد من provider؛ يجب استخدام idempotency key وtransaction state machine وcorrelation ID، وإظهار حالة `pending` عند عدم اليقين، ثم reconciliation لاحقاً. يمنع إعطاء خدمة مدفوعة مرتين نتيجة retry أو تسجيل تحصيل بلا receipt.

**بوابة الدفع:** contract evidence من sandbox، تطابق totals، تقارير ورديات، reconciliation صفر فروقات في بيانات الاختبار، وموافقة finance owner.

### المرحلة السادسة: النسخ الاحتياطي والتعافي

ينفذ drill على Staging ببيانات اصطناعية: backup مشفر، حذف target منفصل، restore، مقارنة counts/hashes/relations، فحص tenant boundaries، ثم تشغيل login وdispensing وreports بعد الاستعادة. تسجل RPO وRTO، وتختبر rotation لمفاتيح التشفير، وفشل object storage، وفشل قاعدة البيانات.

لا يصدر Full GO بلا rollback للتطبيق والـfeature flags والـschema. إذا كانت migration غير قابلة للعكس، يجب أن تكون forward-fix موثقة ومجربة على نسخة staging.

### المرحلة السابعة: الأداء والمراقبة

يحدد مالك التشغيل budgets قبل الاختبار: p95/p99 latency، error rate، throughput، queue depth، Redis latency، DB pool utilization، CPU، memory، وexternal provider latency. تُشغل load وstress وsoak tests ببيانات اصطناعية وحجم مقارب للإنتاج، ثم تراجع النتائج ضد budgets مكتوبة.

تنشأ dashboards وتنبيهات لا تعرض PHI أو NID الخام. يجب وجود runbooks لـRedis outage، DB failover، NID timeout، certificate expiry، secret rotation، queue backlog، tenant-isolation alert، و5xx spike. يحدد on-call زمن الاستجابة ومالك كل alert.

### المرحلة الثامنة: الاختبارات البشرية والأمنية

تجرى browser matrix على المتصفحات المعتمدة، بما يشمل cookies وcredentials وCSRF وCORS وrefresh/logout وwrong-origin. وتجرى اختبارات Flutter/Android على أجهزة أو محاكيات تشمل SQLCipher، offline queue، conflict resolution، device loss، clock skew، secure storage، TalkBack، keyboard navigation، وscreen-reader labels.

ينفذ فريق أمني مرخص أو فريق مفوض رسمياً Pentest على Staging مع نطاق مكتوب. تشمل المراجعة broken access control، tenant escape، SSRF، file upload، webhook replay، session/token abuse، rate limits، secrets، وsecurity headers. تُغلق النتائج بإعادة اختبار، لا بمجرد تغيير الحالة إلى closed.

## 3. Pilot وCanary

### Pilot مغلق

يبدأ pilot بعد موافقة جميع المالكين، وبعيادة أو وحدة إدارية محددة، ومستخدمين مدربين، وبيانات اصطناعية أو بيانات حقيقية مصرح بها وفق سياسة الجهة المالكة. تبقى الميزات عالية المخاطر مثل NID production والدفع الحقيقي إما مقفلة أو محدودة جداً حتى اجتياز acceptance.

تقاس في pilot: successful login، NID verification، prescription/dispensing correctness، duplicate monthly dispensing prevention، ticket/payment correctness، report totals، notification delivery، error rate، privacy incidents، support tickets، ووقت الاستعادة.

**توقف pilot فوراً عند:** تسريب بيانات، cross-tenant access، صرف مزدوج، تحصيل مزدوج، verification خاطئ، فقدان audit، عدم القدرة على rollback، أو تجاوز error/latency budget المعتمد.

### Canary إنتاجي

يُفتح الإصدار لنسبة صغيرة من العيادات أو traffic المصرح، مع feature flags مستقلة لكل وحدة. لا يُفتح التوسع تلقائياً. تراجع النتائج بعد نافذة مراقبة متفق عليها، ثم يوقع مالك التشغيل على الانتقال التالي.

| المرحلة | النطاق | شرط الانتقال |
|---|---|---|
| Canary 1 | عيادة/وحدة واحدة | لا P0/P1، metrics ضمن budget، reconciliation سليم |
| Canary 2 | مجموعة صغيرة | stability window ناجحة، support load مقبول |
| Expansion | عدة وحدات | audit وprivacy وperformance evidence مكتملة |
| Full rollout | كل الوحدات المعتمدة | Go/No-Go نهائي وتراجع مجرب |

## 4. مصفوفة Go/No-Go

| المالك | يوقع على |
|---|---|
| Clinical owner | صحة workflow الطبي وعدم اعتماد النظام وحده على قرار سريري |
| Data/privacy owner | PHI/PII، retention، consent، breach response |
| Security owner | Pentest، RBAC، tenant isolation، secrets، egress |
| NID owner | عقد الهوية والشهادات والفشل والتراجع |
| Finance owner | payment/reconciliation/segregation of duties |
| DBA/SRE | migrations، backup/restore، RPO/RTO، failover |
| Mobile/accessibility owner | الأجهزة، offline، screen readers، WCAG |
| Operations owner | alerts، on-call، support، incident runbooks |
| Release owner | artifact، rollout، freeze، rollback |

## 5. خطة التراجع

يُوقف التوسع أولاً عبر feature flags، ثم يُعاد traffic إلى الإصدار السابق أو إلى وضع الخدمة المقيدة، مع إبقاء audit والبيانات المتسقة. لا يُحذف سجل مالي أو سريري لإخفاء أثر فشل. تُنفذ reconciliation للمعاملات المعلقة، وتُعزل webhooks المتأخرة، ويُبلغ مالك البيانات والأمن والتشغيل بالحادث.

بعد التراجع، يحظر إعادة الفتح قبل root-cause analysis، evidence، test regression، وموافقة Go/No-Go جديدة. في حالة NID أو الدفع، يجب أن يكون الوضع الآمن هو الرفض أو `pending`، وليس قبولاً غير موثق.

## 6. Definition of Done لـFull GO

```text
[ ] release manifest وcommit/artifact signed
[ ] owners وapprovals وrisk register محدثة
[ ] لا P0/P1 مفتوحة
[ ] NID official sandbox وproduction contract معتمد
[ ] payment contract وreconciliation وsegregation ناجحة
[ ] PostgreSQL/Redis staging multi-worker مع TLS/ACL ناجح
[ ] tenant/RBAC/concurrency matrix ناجحة
[ ] PHI/PII inventory وretention وconsent وaudit مكتملة
[ ] backup/restore وRPO/RTO وrollback drill ناجحة
[ ] browser/mobile/accessibility evidence ناجحة
[ ] performance/load/soak ضمن budgets
[ ] Pentest وإعادة الاختبار مكتملان
[ ] dashboards/alerts/on-call/runbooks جاهزة
[ ] pilot وcanary ناجحان
[ ] no unresolved critical incident
[ ] Go/No-Go موقع من جميع المالكين
```

## 7. النتيجة المتوقعة لحالة GULA الحالية

استناداً إلى الأدلة المحلية الحالية، يمكن الانتقال أولاً إلى **Staging رسمي ثم Pilot محدود**، وليس مباشرة إلى Full GO. العوائق التي يجب إغلاقها أولاً هي PostgreSQL/Redis staging الفعلي، NID sandbox الرسمي، payment sandbox، browser/mobile tests، backup/restore، performance evidence، وPentest. بعد إغلاقها وإعادة الاختبار، يصبح قرار `GO_WITH_RESTRICTIONS` قابلاً للترقية إلى canary، ثم إلى Full GO فقط بعد نجاح نافذة المراقبة والتوقيعات النهائية.

## مراجع محلية

[1]: `PRODUCTION_READINESS_EXECUTION_REPORT_AR.md` — نتائج مراجعة الجاهزية المحلية.

[2]: `PRODUCTION_READINESS_REVIEW_RUNBOOK_AR.md` — بوابات الفحص والأدلة المطلوبة.

[3]: `STAGING_NID_GOVERNMENT_CONNECTORS_RUNBOOK_AR.md` — إعداد Staging لموفر الهوية والموصلات.

[4]: `STAGING_NID_GOVERNMENT_CONNECTORS_EXECUTION_REPORT_AR.md` — نتائج التنفيذ المحلي للـpreflight والمحاكاة.
