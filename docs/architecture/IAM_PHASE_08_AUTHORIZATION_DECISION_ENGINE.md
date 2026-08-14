# IAM Phase 8 — Authorization Decision Engine

## الهدف والحدود

يقدم Phase 8 محركًا مركزيًا لقرار التفويض داخل NIAM. المحرك لا يستبدل Phase 6 أو Phase 7؛ بل يستهلك العضويات النشطة، أدوارها وصلاحياتها، حالة الحساب والجلسة، التحقق المهني، العلاقات الصريحة، وسياق المورد ليصدر قرارًا حتميًا. يظل GULA هو السجل السريري الوحيد ونقطة فرض السياسة الوحيدة.

لن يعتمد المحرك على role name أو frontend state أو localStorage أو claims غير المتحقق منها أو معرفات العميل باعتبارها حقائق. معرفات المؤسسة والمنشأة والقسم ومساحة العمل القادمة من route/query تُعامل كمرشحات غير موثوقة، ثم تُثبت مقابل عضوية ومورد backend قبل السماح.

## نموذج الطلب والقرار

`AuthorizationRequest` هو dataclass داخلي ينقل action/resource وسياق المؤسسة والمنشأة والقسم والوحدة ومساحة العمل والعلاقة والغرض وحالة المورد وخصائص البيئة ومستوى الحساسية. `subject_account_id` لا يُقبل من body في المسارات المحمية؛ يملؤه route handler من `NiamActor.account.id`.

`AuthorizationDecision` يحتوي `ALLOW` أو `DENY`، و`reason_code` مستقرًا للاستخدام الداخلي، و`policy_id` و`policy_version` عند انطباق policy، و`required_assurance` عند الحاجة، ومرجع تدقيق عند تسجيل القرار. واجهة العميل لا تستلم تفاصيل policy أو شروطها الداخلية؛ endpoint محمي يعيد قرارًا عامًا فقط عند الحاجة.

## ترتيب التقييم الحتمي

يطبق المحرك الترتيب التالي ولا يسمح بتجاوز مرحلة فاشلة:

| الترتيب | الفحص | نتيجة الفشل |
|---|---|---|
| 1 | authenticated actor/account | `UNAUTHENTICATED` |
| 2 | account status and active flag | `ACCOUNT_INACTIVE` |
| 3 | active session, expiry, JTI-backed session | `SESSION_INVALID` |
| 4 | active membership for requested organization/scope | `MEMBERSHIP_UNRESOLVED` أو `MEMBERSHIP_SCOPE_MISMATCH` |
| 5 | active role assignment and catalog status | `ROLE_UNRESOLVED` |
| 6 | known active permission/capability | `PERMISSION_UNKNOWN` أو `PERMISSION_MISSING` |
| 7 | resource existence/resolution | `RESOURCE_UNRESOLVED` |
| 8 | organization/tenant boundary | `CROSS_TENANT_DENIED` |
| 9 | workspace boundary | `WORKSPACE_BOUNDARY_DENIED` |
| 10 | facility/department/unit scope | `SCOPE_MISMATCH` |
| 11 | explicit relationship/self/dependent context | `RELATIONSHIP_REQUIRED` |
| 12 | sensitivity and resource state | `STEP_UP_REQUIRED` أو `RESOURCE_STATE_DENIED` |
| 13 | validated purpose | `PURPOSE_REQUIRED` أو `PURPOSE_INVALID` |
| 14 | environment/emergency policy | `BREAK_GLASS_REVIEW_REQUIRED` أو `ENVIRONMENT_DENIED` |
| 15 | explicit policy deny/allow and conflict resolution | explicit deny wins |
| 16 | final decision and audit category | `ALLOW` أو `DENY` |

## RBAC and contextual policy

Phase 7 RBAC establishes capability through active role assignment, active catalog role, active permission relation, and matching scope. Context determines applicability. Organization ownership or active representative authority remains the explicit authority for membership and role-management operations, as already enforced by `MembershipService`.

The existing `IdentityPolicy` registry is consumed for explicit policy conflicts. Matching `deny` policies override allows. Matching policies are evaluated only against server-derived request context and exact action/resource matches; missing or malformed conditions do not grant access. The engine does not create speculative clinical policies or permissions.

## Relationship and citizen self-access

Self and dependent access use `CitizenRelationship`, not phone number, national ID equality, family association, device, or shared organization. Relationships must be active, within validity, non-revoked, and resource-scoped. A self relationship may authorize only a resource whose trusted owner/patient context matches the explicit relationship; family access is never inferred.

## Fail-closed and audit

Unknown permission, unknown resource, unresolved membership/context, policy evaluation failure, and internal exceptions all produce `DENY`. No unrestricted cache or frontend fallback is allowed. Sensitive allows and security-relevant denies are recorded through the existing hash-chained `AuditService` using the Phase 8 event categories. Clinical payloads are not written to audit metadata.

## Non-goals

Phase 8 does not approve clinical results, create organization activation, invent provider/government integrations, implement unrestricted delegation or impersonation, or make the frontend/mobile a security boundary. Break-glass is represented as an explicit controlled request that remains denied until a separately approved workflow supplies strong authentication, reason, scope, expiry, audit, and post-event review.
