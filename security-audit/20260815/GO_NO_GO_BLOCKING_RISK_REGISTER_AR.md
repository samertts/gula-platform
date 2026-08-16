# سجل المخاطر الحاجزة لقرار Go/No-Go النهائي

**النظام:** GULA Platform — العيادات الطبية الشعبية
**الحالة الحالية:** `GO_WITH_RESTRICTIONS`  ￼
**الهدف:** تحديد المخاطر التي يجب إغلاقها أو قبولها رسمياً قبل `FULL_GO` الحكومي.
**ملاحظة:** الاختبارات المحلية الناجحة تثبت سلامة أجزاء من المصدر والعقود، لكنها لا تثبت سلوك Production أو الخدمات الحكومية أو الشبكات أو الأجهزة.

## الخلاصة التنفيذية

أبرز الحواجز الحالية ليست استخدامات `datetime.utcnow` أو أخطاء الاختبارات المحلية؛ فقد أُغلقت هذه الجوانب إلى حد كبير. الحواجز الفعلية قبل Go/No-Go هي **التكامل الحقيقي مع NID، العزل والتوافر في PostgreSQL/Redis متعدد العمال، حماية PHI/PII عند التشغيل الحقيقي، الدفع والتسوية، النسخ الاحتياطي والاستعادة، Pentest مصرح، اختبارات المتصفح والهاتف، والأداء التشغيلي**.

أي خطر من فئة P0 أو P1 أدناه، إذا بقي بلا دليل قابل لإعادة الفحص أو بلا قبول رسمي موثق، يمنع `FULL_GO`.

## المخاطر الأمنية والهوية والتكاملات

| المعرف | الأولوية | الخطر | الأثر المحتمل | الحالة | دليل الإغلاق المطلوب | قرار Go/No-Go |
|---|---|---|---|---|---|---|
| SEC-01 | P0 | تجاوز tenant isolation أو اختلافه عند PostgreSQL متعدد العمال | كشف سجلات مرضى أو وصفات أو نتائج مختبر بين عيادات/جهات | غير مثبت تشغيلياً | tenant matrix سلبي على PostgreSQL staging مع concurrent workers وقراءة/كتابة ومراجعة query/service layer | مانع مطلق |
| SEC-02 | P0 | قبول هوية NID خاطئة أو تحويل فشل provider إلى `verified=true` | إنشاء هوية مواطن خاطئة أو ربط سجل طبي بالشخص الخطأ | مفتوح — SAFE_STOP | عقد NID رسمي، sandbox، mTLS، اختبارات 401/403/429/5xx/timeout/schema drift/replay، SHADOW ثم LIVE محدود | مانع مطلق |
| SEC-03 | P0 | تسريب PHI أو NID الخام في logs أو traces أو URLs أو cache keys | كشف بيانات صحية أو هوية خارج نطاق الوصول | غير مثبت في شبكة وobservability حقيقية | data inventory، log sampling، redaction tests، tracing review، DLP/secret scan، وموافقة privacy owner | مانع مطلق |
| SEC-04 | P0 | fallback غير آمن عند فقد Redis أو NID أو الدفع | قبول جلسة revoked أو تجاوز rate-limit أو قرار غير موثق | source/test مغلق، runtime غير مثبت | outage test متعدد العمال يثبت fail-closed في staging، مع عدم وجود in-memory fallback في staging/production | مانع مطلق |
| SEC-05 | P1 | تلوث module/config أو اختلاف secrets بين workers أو الاختبارات | سلوك غير متسق في JWT/revocation أو فشل startup غير متوقع | أُصلح في test isolation؛ runtime غير مثبت | multi-worker startup وsecret consistency وrefresh/revocation replay tests | مانع حتى إثباته |
| SEC-06 | P1 | ضعف CORS/CSRF عند cookies وcredentials في متصفحات حقيقية | سرقة جلسة أو طلبات cross-origin غير مصرح بها | الاختبارات المحلية جزئية | Chromium/Firefox/Safari matrix، preflight، wrong-origin، refresh/logout، cookie flags، وCSRF invalid/missing | مانع قبل فتح الويب العام |
| SEC-07 | P1 | service account أو RBAC scope أوسع من الحاجة | وصول عامل تكامل أو قاطع تذاكر إلى بيانات أو أموال غير مخولة | مواءمة source/tests ناجحة، runtime غير مثبت | role/scope matrix، deny tests، token rotation/revocation، ومراجعة مالك النظام | مانع قبل التفعيل الكامل |
| SEC-08 | P1 | webhook replay أو عدم idempotency في NID/الدفع/الإشعارات | تكرار إنشاء هوية أو تحصيل أو صرف | العقود المحلية فقط | signed webhook، nonce/timestamp، idempotency key، replay test، وحالة pending واضحة | مانع للتكامل المتأثر |
| SEC-09 | P1 | رفع ملف CSV/XLSX خبيث أو غير منضبط | malware، formula injection، تسريب أو إدخال بيانات خاطئة | validation preview فقط | quarantine، malware scan، content sniffing، quota، schema version، approval، audit، secure deletion، وrollback | يمنع import الحقيقي |
| SEC-10 | P1 | شهادات TLS/mTLS أو egress allowlist غير صحيحة | إرسال بيانات إلى endpoint خاطئ أو فشل التكامل | غير مثبت خارجياً | certificate chain/expiry/rotation، DNS/egress tests، منع HTTP، allowlist، ومراجعة firewall | مانع للتكامل |
| SEC-11 | P1 | Pentest غير منفذ أو غير قابل لإعادة الاختبار | بقاء SSRF أو broken access control أو tenant escape غير مكتشف | مفتوح — SAFE_STOP | Pentest مرخص أو تفويض موثق على staging، scope، findings، remediation، وإعادة اختبار | مانع Full GO |

