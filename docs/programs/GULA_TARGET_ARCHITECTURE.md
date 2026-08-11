# GULA — Target Architecture

## المبدأ المعماري

GULA هو نظام واحد بحساب وهوية وأمن مركزيين، مع تطبيق واحد لكل منصة لا تطبيق مستقل لكل مجال. المجالات الصحية Workspaces/Modules داخل المنصة، وتستخدم خدمات مشتركة للهوية والتفويض والإشعارات والبحث والتدقيق والمهام والـworkflow والتكامل والتصميم.

```text
GULA Account
  ├── Identity / Verification / Profile / Health ID
  ├── Organization Memberships / Roles / Permissions / Policies
  ├── Context / Entitlements / Workspaces / Devices / Sessions
  ├── Consents / Privacy / Audit History
  └── Authorized application surfaces

Platform Shell
  ├── Session + Workspace + Organization Context
  ├── Search + Notifications + Inbox + Tasks
  ├── Documents + Consent + Privacy + Security Center
  ├── Localization + Accessibility + Offline/Sync status
  └── Domain workspaces
```

## طبقات النظام

| الطبقة | المكوّن المستهدف | القاعدة غير القابلة للتفاوض |
|---|---|---|
| Clients | GULA Web، GULA Android، GULA iOS، GULA Desktop عند الحاجة التشغيلية | العميل لا يملك authorization؛ يستخدم عقود API مشتركة ويخزن الأسرار في secure storage |
| Application shell | session, workspace, context, search, tasks, notifications, consent, help | لا تكرار لهذه الخدمات داخل المجالات |
| API | FastAPI factory وversioned contracts | deny by default، server-side auth، canonical errors، request IDs |
| Identity/security | unified account + RBAC/ABAC/resource auth + MFA + device/session security | least privilege وfail closed وtenant isolation |
| Domain services | citizen, clinical, laboratory, radiology, pharmacy, hospital, EMS, blood, public health, workforce, ministry | modular domains فوق engines مشتركة، لا حسابات منفصلة |
| Shared engines | workflow, rules, appointment, patient flow, referral, resource, entitlement, terminology | state/version/audit/idempotency لكل كتابة حرجة |
| Integration Hub | FHIR, HL7, DICOM, PACS/RIS/LIS, analyzers, external APIs | gateway → validation → mapping → terminology → canonical model |
| Data | PostgreSQL primary، Redis shared، object storage، event/outbox | ACID، provenance، retention، backup/restore، no mutable clinical cache without policy |
| Event/async | outbox/event backbone، workers، durable queues | retry/backoff، idempotency، dead-letter/reconciliation |
| Observability | logs, metrics, traces, audit, alerts, dashboards, health | incident correlation وSLO evidence |
| Infrastructure | Docker/Compose، Kubernetes/Helm، PostgreSQL HA، Redis Sentinel، MinIO، Prometheus/Grafana/Loki/Tempo | environment separation، secret management، rollback، DR |

## قواعد السلامة والأمن

كل كتابة سريرية يجب أن تتحقق من الهوية والسياق والمورد والعينة/المريض والحالة الحالية والإصدار، ثم تسجل before/after/user/entity/time/reason في سجل تدقيق غير قابل للتلاعب. الكتابة القديمة أو المتعارضة ترفض أو تدخل مسار resolution صريحاً. لا يجوز أن يحول الأداء أو offline mode أو AI هذه القواعد إلى خيار.

الوصول التجريبي لا يملك أي اتصال ببيانات الإنتاج. يجب أن تستخدم Demo قاعدة وRedis وsecrets وموصلات منفصلة، وبيانات synthetic، وانتهاء جلسة، وread-only قدر الإمكان. لا يوجد login بدون كلمة مرور إلى الإنتاج.

## استراتيجية التوسع

التوسع الأفقي يعتمد PostgreSQL وRedis مشتركين، pool limits متوافقة مع عدد العمال، rate limiting موزع، outbox/event retries، readiness حقيقي، وقياس production-like. SQLite يظل أداة Demo/Test لا مصدر شهادة أداء وطنية.

## حدود Wave 4

هذه البنية لا تفوض عمليات حذف الفروع أو إعادة تسمية المسارات أو حذف ملفات النشر أو إنشاء Release. أي اختلاف معماري جوهري أو تغيير deployment يحتاج ADR ومراجعة Security/Clinical/Operations واعتماد Program Director.
