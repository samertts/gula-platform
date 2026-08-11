# GULA — Master Risk Register

**المقياس:** P0 يمنع النشر أو قد يسبب ضرراً مباشراً؛ P1 يحتاج إغلاقاً قبل staging/scale؛ P2 مهم للتحسين؛ P3 مستقبلي.

| ID | الخطر | الحالة | الأولوية | المالك المقترح | التخفيف / الإجراء | بوابة الاعتماد |
|---|---|---|---:|---|---|---|
| R-001 | Demo قد يتصل ببيانات الإنتاج إذا أسيء النشر | مثبت كخطر تشغيلي، الكود محمي محلياً | P0 | Infrastructure/Security | DB وRedis وsecrets وnetwork منفصلة، synthetic-only، expiry، read-only | isolation drill |
| R-002 | اختلاف legacy User/LabUser عن unified account | جزئي | P0 | Identity/API | mapping وmigration plan، authorization negative tests، عدم حذف legacy | Architecture + Security |
| R-003 | stale clinical write في mutation غير مغطى بـCAS | مفتوح جزئياً | P0 | Clinical/Data | version check و409/resolution workflow، عدم silent overwrite | Clinical Safety + Data |
| R-004 | خطأ patient/sample/result أو unsafe transition | state tests موجودة لكن coverage غير كاملة | P0 | Clinical Safety | verified sample، senior validation، state machine، violation audit | Clinical Safety certification |
| R-005 | Redis غير مشترك بين workers | fallback local في non-production | P1 | Operations | shared Redis/HA، revocation/rate-limit multi-worker test | outage drill |
| R-006 | PostgreSQL migration/schema drift | fresh SQLite head، PG round-trip pending | P0 | DBA/Release | PG upgrade/downgrade/upgrade، expand/contract، backup | DBA approval |
| R-007 | backup موجود دون restore proof | غير متحقق | P1 | Operations/DR | real restore، checksum، RTO/RPO، audit integrity | DR drill |
| R-008 | p95 production غير مثبت | SQLite smoke only؛ 120/120 no errors | P1 | Performance/Operations | k6/Locust على PG/Redis، pool/queue metrics، soak/stress | performance certification |
| R-009 | native Android/iOS/Windows build غير متحقق | جزئي | P1 | Mobile/Release | CI native، signing، tests، release artifact/rollback | release gate |
| R-010 | AI قد يصبح final medical decision maker | guardrails/evals موجودة، governance production pending | P1 | AI Safety/Clinical | human oversight، confidence/provenance، kill switch، rollback | AI safety review |
| R-011 | workflow/authorization engines متكررة | technical debt محتمل | P1 | Architecture | source-of-truth map، ADR، incremental reconciliation | architecture review |
| R-012 | offline local PHI leakage أو conflict replay | offline capability غير مكتملة | P1 | Mobile/Data Security | encrypted local state، idempotency، reconciliation، expiry | offline recovery drill |
| R-013 | external integration mapping unsafe | integrations متعددة | P1 | Interoperability | gateway validation/terminology/provenance، contract tests | integration certification |
| R-014 | secret leakage أو weak production defaults | local warnings، production rejection موجود | P0 | Security/DevOps | secret manager، rotation، CI secret scan، no local DB commit | security gate |
| R-015 | CI workflow permission/tool failure | fixes local/staged؛ remote run pending | P1 | DevOps | push branch، inspect Actions، fix only proven failures | CI green gate |
| R-016 | destructive Wave 4 operation accidentally executed | HARD STOP | P0 | Program Director | do not prune/rename/delete/release without recorded scope approval | explicit approval |
| R-017 | frontend unit coverage absent | Vitest passes with no tests | P2 | Web QA | add component/API/security/E2E tests | web quality gate |
| R-018 | hot operational tables grow without archival | lifecycle configs partial | P2 | Data/DBA | retention/archive/legal hold/partitioning and metrics | data lifecycle review |

## قرار المخاطر

لا يُسمح بتغيير الحالة إلى `CLOSED` اعتماداً على وجود كود أو وثيقة فقط. يلزم تنفيذ mitigation وتشغيل validation المحدد وإرفاق evidence. المخاطر R-001 وR-003 وR-004 وR-006 وR-014 وR-016 تمنع release production حتى يثبت إغلاقها.