## مخاطر البيانات والخصوصية والامتثال

| المعرف | الأولوية | الخطر | الأثر | دليل الإغلاق | القرار |
|---|---|---|---|---|---|
| DATA-01 | P0 | استخدام بيانات حقيقية دون أساس قانوني وموافقة ومالك معالجة واضح | مخالفة خصوصية أو ضرر للمواطنين وفقدان الثقة | موافقة الجهة المالكة، privacy impact assessment، consent/notice، retention، access review، وincident process | مانع مطلق |
| DATA-02 | P0 | عدم وجود مسار تصحيح/حذف/ربط آمن للهوية | بقاء سجل طبي خاطئ أو عدم القدرة على معالجة طلب المواطن | data lifecycle، correction workflow، merge/unmerge audit، rollback، وموافقة clinical/data owner | مانع مطلق |
| DATA-03 | P1 | خلط tenants في backup أو restore أو analytics | كشف واسع عند الاستعادة أو التقارير | restore إلى target منفصل، row counts/hashes، tenant boundary proof، وredaction/aggregation | مانع قبل البيانات الحقيقية |
| DATA-04 | P1 | retention غير منضبط لنتائج المختبر والإشعارات والملفات | تخزين زائد أو بقاء PHI في أماكن غير لازمة | retention schedule، TTL، deletion drill، legal hold policy، ومراجعة object storage | مانع حسب البيانات |
| DATA-05 | P1 | قرار سريري أو صرف دوائي يعتمد على هوية/نتيجة غير موثقة | ضرر سريري أو صرف مزدوج/خاطئ | clinical UAT، حالات pending/unknown، human override موثق، ومنع النظام من ادعاء تشخيص مستقل | مانع للـworkflow المتأثر |

## مخاطر الدفع والتحصيل

