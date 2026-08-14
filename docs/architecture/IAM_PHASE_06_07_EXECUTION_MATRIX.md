# IAM Phase 6–7 Execution Matrix

## 1. ترتيب التنفيذ

يجب تنفيذ **Phase 6 — Membership & Relationship Engine** قبل **Phase 7 — Role & Permission Engine**. السبب أن Role Assignment يحتاج Membership وScope وWorkspace Context موثوقاً؛ ولا يجوز بناء authorization على عضوية أو workspace غير مثبتين. أما Phase 8 — ABAC/contextual authorization — فتبقى خارج النطاق الحالي.

| الترتيب | المكوّن | الاعتماد | حالة المصدر الحالية | أولوية |
|---|---|---|---|---|
| 1 | Previous Phase 0–5 pre-flight | المصدر، الاختبارات، migrations، GitHub | `PARTIAL/UNVERIFIED` في بعض الأبعاد | P0 |
| 2 | Membership/Relationship schema وstate machines | Account، Organization، Facility، Department، Unit، Workspace | غير موجود كـengine عام؛ توجد علاقات مواطن ضيقة وAssignment قديم | P0 |
| 3 | Invitation/Application workflows | Membership schema وserver actor | غير موجود كمسار canonical | P0 |
| 4 | Membership API وtenant isolation | Membership service وaudit | غير موجود كعقد عام | P0 |
| 5 | Role/Permission registries | Membership وscope | لا توجد نماذج canonical؛ توجد IdentityPolicy وAssignment وclient RBAC صلب | P0 |
| 6 | Role assignment lifecycle وenforcement primitive | Role/Permission + Membership | غير موجود كطبقة موحدة | P0 |
| 7 | Frontend capability reflection | Backend effective capabilities | الواجهة تحتوي hardcoded RBAC map | P1 |
| 8 | Mobile shared contracts | Backend APIs وFlutter client | Flutter offline engine موجود، parity غير مثبت | P1 |
| 9 | Concurrency/performance/observability | كل الطبقات | جزئي | P1 |

## 2. حالات يجب إنفاذها على الخادم

لا يحق للعميل تغيير status أو scope أو account/organization/facility/workspace ownership عبر body أو localStorage أو JWT claims غير موثوقة. كل قرار يعتمد على actor/session/JTI، ثم يتحقق من membership والscope والـstate machine داخل transaction، ويسجل audit event مع actor/target/before/after/reason.

| المجال | الحالات المطلوبة | قاعدة الإغلاق |
|---|---|---|
| Membership | `PENDING`, `INVITED`, `ACTIVE`, `SUSPENDED`, `EXPIRED`, `REVOKED`, `REJECTED`, `DEACTIVATED` | لا transitions خارج matrix؛ لا حذف تاريخي |
| Invitation | created, accepted, rejected, revoked, expired | token random، single-use، قصير العمر، قابل للإلغاء، لا يُسجل سراً |
| Application | `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`, `EXPIRED` | organization actor فقط يوافق أو يرفض |
| Role | `ACTIVE`, `DISABLED`, `DEPRECATED` | deprecated لا يُسند جديداً؛ التاريخ لا يُحذف |
| Role Assignment | `PENDING`, `ACTIVE`, `SUSPENDED`, `EXPIRED`, `REVOKED` | active assignment فريد ضمن account/membership/role/scope |
| Permission | `ACTIVE`, `DISABLED`, `DEPRECATED` | لا permission غير مسجلة أو speculative تمنح وصولاً |

## 3. Phase 6 deliverables

يتكون Phase 6 من نموذج Membership عام منفصل عن Account وIdentity وOrganization وWorkspace وRole. يجب أن يدعم حساباً واحداً مع عدة منظمات ومنشآت ومساحات وسياقات مهنية، مع `organization_id` إلزامي وfacility/department/unit/workspace اختياريين حسب scope، وrelationship type مستقل عن authorization.

| الدفعة | نطاق التنفيذ | الاختبارات الإلزامية | معيار القبول |
|---|---|---|---|
| M6-A | models/enums/migration وunique/FK/indexes | migration upgrade/downgrade، FK، uniqueness، orphan rejection | لا duplicate active membership ولا orphan |
| M6-B | membership service/state machine | legal/illegal transitions، expiry، suspension، revoke، idempotency | final state deterministic وتاريخ محفوظ |
| M6-C | invitation/application workflows | replay/theft/expiry/revocation/enumeration | single-use، no secret logs، organization approval |
| M6-D | API actor authorization | 401/403/404، IDOR/BOLA، cross-tenant | لا self-membership ولا cross-scope access |
| M6-E | Workspace eligibility bridge | membership + professional verification + workspace context | backend فقط يقرر eligibility |
| M6-F | Frontend/Mobile contracts | real API, loading/error/status, RTL, shared mobile contract | لا mock membership ولا fake acceptance |

