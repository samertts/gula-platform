# IAM Phase 8 — نتائج التدقيق التمهيدي من المصدر الفعلي

**المستودع:** `samertts/gula-platform`
**الفرع:** `feat/iam-phase6-memberships`
**رأس الفرع الحالي:** `0f963cf3`
**PR السابق المفتوح:** [#168](https://github.com/samertts/gula-platform/pull/168)

## تأكيد نطاق المواصفات

الملفان المرفقان يقدمان مواصفات متطابقة عمليًا لـPhase 8: محرك مركزي ينتج قرارًا حتميًا `ALLOW` أو `DENY` بعد دمج هوية الحساب، التحقق، العضوية، الدور، الصلاحية، النطاق التنظيمي، المورد، العلاقة، الغرض، البيئة، وسياق المصادقة. كما يشترطان أن يكون الخادم مصدر التفويض الوحيد، وأن يكون القرار deny-by-default وfail-closed، مع حدود صريحة للمؤسسة والمنشأة والقسم ومساحة العمل، وتدقيق للقرارات الحساسة، وت versioning للسياسات، وresource/query-level authorization، واختبارات IDOR/BOLA.

المرفقان غير مكتملين في نهايتهما؛ إذ ينتهيان عند عبارة مبتورة في قسم Security Event Categories: `Avoid logging every trivial read if this creates unacceptable v...`. لذلك لن يتم اختراع متطلبات ختامية غير موجودة في المصدر، وسيتم تنفيذ المتطلبات المكتملة وتوثيق هذا الحد بوضوح.

## نتائج التدقيق الفعلي

| المجال | الدليل من المصدر | الحالة |
|---|---|---|
| حدود actor والجلسة | `backend/app/identity/api/workspaces.py` يستخرج `NiamActor` من token مفكوك ومتحقق منه، ثم يطابق `account_uuid` و`jti` مع حساب نشط و`UserSession` نشطة. | **PASS — أساس صالح** |
| Phase 6 | نماذج وخدمة وAPI وmigration `20260814_0004` واختبارات العضويات والدعوات والتطبيقات موجودة في الفرع. | **PASS — موجود** |
| Phase 7 | نماذج وخدمة وAPI وmigration `20260814_0005` واختبارات Role/Permission موجودة في الفرع. | **PASS — موجود** |
| السياق السريري | `clinical_authorization_context_service.py` يثبت account → identity → person → assignment → facility → organization → tenant ويرفض الغموض أو الفشل. | **PASS — قابل لإعادة الاستخدام** |
| policy registry | `IdentityPolicy` وجدول `niam_policies` موجودان مع effect/actions/resources/conditions/priority/version/time range/approval/status. | **PARTIAL — أساس موجود** |
| relationship-based access | `CitizenRelationship` يدعم self/guardian/caregiver/delegate/authorized representative مع status وpurpose وscope وexpiry وrevocation. | **PASS — مصدر موثوق محدود** |
| verification | `VerificationRecord` يدعم identity/professional verification وassurance level وexpiry/revocation وprofessional type. | **PASS — مصدر موثوق** |
| assignment context | `Assignment` يحتوي organization/facility/department/role/status/start/end وخصائص temporary/emergency/delegated/requires_mfa. | **PASS — مصدر موثوق** |
| session context | `UserSession` يحتوي active state وJTI وstarted/last activity/expiry وMFA/risk metadata. | **PASS — مصدر موثوق** |
| ABAC helper | `app/security/abac.py` يطبق قواعد in-memory مع allow/deny وdeny-by-default، لكنه غير مربوط مركزيًا بـNIAM actor أو قاعدة السياسات. | **PARTIAL — لا يكفي وحده** |
| PolicyEngine الحالي | `app/identity/policy_engine.py` هو placeholder: `evaluate()` يعيد `True` و`evaluate_action()` يعيد `allow` و`filter_resources()` يعيد الموارد بلا فلترة. | **P1 قبل الاعتماد — يجب استبداله** |
| Frontend | `Sidebar` يستخدم static permission map في demo فقط؛ live يعرض العناصر ويترك القرار للخادم، لكن `usePermissions.ts` ما زال يعكس map محليًا لأغراض UX. | **PARTIAL — يجب عزله بوضوح كـUX** |
| Mobile | Desktop Flutter موجود، بينما Android/iOS يحتويان هياكل جزئية؛ لا توجد صلاحيات master/admin مضمنة في التغييرات الحالية. | **UNVERIFIED — يحتاج source-level parity فقط** |
| Alembic محليًا | `alembic heads` يعرض `20260814_0005`. `alembic current` المحلي تعذر بسبب غياب `shared` من `PYTHONPATH` في الأمر المباشر، وليس بسبب migration error. | **UNVERIFIED محليًا** |
| CI السابق | PR #168 أثبت remote IAM gates الأربعة بنجاح على رأس الفرع السابق؛ Vercel بقي متأثرًا بمعدل البناء الخارجي. | **PASS للـIAM / Vercel خارجي** |

## قرار ما قبل التنفيذ

لا يظهر في تدقيق Phase 0–7 عيب P0 يمنع البناء. يوجد placeholder مركزي في `app/identity/policy_engine.py` يمثل عيبًا أمنيًا عالي الأولوية إذا استُخدم، ولذلك سيُستبدل بمحرك القرار الجديد قبل ادعاء اكتمال Phase 8. لن يتم اعتماد أي fallback إلى role name أو frontend permission أو owner عند فشل السياق.

سيُبنى Phase 8 فوق actor/session وPhase 6 membership وPhase 7 RBAC وIdentityPolicy وCitizenRelationship وVerificationRecord وAssignment، مع إبقاء policy registry قابلاً للتفسير والت versioning. لن تُضاف سياسات سريرية تخمينية للمريض أو المختبر أو الأشعة أو الصيدلية ما لم يثبت المورد والسياق في backend الفعلي؛ وستكون الحالات غير المحلولة DENY.

## مصادر التدقيق

1. [`backend/app/identity/api/workspaces.py`](../backend/app/identity/api/workspaces.py)
2. [`backend/app/identity/models/authorization.py`](../backend/app/identity/models/authorization.py)
3. [`backend/app/identity/services/authorization_service_v2.py`](../backend/app/identity/services/authorization_service_v2.py)
4. [`backend/app/identity/services/clinical_authorization_context_service.py`](../backend/app/identity/services/clinical_authorization_context_service.py)
5. [`backend/app/identity/models/citizen_relationship.py`](../backend/app/identity/models/citizen_relationship.py)
6. [`backend/app/identity/models/verification_record.py`](../backend/app/identity/models/verification_record.py)
7. [`backend/app/identity/models/assignment.py`](../backend/app/identity/models/assignment.py)
8. [`backend/app/identity/models/policy.py`](../backend/app/identity/models/policy.py)
9. [`backend/app/identity/policy_engine.py`](../backend/app/identity/policy_engine.py)
10. [`backend/app/security/abac.py`](../backend/app/security/abac.py)