| المعرف | الأولوية | الخطر | الأثر | دليل الإغلاق | القرار |
|---|---|---|---|---|---|
| PAY-01 | P0 | تحصيل مزدوج أو صرف خدمة بلا receipt بسبب retry/timeout | خسارة مالية ونزاع مع المواطن | payment sandbox، state machine، idempotency، retry/failure/refund tests، reconciliation | مانع مطلق للدفع |
| PAY-02 | P0 | اختلاف تقارير الورديات عن ledger أو payment provider | عجز أو تلاعب مالي وعدم إمكانية التسوية | daily close، totals comparison، pending settlement، audit chain، وموافقة finance owner | مانع مطلق للدفع |
| PAY-03 | P1 | تداخل صلاحيات قاطع التذاكر والطبيب والصيدلي | تلاعب بالتحصيل أو الوصفة أو الصرف | segregation-of-duties matrix، negative tests، approval flow، ومراجعة مالية | مانع للتفعيل المالي |
| PAY-04 | P1 | عدم معالجة refunds وchargebacks والانقطاع | التزامات مالية غير مكتملة | refund/reconcile drills، manual fallback محدود، وتقرير استثناءات | مانع للتوسع |

## مخاطر التشغيل والمرونة

| المعرف | الأولوية | الخطر | الأثر | دليل الإغلاق | القرار |
|---|---|---|---|---|---|
| OPS-01 | P0 | عدم إثبات backup/restore وRPO/RTO | فقدان بيانات أو توقف طويل بعد حادث | encrypted backup، restore drill، قياس RPO/RTO، key rotation، ومالك on-call | مانع مطلق |
| OPS-02 | P0 | migrations غير مجربة على PostgreSQL staging | توقف أو فساد schema عند الترقية | clone/backup، `alembic check`، rehearsal، expand/contract، وrollback/forward-fix | مانع مطلق |
| OPS-03 | P1 | false-ready أو قبول traffic أثناء partial startup | أخطاء صامتة أو فقدان معاملات | DB/Redis/migration failure tests، load balancer readiness، و503 verification | مانع قبل التفعيل |
| OPS-04 | P1 | عدم وجود failover أو capacity متعددة العمال | توقف أو اختلاف سلوك الجلسات والـrate limits | worker/concurrency/chaos tests، Redis/DB failover، resource limits | مانع Full GO |
| OPS-05 | P1 | مراقبة ناقصة أو logs تحتوي PHI | اكتشاف متأخر للحوادث أو حادث خصوصية جديد | dashboards، alerts، redaction، SIEM/incident routing، وon-call drill | مانع Full GO |
| OPS-06 | P1 | rollback غير قابل للتنفيذ أو feature flags غير مستقلة | استمرار حادث بعد canary أو صعوبة الإيقاف | rollback drill، artifact سابق، flags لكل وحدة، وقرار توقف مكتوب | مانع Canary |

## مخاطر الأداء وتجربة المستخدم والأجهزة

| المعرف | الأولوية | الخطر | الأثر | دليل الإغلاق | القرار |
|---|---|---|---|---|---|
| PERF-01 | P1 | saturation أو latency مرتفعة عند عدة عيادات وworkers | طوابير صرف وتذاكر، timeouts، وإعادة محاولات خطرة | load/stress/soak ببيانات اصطناعية، p95/p99 budgets، queue/DB/Redis metrics | مانع التوسع |
| PERF-02 | P1 | اختلاف browser cookie/CSRF/CORS عن TestClient | فشل login أو تجاوز سياسة جلسة في المتصفح | browser matrix موثق على المتصفحات المعتمدة | مانع فتح الويب العام |
| MOB-01 | P1 | عدم إثبات SQLCipher وoffline conflict resolution | تسريب على الجهاز أو فقد/تعارض سجل صرف | أجهزة/محاكيات، device loss، backup/restore، conflict tests، clock skew | مانع Mobile GO |
| MOB-02 | P1 | فشل TalkBack/Orca أو keyboard/navigation | عدم وصول عامل صحي أو مواطن إلى الخدمة | accessibility audit عملي وscreen-reader evidence وUAT | مانع Full GO إذا كانت القناة ضمن النطاق |

## المخاطر الحوكمية والإنسانية

