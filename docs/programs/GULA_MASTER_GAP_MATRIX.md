# GULA — Master Gap Matrix

**تاريخ الإصدار:** 11 أغسطس 2026

**قاعدة التصنيف:** لا تعني `CERTIFIED` إلا وجود تنفيذ واختبار ودليل قابل لإعادة الإنتاج ضمن النطاق المحدد. لا تعني `IMPLEMENTED` شهادة تشغيل إنتاجي.

| المجال / القدرة | الحالة الحالية | الهدف | الفعل | الأولوية | المخاطر والاعتماد | التحقق المطلوب |
|---|---|---|---|---:|---|---|
| Repository governance | Wave 3 موثقة، Wave 4 متوقفة عند HARD STOP | حالة موحدة قابلة للتتبع | KEEP / DOCUMENT | P0 | أي pruning أو rename غير مصرح قد يفقد العمل | مراجعة branch/tag/worktree وProgram approval |
| Unified identity/account | `User` و`LabUser` ومسارات تحقق وجلسات موحدة جزئياً | حساب GULA واحد مع Identity/Profile/Role/Context منفصلة | HARDEN / MIGRATE | P0 | اختلاف legacy clients وبيانات الهوية الطبية | contract tests، migration map، tenant/object auth |
| Authentication/session | HttpOnly cookies وrefresh rotation وCSRF موجودة | Deny-by-default، rotation، expiry، MFA | HARDEN | P0 | الأسرار وSecure cookies وMFA production | HTTPS smoke، abuse tests، refresh/revocation drill |
| Authorization/RBAC/ABAC | طبقات متعددة مع اختبارات عزل | محرك مركزي قابل للتدقيق | RECONCILE | P0 | تضارب engines أو ثقة في IDs من الواجهة | policy matrix وobject-level negative tests |
| Demo/Preview | `POST /demo/access` وبيانات اصطناعية | synthetic-only، isolated، read-only حيث يمكن، expiry | HARDEN | P0 | اتصال عرضي بالإنتاج أو secrets مشتركة | network/DB/Redis isolation drill |
| Laboratory workflow | مسارات order/sample/result/validation موجودة | state machine موحدة مع verified sample وsenior validation | KEEP / HARDEN | P0 | wrong patient/sample/result وstale writes | clinical safety transition tests وCAS design approval |
| Clinical data integrity | ACID وaudit موجودان، CAS غير مكتمل لبعض mutation paths | version check وconflict rejection لكل كتابة | FIX | P0 | silent overwrite أو فقدان نتيجة | concurrent writers، stale version، rollback |
| Audit/provenance | append/hash chain وcanonical timestamp موجودان | before/after/user/entity/reason، immutable وqueryable | HARDEN | P0 | tamper أو restore divergence | tamper tests وPostgreSQL restore verification |
| Backend API | واسع ومتكامل مع legacy routes | versioned contracts وcanonical errors | RECONCILE | P1 | route confusion وbreaking clients | OpenAPI diff وconsumer tests |
| Frontend shell/workspaces | Dashboard/GuideAssistant وواجهات كثيرة؛ shell موحد جزئياً | GULA shell مع workspace/context switching server-authorized | BUILD / RECONCILE | P1 | frontend visibility ليست authorization | route inventory وworkspace auth tests |
| Citizen/Clinical experience | Citizen registration وبعض الشاشات موجودة | unified citizen/clinical workflows | BUILD | P1 | exposure of data without resource auth | E2E authorization and consent tests |
| Radiology/PACS/DICOM | domain code/configs موجودة | Integration Hub؛ لا PACS replacement مبسط | KEEP / INTEGRATE | P1 | clinical interoperability and PHI leakage | DICOM/FHIR contract and sandbox integration |
| Pharmacy/Hospital/EMS/Blood/Public Health | modules/models/routes متفاوتة | reusable workspaces and shared engines | RECONCILE / BUILD | P1 | domain duplication and safety gaps | domain readiness matrix and clinical review |
| Patient Flow/Appointment/Referral/Resource | أجزاء موزعة، لا محرك مركزي مثبت | reusable national engines | BUILD | P1 | inconsistent queue/capacity behavior | workflow ADR، state and capacity tests |
| Integration Hub/Terminology | FHIR/DHIS2/DICOM/AI integrations متعددة | Gateway → validation → mapping → canonical model | REFACTOR | P1 | unsafe mappings and external failures | mapping provenance and contract tests |
| Offline-first/sync | PWA/offline indications، conflict resolution غير مكتمل | encrypted local queue, idempotency, reconciliation | BUILD | P1 | local PHI leakage and duplicate writes | offline E2E، conflict/recovery drill |
| Redis/worker scalability | fallback محلي؛ shared Redis production غير مثبت | HA Redis، cross-worker sessions/rate limits | HARDEN | P1 | stale revocation وabuse bypass | multi-worker outage drill |
| Database/migrations | no duplicate revisions؛ fresh SQLite head | PostgreSQL additive migration and rollback proof | VERIFY / HARDEN | P0 | schema drift and deployment failure | PG upgrade/downgrade/upgrade |
| Data lifecycle/DR | configs and docs موجودة؛ restore غير مثبت | retention/archive/legal hold/RTO/RPO | BUILD / VERIFY | P1 | loss or overgrowth of hot data | real restore with checksum and RTO/RPO |
| Observability/self-healing | health/metrics/request IDs/self-heal موجودة | dashboards, alerts, trace correlation | HARDEN | P1 | silent outage and false readiness | alert drill and incident correlation |
| AI governance | evaluation/RAG/guardrails موجودة | versioning, provenance, confidence, human oversight, kill switch | HARDEN | P1 | unsafe AI final decision or PHI exposure | eval gates, kill-switch, audit review |
| Web performance | code splitting/PWA؛ smoke SQLite p95≈918ms at c20 | p95 ≤500ms peak on production-like stack | MEASURE / OPTIMIZE | P1 | optimization may bypass safety | k6/Locust on PG/Redis with thresholds |
| Android/iOS/Desktop release | source foundations exist | reproducible signed releases and rollback | VERIFY / BUILD | P1 | unverified clients and signing | CI native matrix, analyze/test/build |
| CI/CD/supply chain | many workflows and dependency checks | green gates, SBOM, secret/license scanning | HARDEN | P1 | workflow permission failures | GitHub Actions run and artifact review |

## Wave 4 protected decisions

لم يُعتمد حذف فروع بعينها، ولا إعادة تسمية `frontend-v3`، ولا حذف ملفات root، ولا نشر Release أو تغيير deployment behavior. تصنف هذه البنود `AWAITING APPROVAL` ولا تدخل في الإصلاحات الآمنة الحالية.