## 4. Phase 7 deliverables

يبني Phase 7 Role Catalog وPermission Catalog وRolePermission وRoleAssignment وcentral authorization primitive فوق Membership. لا يتم إدخال ABAC كامل أو inheritance ضمن هذه الدفعة إلا كواجهات مستقبلية صريحة.

| الدفعة | نطاق التنفيذ | الاختبارات الإلزامية | معيار القبول |
|---|---|---|---|
| R7-A | role/permission registries وcatalog seed | duplicate keys، sensitivity، deprecated behavior، no speculative grants | catalog authoritative ومطابق لقدرات موجودة |
| R7-B | role-permission relations | relation uniqueness، disable/deprecate، least privilege | لا `ADMIN=ALL_PERMISSIONS` shortcut |
| R7-C | scoped role assignments | global/org/facility/department/workspace، expiry/revoke | role لا يتسرب بين tenants/scopes |
| R7-D | assign/revoke authorization | self-escalation، cross-org، platform-admin restrictions | actor يحتاج permission ضمن scope نفسه |
| R7-E | backend enforcement primitive | direct API 401/403، action matrix، resource context | frontend hiding لا يعتبر security |
| R7-F | frontend capability reflection | no hardcoded authoritative role map، route guards from server capabilities | UI انعكاس فقط وserver authoritative |
| R7-G | audit/cache/concurrency | role created/updated/assigned/revoked، invalidation، races | no stale high-risk authorization |

## 5. Permission catalog policy

تُسجل فقط permissions لقدرات موجودة أو formally planned ومثبتة في المصدر. تستخدم المفاتيح صيغة واحدة مثل `identity.profile.read` و`laboratory.result.validate` و`workspace.switch`. لا يجوز اختراع permission تمنح وصولاً إلى وظيفة غير موجودة.

| الحساسية | أمثلة تحتاج حماية إضافية لاحقاً |
|---|---|
| LOW | profile.read، notification.read |
| MEDIUM | organization.read، membership.read، workspace.read |
| HIGH | membership.invite، membership.revoke، clinical.result.enter |
| CRITICAL | role.assign، permission.assign، ownership.transfer، audit.read_sensitive، clinical.data.export، security.manage |

## 6. Security matrix

يجب اختبار self-membership، self-role assignment، role ID manipulation، scope manipulation، account/membership/organization/facility/workspace IDOR، cross-tenant reads، expired/suspended/revoked access، invitation replay، unauthorized revocation، platform-admin escalation، وconcurrent mutations. كل محاولة غير مصرح بها يجب أن تفشل بوضوح وتنتج audit violation مناسباً دون كشف معلومات enumeration.

## 7. Frontend and Mobile policy

الواجهة قد تعرض effective roles وpermissions وworkspace capabilities القادمة من Backend لتحسين UX، لكنها لا تنشئ membership أو تقبل invitation أو تعين role محلياً ولا تتخذ authorization decision. يجب استبدال hardcoded `role ===`, `permissions.includes`, `localStorage.role` وJWT role decoding authoritative checks بعقد capabilities من الخادم.

Flutter Android/iOS/Desktop يستخدم العقود نفسها. offline queue يمكنها حفظ operations المسموح بها reconciliation فقط، ولا يجوز لها إصدار authorization أو اعتماد clinical result. كل operation يحمل context/version/idempotency key ويُرفض عند conflict أو stale state.

## 8. CI and evidence gates

يجب أن تحتوي PRs على jobs منفصلة لـunit، DB migration، API security، concurrency، frontend component/a11y، mobile Flutter، contract governance، وregression Phases 0–5. لا يُعتبر phase complete إذا بقي أي بعد `MISSING` أو `UNVERIFIED`، أو إذا كانت Vercel deployment rate-limit تمنع دليلاً مطلوباً.

## 9. PR chain

يُنشأ فرع Phase 6 فوق آخر SHA لفرع hardening الحالي، ثم فرع Phase 7 فوق head Phase 6. لا يتم الدمج تلقائياً، ولا تُنشأ tags completion حتى تنجح البوابات وتتم مراجعة بشرية. يجب أن تبقى الملفات غير المرتبطة وstash السابق خارج commits.