| المعرف | الأولوية | الخطر | الأثر | دليل الإغلاق | القرار |
|---|---|---|---|---|---|
| GOV-01 | P0 | غياب موافقة الجهة المالكة للهوية والبيانات والدفع | تشغيل غير مصرح به أو تجاوز صلاحيات حكومية | signed approvals، data owner، integration owner، وchange record | مانع مطلق |
| GOV-02 | P1 | عدم وضوح المسؤولية عند قرار سريري أو حادث خصوصية | تأخر الاستجابة وغياب المساءلة | RACI، incident response، clinical escalation، وlegal/privacy contact | مانع Full GO |
| GOV-03 | P1 | فتح التسجيل أو التوسع دون تدريب ودعم | أخطاء إدخال وصرف وتذاكر وحوادث متكررة | training/UAT، support runbook، helpdesk، وpilot metrics | مانع التوسع |
| GOV-04 | P1 | اعتبار نجاح الاختبارات المحلية دليلاً على خلو كل الثغرات | قرار Go خاطئ وثقة زائفة | سجل حدود evidence، staging proof، Pentest، ومراجعة بشرية مستقلة | مانع Full GO |

## الحواجز المطلقة قبل Go/No-Go

يجب إصدار `NO_GO` أو إبقاء `GO_WITH_RESTRICTIONS` إذا تحقق أي مما يلي:

1. لا يوجد عقد sandbox رسمي لـNID أو payment، أو لا يمكن إثبات صحة التوقيع والفشل والتراجع.
2. فشل tenant isolation أو وجود مسار يعيد PHI/PII لمستأجر غير مخول.
3. لا يوجد backup/restore drill أو rollback قابل للتنفيذ.
4. PostgreSQL/Redis متعدد العمال وTLS/ACL غير مختبرين في Staging.
5. وجود تحصيل مزدوج أو صرف مزدوج أو اختلاف reconciliation.
6. تسريب سر أو NID أو PHI في logs/traces/URLs أو artifacts.
7. Pentest غير مصرح أو findings P0/P1 غير معادة الاختبار.
8. غياب موافقة مالك البيانات أو مالك التكامل الحكومي أو مالك التشغيل.
9. فشل readiness أو عدم وجود on-call وincident runbooks.
10. فتح أي feature flag حكومي دون change record وrollback.

## ترتيب المعالجة المقترح

تبدأ المعالجة بـ **SEC-01/02/03/04، DATA-01، PAY-01/02، OPS-01/02، وGOV-01**؛ لأنها قد تسبب كشف بيانات أو قرار هوية خاطئ أو خسارة مالية أو تشغيلًا غير مصرح به. بعد ذلك تغلق SEC-06 إلى SEC-11 ومخاطر الأداء والأجهزة والتدريب. لا ينبغي ترتيب تحسين السرعة أو الشكل قبل إثبات العزل، الهوية، التسوية، والتعافي.

## تعريف الدليل الكافي

لا تعتبر عبارة “اختبار ناجح” دليلاً كافياً ما لم تتضمن البيئة، commit، dataset اصطناعية أو أساس استخدام البيانات الحقيقية، الأمر، الزمن، المخرجات، expected/actual، المراجع، ومالك التوقيع. يجب أن يكون كل finding قابلاً لإعادة الاختبار، وأن يكون لكل risk owner وdeadline وrollback.

## القرار الحالي

استناداً إلى مراجعة GULA المحلية، توجد بوابات source/test ناجحة، لكن المخاطر التشغيلية الخارجية المذكورة أعلاه لم تُغلق بالأدلة المطلوبة. لذلك القرار الآمن قبل استكمال Staging هو:

> **`GO_WITH_RESTRICTIONS` — لا Full GO، لا NID production، لا payment production، لا تسجيل عام، ولا استيراد PHI/PII حقيقية.**

## مراجع محلية

[1]: `PRODUCTION_READINESS_EXECUTION_REPORT_AR.md` — نتائج بوابة الجاهزية المحلية.

[2]: `FULL_GO_PRODUCTION_TRANSITION_PLAN_AR.md` — خطة الانتقال المرحلية.

[3]: `STAGING_NID_GOVERNMENT_CONNECTORS_RUNBOOK_AR.md` — متطلبات Staging وNID والموصلات.

[4]: `COMPREHENSIVE_RISK_INVENTORY_AND_REMEDIATION_PLAN_AR.md` — سجل المخاطر الشامل.
